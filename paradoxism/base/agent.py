import hashlib
import threading
import time
import uuid
import re
from functools import wraps
from typing import Callable,Iterable,Dict,Any
import inspect
from openai import OpenAI
from collections import OrderedDict
from paradoxism.base.perfm import PerformanceCollector
from paradoxism.utils.utils import *
from paradoxism.utils.docstring_utils import *
from paradoxism.ops.convert import *
from paradoxism.llm import *

# 建立全域的 PerformanceCollector 實例，保證所有地方都能使用這個實例
collector = PerformanceCollector()

# Thread-local storage to store LLM client and current executor
_thread_local = threading.local()


def get_current_executor():
    """獲取當前線程的 FlowExecutor 實例。"""
    return getattr(_thread_local, 'executor', None)


def generate_agent_key(system_prompt: str, static_instruction: str, func_code: str):
    """基於 system_prompt, static_instruction 及函數邏輯生成唯一的哈希 key"""
    hash_input = system_prompt + static_instruction + func_code
    return hashlib.sha256(hash_input.encode()).hexdigest()


def agent(model: str, system_prompt: str, temperature: float = 0.7,stream=False, **kwargs):
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

        func.llm_client =get_llm(model, system_prompt, temperature, **kwargs)
        if func.__doc__ is None:
            # 使用 re.search 來提取第一個被 """ 夾住的區塊
            match = re.search( r'def\s+\w+\s*\(.*?\):\s*f?"""\s*([\s\S]*?)\s*"""', inspect.getsource(func))
            if match:
                func.__doc__ = match.group(1)
            else:
                func.__doc__=''

        _thread_local.llm_client =func.llm_client

        @wraps(func)
        def wrapper(*args, **kwargs_inner):
            instance_id = str(uuid.uuid4())

            # 產生inputs_dict
            inputs_dict = OrderedDict()
            signature = inspect.signature(func)
            for i,(param_name, param) in enumerate(signature.parameters.items()):
                if len(args) > i:
                    inputs_dict[param_name] = {'arg_name':param_name,'arg_value': args[i], 'arg_type': param.annotation.__name__ if param.annotation else None}
                elif param_name in kwargs_inner:
                    inputs_dict[param_name] = {'arg_name': param_name, 'arg_value': kwargs_inner['param_name'], 'arg_type': param.annotation.__name__ if param.annotation else None}
                elif param.default is not inspect.Parameter.empty:
                    inputs_dict[param_name] = {'arg_name':param_name,'arg_value':  str(param.default), 'arg_type': param.annotation.__name__ if param.annotation else None}
                else:
                    inputs_dict[param_name]={'arg_name':param_name,'arg_value':'none',  'arg_type': param.annotation.__name__ if param.annotation else None}
            _thread_local.input_args = inputs_dict

            variables_need_to_replace =list(set(re.findall(r'{(.*?)}', func.__doc__)))
            if len(variables_need_to_replace) and len([item for item in variables_need_to_replace if item in inputs_dict])== len(variables_need_to_replace):
                docstring= func.__doc__.format(**{k:inputs_dict[k]['arg_value'] for k in variables_need_to_replace})
            else:
                docstring = func.__doc__
            parsed_results =parse_docstring(docstring)

            # 基於 system_prompt, static_instruction 和代碼邏輯生成唯一的 agent key

            signature = inspect.signature(func)
            return_annotation = get_type_hints(func).get('return')
            start_time = time.time()  # 記錄開始時間
            executor = get_current_executor()
            _thread_local.llm_client = func.llm_client
            _thread_local.static_instruction = parsed_results['static_instruction']
            _thread_local.returns =parsed_results[ 'return']

            func_code = func.__code__.co_code.decode('latin1')  # 使用函數的原始字節碼生成唯一 key
            agent_key = generate_agent_key(system_prompt, _thread_local.static_instruction, func_code)


            result = None
            if executor:
                # 委託給 FlowExecutor 執行

                result= executor.execute_agent(func, *args, **kwargs_inner)
            else:
                # 正常執行
                result= func(*args, **kwargs_inner)

            if  return_annotation=='str' or (not isinstance(result, Iterable) and len( _thread_local.returns)==1 and return_annotation  in target_types):
                result = force_cast(result, return_annotation)
            elif not isinstance(result, Iterable) and len( _thread_local.returns)==1 and  _thread_local.returns['return_type'] in target_types:
                result =force_cast(result,_thread_local.returns['return_type'])


            end_time = time.time()  # 記錄結束時間
            execution_time = end_time - start_time  # 計算執行時間
            print(green_color(f"agent {func.__name__}"),yellow_color(f"executed in {execution_time:.4f} seconds"),flush=True)  # 輸出執行時間

            # 使用全域的 collector 來記錄效能數據
            collector.record(instance_id, agent_key, execution_time)
            return result

        return wrapper

    return decorator