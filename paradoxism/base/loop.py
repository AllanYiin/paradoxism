import os
import time
import traceback
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import as_completed
from itertools import accumulate, combinations
from typing import Callable, Iterable, Iterator, List, Dict, Any,Union
from paradoxism.context import get_optimal_workers
from collections.abc import ItemsView
import logging
__all__ = ["PCombinations", "PForEach", "PMap", "PFilter"]


def retry_with_fallback(func, value, index, max_retries=3, delay=0.5):
    """
    通用重試函數，處理異常或不符合預期的返回值。
    :param func: 需要執行的函數
    :param value: 傳入函數的參數值
    :param index: 傳入值在enumerable中的索引
    :param max_retries: 最大重試次數
    :param delay: 每次重試之間的延遲時間
    :return: 若成功則返回結果，否則為 None
    """
    for attempt in range(max_retries):
        try:
            result = func(value)
            if result is not None:
                return result
            else:
                logging.warning("重試 %s/%s 失敗: 返回 None, 索引: %s, 值: %s", attempt + 1, max_retries, index, value)
        except Exception as e:
            logging.error(
                "重試 %s/%s 遇到異常: 索引: %s, 值: %s, 異常原因: %s", attempt + 1, max_retries, index, value, traceback.format_exc())
        time.sleep(delay)

    logging.error("達到最大重試次數: %s，放棄索引: %s, 值: %s", max_retries, index, value)
    return None


def PForEach(func, enumerable, max_workers=None, max_retries=3, delay=0.5, output_type="list",
             rate_limit_per_minute=None):
    """
    平行地對每個枚舉值應用函數，並返回結果列表或字典，支援重試機制和速率限制。
    可處理一般可枚舉對象以及 dict.items()。

    :param func: 需要應用的函數
    :param enumerable: 可枚舉的列表、集合或字典的 items
    :param max_workers: 最大工作者數量，默認為最佳工作者數量
    :param max_retries: 每個元素的最大重試次數
    :param delay: 每次重試間的延遲時間
    :param output_type: 輸出類型，"list" 或 "dict"
    :param rate_limit_per_minute: 每分鐘的速率限制
    :return: 包含每個元素結果的列表或字典

    Example:
        >>> def square(x):
        ...     return x * x
        >>> PForEach(square, [1, 2, 3, 4])
        [1, 4, 9, 16]

        >>> def fail_on_two(x):
        ...     if x == 2:
        ...         raise ValueError("Error on 2")
        ...     return x
        >>> PForEach(fail_on_two, [1, 2, 3, 4], max_retries=2)
        [1,None, 3, 4]

        >>> PForEach(square, [1, 2, 3, 4], output_type="dict")
        {1: 1, 2: 4, 3: 9, 4: 16}

        >>> def concat_kv(k, v):
        ...     return f"{k}-{v}"
        >>> PForEach(concat_kv, {"a": 1, "b": 2}.items(), output_type="dict")
        {'a': 'a-1', 'b': 'b-2'}
    """
    if isinstance(enumerable, (type(x for x in []), type(iter([])))):  # 處理生成器或迭代器
        enumerable = list(enumerable)

    # 判斷是否是 dict.items()，需要解包鍵值對
    is_dict_items = isinstance(enumerable,ItemsView)

    if max_workers is None:
        max_workers = get_optimal_workers()

    results = [None] * len(enumerable)

    # 若有設定 rate_limit_per_minute，計算需要的延遲間隔(秒)
    interval = None
    if rate_limit_per_minute and rate_limit_per_minute > 0:
        interval = 60.0 / rate_limit_per_minute

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {}
        for idx, value in enumerate(enumerable):
            # 若有設定速率限制，每次提交任務前都等一下
            if interval is not None and idx > 0:
                time.sleep(interval)

            # 解包鍵值對或直接傳值
            if is_dict_items:
                future = executor.submit(retry_with_fallback, lambda kv: func(*kv), value, idx, max_retries, delay)
            else:
                future = executor.submit(retry_with_fallback, func, value, idx, max_retries, delay)

            futures[future] = idx

        for future in as_completed(futures):
            index = futures[future]
            try:
                results[index] = future.result()
            except Exception as exc:
                results[index] = f"Error after retries: {exc}"

    if output_type == "dict":
        if is_dict_items:
            return dict(zip((k for k, _ in enumerable), results))  # 只保留鍵並組裝結果
        return dict(zip(enumerable, results))
    return results

def PAccumulate(func, enumerable, max_workers=None, max_retries=3, delay=0.5,output_type="list", rate_limit_per_minute=None):
    """
    平行地累加每個枚舉值，類似於 itertools.accumulate。

    :param enumerable: 可枚舉的列表或集合
    :param func: 累加函數，兩個參數，默認為加法操作
    :param max_workers: 最大的工作者數量，控制並行的數量，默認為 CPU 的核心數量
    :param rate_limit_per_minute: 每分鐘的速率限制
     :param output_type: 輸出格式，"list" 或 "dict"，默認為 "dict"。
        - "dict": 返回輸入單元與其函數結果的映射字典，格式為 {key: {function_name: result}}。
        - "list": 返回函數結果的列表，格式為 [{function_name: result}, ...]。
    :return: 累加結果的列表

    Example:
        >>> def identity(x):
        ...     return x
        >>> data = [1, 2, 3, 4]
        >>> PAccumulate(identity, data)
        [1, 3, 6, 10]
    """
    if isinstance(enumerable, (type(x for x in []), type(iter([])))):
        enumerable = list(enumerable)
    if max_workers is None:
        max_workers = get_optimal_workers()

    results = [None] * len(enumerable)
    interval = None
    if rate_limit_per_minute and rate_limit_per_minute > 0:
        interval = 60.0 / rate_limit_per_minute

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {}
        batch_size = max(1, len(enumerable) // max_workers)
        for i in range(0, len(enumerable), batch_size):
            if interval is not None and i > 0:
                time.sleep(interval)
            batch = enumerable[i:i + batch_size]
            future = executor.submit(lambda b: list(accumulate(b, func)), batch)
            futures[future] = (i, batch)

        for future in as_completed(futures):
            try:
                start_index, batch = futures[future]
                accumulated_batch = future.result()
                for j, value in enumerate(accumulated_batch):
                    results[start_index + j] = value
            except Exception as exc:
                logging.error('批次累加時產生異常: %s', exc)
    for i,value in enumerate(results):
        if i==0:
            pass
        else:
            results[i]=results[i]+results[i-1]
    if output_type=='dict':
        return dict(zip(enumerable, results))
    return results


def PCombinations(func, enumerable, r, max_workers=None, max_retries=3, delay=0.5, output_type="list",
                  rate_limit_per_minute=None):
    """
    平行計算所有長度為 r 的組合，並將指定函數應用於每個組合，結果順序與輸入順序一致。
    """
    if isinstance(enumerable, (type(x for x in []), type(iter([])))):
        enumerable = list(enumerable)

    if max_workers is None:
        max_workers = get_optimal_workers()

    combinations_list = list(combinations(enumerable, r))  # 預先計算組合，保證順序
    results = [None] * len(combinations_list)  # 初始化列表以保持順序

    interval = None
    if rate_limit_per_minute and rate_limit_per_minute > 0:
        interval = 60.0 / rate_limit_per_minute

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {}
        for idx, combination in enumerate(combinations_list):
            if interval is not None and idx > 0:
                time.sleep(interval)
            future = executor.submit(retry_with_fallback, func, combination, idx, max_retries, delay)
            futures[future] = idx

        for future in as_completed(futures):
            index = futures[future]
            try:
                results[index] = future.result()
            except Exception as exc:
                logging.error('組合 %s 執行失敗: %s', combinations_list[index], exc)
                results[index] = None  # 記錄異常情況
    if output_type == "dict":
        return dict(zip(combinations_list, results))
    return results


def PMap(func: Callable, enumerable: Iterable, max_workers=None, max_retries=3, delay=0.5,
         rate_limit_per_minute=None) -> Iterator:
    """
    平行地對每個枚舉值應用函數並返回惰性求值的迭代器，支援重試機制。
    :param func: 需要應用的函數
    :param enumerable: 可枚舉的列表或集合
    :param max_workers: 最大工作者數量，默認為 CPU 核心數量
    :param max_retries: 每個元素的最大重試次數
    :param delay: 每次重試間的延遲時間
    :param rate_limit_per_minute: 每分鐘的速率限制
    :return: 包含每個元素結果的惰性迭代器
    """
    if max_workers is None:
        max_workers = min(32, (os.cpu_count() or 1) + 4)  # 動態獲取最佳工作者數量

    interval = None
    if rate_limit_per_minute and rate_limit_per_minute > 0:
        interval = 60.0 / rate_limit_per_minute

    # 使用 ThreadPoolExecutor.map 確保順序並發運行
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 包裝帶重試的函數應用到每個元素，傳入索引和值
        def wrapped_func(x):
            if interval is not None and x[0] > 0:
                time.sleep(interval)
            return retry_with_fallback(func, x[1], x[0], max_retries, delay)

        results = executor.map(wrapped_func, enumerate(enumerable))

        # 返回迭代器以支援惰性求值
        return results


def PFilter(predicate, enumerable, max_workers=None, max_retries=3, delay=0.5, rate_limit_per_minute=None):
    """
    平行地對每個枚舉值應用判斷函數，並返回符合條件的結果列表，支援重試機制和速率限制。

    :param predicate: 判斷函數，返回布林值
    :param enumerable: 可枚舉的列表或集合
    :param max_workers: 最大工作者數量，默認為最佳工作者數量
    :param max_retries: 每個元素的最大重試次數
    :param delay: 每次重試間的延遲時間
    :param rate_limit_per_minute: 每分鐘的速率限制
    :return: 包含符合條件的元素的列表

    Example:
        >>> def is_even(x):
        ...     return x % 2 == 0
        >>> PFilter(is_even, [1, 2, 3, 4])
        [2, 4]

        >>> def fail_on_two(x):
        ...     if x == 2:
        ...         raise ValueError("Error on 2")
        ...     return x % 2 == 0
        >>> PFilter(fail_on_two, [1, 2, 3, 4], max_retries=2)
        [4]
    """
    if isinstance(enumerable, (type(x for x in []), type(iter([])))):
        enumerable = list(enumerable)
    if max_workers is None:
        max_workers = get_optimal_workers()

    results = [None] * len(enumerable)

    interval = None
    if rate_limit_per_minute and rate_limit_per_minute > 0:
        interval = 60.0 / rate_limit_per_minute

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {}
        for idx, value in enumerate(enumerable):
            if interval is not None and idx > 0:
                time.sleep(interval)
            future = executor.submit(retry_with_fallback, predicate, value, idx, max_retries, delay)
            futures[future] = idx

        for future in as_completed(futures):
            index = futures[future]
            try:
                if future.result():
                    results[index] = enumerable[index]
            except Exception as exc:
                logging.error('枚舉值 %s 執行判斷時產生最終異常: %s', enumerable[index], exc)

    return [result for result in results if result is not None]



def PBranch(
    funcs: List[Callable[[Any], Any]],
    enumerable: Iterable[Any],
    max_workers: int = None,
    rate_limit_per_minute: int = None,
    max_retries: int = 3,
    delay: float = 0.5,
    output_type: str = "dict"
) -> Union[List[Dict[str, Any]], Dict[Any, Dict[str, Any]]]:
    """
     平行地對每個枚舉值應用函數，並返回結果列表或字典，支援重試機制和速率限制。

     :param funcs: 需要應用於每個輸入單元的函數列表。
    :param enumerable: 可迭代的輸入數據。
    :param max_workers: 最大工作者數量，默認為函數數量的兩倍。
    :param rate_limit_per_minute: 每分鐘的總速率限制（所有函數執行總和）。
    :param max_retries: 函數執行失敗時的最大重試次數。
    :param delay: 重試間隔時間（秒）。
    :param output_type: 輸出格式，"list" 或 "dict"，默認為 "dict"。
        - "dict": 返回輸入單元與其函數結果的映射字典，格式為 {key: {function_name: result}}。
        - "list": 返回函數結果的列表，格式為 [{function_name: result}, ...]。
    :return: 包含函數處理結果的結構化輸出，格式取決於 output_type。

    Example:
        >>> def func1(x):
        ...     return 2 * x
        >>> def func2(x):
        ...     return x + 5
        >>> results = PBranch(
        ...     funcs=[func1, func2],
        ...     enumerable=[1, 2, 3],
        ...     rate_limit_per_minute=60,
        ...     output_type="dict"
        ... )
        >>> print(results)
        {1: {'func1': 2, 'func2': 6}, 2: {'func1': 4, 'func2': 7}, 3: {'func1': 6, 'func2': 8}}
     """

    if max_workers is None:
        max_workers = get_optimal_workers()

    # 預先配置輸出結構
    results = [None] * len(enumerable)

    # 設置速率限制
    interval = None
    if rate_limit_per_minute:
        interval = 60.0 / rate_limit_per_minute

    def execute_with_retries(func: Callable, value: Any) -> Any:
        for attempt in range(max_retries):
            try:
                return func(value)
            except Exception as e:
                logging.warning("重試 %s/%s 次失敗，原因: %s", attempt + 1, max_retries, e)
                time.sleep(delay)
        return f"Error after {max_retries} retries"

    def process_item(idx, item):
        # 每個輸入單元的結果字典
        item_results = {}
        for func in funcs:
            func_name = func.__name__
            item_results[func_name] = execute_with_retries(func, item)
        return idx, item_results

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(process_item, idx, item): idx for idx, item in enumerate(enumerable)}
        last_execution_time = time.time()

        for future in as_completed(futures):
            if interval:
                elapsed = time.time() - last_execution_time
                if elapsed < interval:
                    time.sleep(interval - elapsed)
                last_execution_time = time.time()

            idx, item_results = future.result()
            results[idx] = item_results

    # 返回對應輸出格式
    if output_type == "list":
        return results
    return {enumerable[idx]: result for idx, result in enumerate(results)}