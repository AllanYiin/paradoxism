import hashlib
import threading
import time
import uuid
import re
import inspect
import logging
from functools import wraps
from collections import OrderedDict
from typing import Callable, Any, get_origin, get_args
from typing import get_type_hints
from paradoxism.base.perfm import PerformanceCollector
from paradoxism.utils import *
from paradoxism.utils.docstring_utils import *
from paradoxism.ops.convert import *
from paradoxism.llm import *
from paradoxism.utils.input_dict_utils import *
from paradoxism.utils.regex_utils import extract_docstring
# 建立全域的 PerformanceCollector 實例，保證所有地方都能使用這個實例
collector = PerformanceCollector()

# 設置 logging 設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Thread-local storage to store LLM client and current executor
_thread_local = threading.local()

def get_current_executor():
    """獲取當前線程的 FlowExecutor 實例。"""
    return getattr(_thread_local, 'executor', None)

def generate_agent_key(system_prompt: str, static_instruction: str, func_code: str):
    """基於 system_prompt, static_instruction 及函數邏輯生成唯一的哈希 key"""
    hash_input = system_prompt + static_instruction + func_code
    return hashlib.sha256(hash_input.encode()).hexdigest()

def execute_function(func: Callable, *args, **kwargs):
    """執行函數的輔助方法，處理有無 executor 的情況"""
    return func(*args, **kwargs)

def agent(model: str, system_prompt: str, temperature: float = 0.7, stream=False, **kwargs):
    """
    @agent 裝飾器，用於標記任務的最小單位。
    Args:
        provider_or_model_name: 使用的llm提供者或是模型名稱，例如 'openai','gpt-4'
        system_prompt: 系統提示語
        temperature: 溫度參數，控制回應的隨機性
        stream: 是否為stream輸出
        **kwargs: 其他額外參數

    Returns:

    """
    def decorator(func: Callable):
        # 初始化 LLM 客戶端
        func.llm_client = get_llm(model, system_prompt, temperature, **kwargs)

        # 初始化函數的 __doc__
        if func.__doc__ is None:
            func.__doc__ = extract_docstring(func)

        # 使用 threading.Lock 保證對 thread-local 的操作是線程安全的
        lock = threading.Lock()
        with lock:
            _thread_local.llm_client = func.llm_client

        @wraps(func)
        def wrapper(*args, **kwargs_inner):
            instance_id = str(uuid.uuid4())
            try:
                # 產生 inputs_dict
                parsed_results =get_input_dict(func)
                # 生成 agent key
                func_code = inspect.getsource(func)
                agent_key = generate_agent_key(system_prompt, parsed_results['static_instruction'], func_code)

                start_time = time.time()
                with lock:
                    _thread_local.llm_client = func.llm_client
                    _thread_local.static_instruction = parsed_results['static_instruction']
                    _thread_local.input_args = parsed_results['input_args']
                    _thread_local.returns = parsed_results['return']
            except:
                PrintException()


            # 執行函數
            result = execute_function(func, *args, **kwargs_inner)
            if len(_thread_local.returns) == 1:
                try:
                    return_type = _thread_local.returns[0]['return_type']
                    return_type=str if not return_type or return_type.lower()=='unknown' else return_type
                    # Comprehensive type check using typing utilities
                    origin_type = get_origin(return_type)
                    type_args = get_args(return_type)
                    if origin_type is not None:
                        if not isinstance(result, origin_type):
                            logger.warning(f"Result type mismatch: expected {origin_type}, got {type(result)}. Skipping cast.")
                        else:
                            result = force_cast(result, return_type)
                    elif type_args:
                        if not any(isinstance(result, arg) for arg in type_args):
                            logger.warning(f"Result type mismatch: expected one of {type_args}, got {type(result)}. Skipping cast.")
                        else:
                            result = force_cast(result, return_type)
                    elif not isinstance(result, return_type):
                        logger.warning(f"Result type mismatch: expected {return_type}, got {type(result)}. Skipping cast.")
                    else:
                        result = force_cast(result, return_type)
                except TypeError as e:
                    logger.error(f"Error in type casting: {e}")
                    logger.error(f"Return type: {return_type}, Result: {result}")
                except:
                    PrintException()


            execution_time = time.time() - start_time
            logger.info(f"agent {func.__name__} executed in {execution_time:.4f} seconds with agent_key: {agent_key} and input_args: {parsed_results['input_args']}")

            # 使用全域的 collector 來記錄效能數據
            collector.record(instance_id, agent_key, execution_time)
            return result

        return wrapper

    return decorator




