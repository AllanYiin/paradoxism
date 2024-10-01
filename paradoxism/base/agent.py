import hashlib
import threading
import time
import uuid
from functools import wraps
from typing import Callable

from openai import OpenAI

from paradoxism.base.perfm import PerformanceCollector
from paradoxism.utils.utils import *
from paradoxism.utils.docstring_utils import *

# 建立全域的 PerformanceCollector 實例，保證所有地方都能使用這個實例
collector = PerformanceCollector()

# Thread-local storage to store LLM client and current executor
_thread_local = threading.local()


def get_current_executor():
    """獲取當前線程的 FlowExecutor 實例。"""
    return getattr(_thread_local, 'executor', None)


class LLMClient:
    """封裝 OpenAI LLM 客戶端的類別。"""

    def __init__(self, model: str, system_prompt: str, temperature: float = 0.2, **kwargs):

        self.client=OpenAI()
        self.model = model
        self.system_prompt = system_prompt
        self.temperature = temperature
        self.extra_params = kwargs

    def generate(self, prompt: str) -> str:
        """生成 LLM 的回應。"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=self.temperature

        )
        return response.choices[0].message.content.strip()


def generate_agent_key(system_prompt: str, static_instruction: str, func_code: str):
    """基於 system_prompt, static_instruction 及函數邏輯生成唯一的哈希 key"""
    hash_input = system_prompt + static_instruction + func_code
    return hashlib.sha256(hash_input.encode()).hexdigest()


def agent(model: str, system_prompt: str, temperature: float = 0.7, **kwargs):
    """
    @agent 裝飾器，用於標記任務的最小單位。
    Args:
        model: 使用的模型名稱，例如 'gpt-4'
        system_prompt: 系統提示語
        temperature: 溫度參數，控制回應的隨機性
        **kwargs: 其他額外參數

    Returns:

    """

    def decorator(func: Callable):

        func.llm_client = LLMClient(model, system_prompt, temperature, **kwargs)

        func.static_instruction =parse_docstring(func.__doc__)['static_instruction'] or ""
        _thread_local.llm_client =func.llm_client
        _thread_local.static_instruction = parse_docstring(func.__doc__)['static_instruction'] or ""

        @wraps(func)
        def wrapper(*args, **kwargs_inner):
            instance_id = str(uuid.uuid4())

            # 基於 system_prompt, static_instruction 和代碼邏輯生成唯一的 agent key
            func_code = func.__code__.co_code.decode('latin1')  # 使用函數的原始字節碼生成唯一 key
            agent_key = generate_agent_key(system_prompt, func.static_instruction, func_code)

            start_time = time.time()  # 記錄開始時間
            executor = get_current_executor()
            _thread_local.llm_client = func.llm_client
            _thread_local.static_instruction = func.static_instruction
            result=None
            if executor:
                # 委託給 FlowExecutor 執行

                result= executor.execute_agent(func, *args, **kwargs_inner)
            else:
                # 正常執行
                result= func(*args, **kwargs_inner)

            end_time = time.time()  # 記錄結束時間
            execution_time = end_time - start_time  # 計算執行時間
            print(green_color(f"agent {func.__name__}"),yellow_color(f"executed in {execution_time:.4f} seconds"),flush=True)  # 輸出執行時間

            # 使用全域的 collector 來記錄效能數據
            collector.record(instance_id, agent_key, execution_time)
            return result

        return wrapper

    return decorator