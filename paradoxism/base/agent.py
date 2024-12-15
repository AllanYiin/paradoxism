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
            func.__doc__ = _extract_docstring(func)

        # 使用 threading.Lock 保證對 thread-local 的操作是線程安全的
        lock = threading.Lock()
        with lock:
            _thread_local.llm_client = func.llm_client

        @wraps(func)
        def wrapper(*args, **kwargs_inner):
            instance_id = str(uuid.uuid4())
            try:
                # 產生 inputs_dict
                inputs_dict = _generate_inputs_dict(func, *args, **kwargs_inner)
                with lock:
                    _thread_local.input_args = inputs_dict

                # 格式化並解析 docstring
                docstring = _format_docstring(func.__doc__, inputs_dict)
                parsed_results = parse_docstring(docstring)
                type_hints_results = get_type_hints(func)

                _update_parsed_results(parsed_results, inputs_dict, type_hints_results)

                # 生成 agent key
                func_code = inspect.getsource(func)
                agent_key = generate_agent_key(system_prompt, parsed_results['static_instruction'], func_code)

                start_time = time.time()
                with lock:
                    _thread_local.llm_client = func.llm_client
                    _thread_local.static_instruction = parsed_results['static_instruction']
                    _thread_local.returns = parsed_results['return']
            except:
                PrintException()


            # 執行函數
            result = execute_function(func, *args, **kwargs_inner)
            if len(_thread_local.returns) == 1:
                return_type = _thread_local.returns[0]['return_type']
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

            execution_time = time.time() - start_time
            logger.info(f"agent {func.__name__} executed in {execution_time:.4f} seconds with agent_key: {agent_key} and input_args: {inputs_dict}")

            # 使用全域的 collector 來記錄效能數據
            collector.record(instance_id, agent_key, execution_time)
            return result

        return wrapper

    return decorator

# 新增輔助函數以分離不同邏輯片段，提高代碼可讀性
def _extract_docstring(func: Callable) -> str:
    match = re.search(r'def\s+\w+\s*\(.*?\):\s*f?"""\s*([\s\S]*?)\s*"""', inspect.getsource(func))
    return match.group(1) if match else ''

def _generate_inputs_dict(func: Callable, *args, **kwargs) -> OrderedDict:
    inputs_dict = OrderedDict()
    signature = inspect.signature(func)
    for i, (param_name, param) in enumerate(signature.parameters.items()):
        if len(args) > i:
            inputs_dict[param_name] = {
                'arg_name': param_name,
                'arg_value': args[i],
                'arg_type': param.annotation.__name__ if param.annotation else None
            }
        elif param_name in kwargs:
            inputs_dict[param_name] = {
                'arg_name': param_name,
                'arg_value': kwargs[param_name],
                'arg_type': param.annotation.__name__ if param.annotation else None
            }
        elif param.default is not inspect.Parameter.empty:
            inputs_dict[param_name] = {
                'arg_name': param_name,
                'arg_value': str(param.default),
                'arg_type': param.annotation.__name__ if param.annotation else None
            }
        else:
            inputs_dict[param_name] = {
                'arg_name': param_name,
                'arg_value': 'none',
                'arg_type': param.annotation.__name__ if param.annotation else None
            }
    return inputs_dict

def _format_docstring(docstring: str, inputs_dict: OrderedDict) -> str:
    variables_need_to_replace = list(set(re.findall(r'{(.*?)}', docstring)))
    if variables_need_to_replace and all(var in inputs_dict for var in variables_need_to_replace):
        return docstring.format(**{k: inputs_dict[k]['arg_value'] for k in variables_need_to_replace})
    return docstring

def _update_parsed_results(parsed_results: dict, inputs_dict: OrderedDict, type_hints_results: dict):
    inputs_dict_keys = list(inputs_dict.keys())
    for idx, item in enumerate(parsed_results['input_args']):
        if item['arg_name'] in inputs_dict_keys:
            ref = inputs_dict[item['arg_name']]
            if ref['arg_type']:
                parsed_results['input_args'][idx]['arg_type'] = ref['arg_type']
            inputs_dict_keys.remove(item['arg_name'])
        if not item['arg_type'] and item['arg_name'] in type_hints_results:
            parsed_results['input_args'][idx]['arg_type'] = type_hints_results[item['arg_name']].__name__
    for k in inputs_dict_keys:
        if k in type_hints_results:
            parsed_results['input_args'].append({'arg_name': k, 'arg_type': type_hints_results[k].__name__})
