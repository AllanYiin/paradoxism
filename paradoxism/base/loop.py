from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import os
from itertools import accumulate, combinations
from paradoxism.context import get_optimal_workers
from concurrent.futures import ThreadPoolExecutor, Future
from typing import Callable, Any, List, Dict,Iterable, Iterator
import traceback
from paradoxism.context import PrintException
__all__ = ["PCombinations", "PForEach",  "PMap", "PFilter"]


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
                print(f"重試 {attempt + 1}/{max_retries} 失敗: 返回 None, 索引: {index}, 值: {value}")
        except Exception as e:
            print(f"重試 {attempt + 1}/{max_retries} 遇到異常: 索引: {index}, 值: {value}, 異常原因: {traceback.format_exc()}")
        time.sleep(delay)

    print(f"達到最大重試次數: {max_retries}，放棄索引: {index}, 值: {value}")
    return None



def PForEach(func, enumerable, max_workers=None, max_retries=3, delay=0.5, output_type="list", rate_limit_per_minute=None):
    """
    平行地對每個枚舉值應用函數，並返回結果列表或字典，支援重試機制和速率限制。

    :param func: 需要應用的函數
    :param enumerable: 可枚舉的列表或集合
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
        [1, 'Error after retries: Error on 2', 3, 4]

        >>> PForEach(square, [1, 2, 3, 4], output_type="dict")
        {1: 1, 2: 4, 3: 9, 4: 16}
    """
    if isinstance(enumerable, (type(x for x in []), type(iter([])))):
        enumerable = list(enumerable)
    if max_workers is None:
        max_workers = get_optimal_workers()

    results = [None] * len(enumerable)

    # 若有設定rate_limit_per_minute，計算需要的延遲間隔(秒)
    interval = None
    if rate_limit_per_minute and rate_limit_per_minute > 0:
        interval = 60.0 / rate_limit_per_minute

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {}
        for idx, value in enumerate(enumerable):
            # 若有設定速率限制，每次提交任務前都等一下
            if interval is not None and idx > 0:
                time.sleep(interval)

            future = executor.submit(retry_with_fallback, func, value, idx, max_retries, delay)
            futures[future] = idx

        for future in as_completed(futures):
            index = futures[future]
            try:
                results[index] = future.result()
            except Exception as exc:
                results[index] = f"Error after retries: {exc}"

    if output_type == "dict":
        return dict(zip(enumerable, results))
    return results
def PAccumulate(func, enumerable, max_workers=None, rate_limit_per_minute=None):
    """
    平行地累加每個枚舉值，類似於 itertools.accumulate。

    :param enumerable: 可枚舉的列表或集合
    :param func: 累加函數，兩個參數，默認為加法操作
    :param max_workers: 最大的工作者數量，控制並行的數量，默認為 CPU 的核心數量
    :param rate_limit_per_minute: 每分鐘的速率限制
    :return: 累加結果的列表

    Example:
        >>> data = [1, 2, 3, 4]
        >>> PAccumulate(data)
        [1, 3, 6, 10]
    """
    if isinstance(enumerable, (type(x for x in []), type(iter([])))):
        enumerable = list(enumerable)
    if max_workers is None:
        max_workers = get_optimal_workers()

    results = []
    interval = None
    if rate_limit_per_minute and rate_limit_per_minute > 0:
        interval = 60.0 / rate_limit_per_minute

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        batch_size = max(1, len(enumerable) // max_workers)
        for i in range(0, len(enumerable), batch_size):
            if interval is not None and i > 0:
                time.sleep(interval)
            batch = enumerable[i:i + batch_size]
            futures.append(executor.submit(lambda b: list(accumulate(b, func)), batch))

        for future in as_completed(futures):
            try:
                results.extend(future.result())
            except Exception as exc:
                print(f'批次累加時產生異常: {exc}')

    return results

def PCombinations(func, enumerable, r, max_workers=None, max_retries=3, delay=0.5, output_type="list", rate_limit_per_minute=None):
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
                print(f'組合 {combinations_list[index]} 執行失敗: {exc}')
                results[index] = None  # 記錄異常情況
    if output_type=="dict":
        return dict(zip(combinations_list, results))
    return results

def PMap(func: Callable, enumerable: Iterable, max_workers=None, max_retries=3, delay=0.5, rate_limit_per_minute=None) -> Iterator:
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
                print(f'枚舉值 {enumerable[index]} 執行判斷時產生最終異常: {exc}')

    return [result for result in results if result is not None]

def PChain(*iterables, max_workers=None, rate_limit_per_minute=None):
    """
    平行地鏈接多個可迭代對象，類似於 itertools.chain。

    :param iterables: 多個可迭代的對象
    :param max_workers: 最大的工作者數量，控制並行的數量，默認為 CPU 的核心數量
    :param rate_limit_per_minute: 每分鐘的速率限制
    :return: 鏈接後的所有元素的列表

    Example:
        >>> PChain([1, 2], [3, 4], [5, 6])
        [1, 2, 3, 4, 5, 6]
    """
    if max_workers is None:
        max_workers = get_optimal_workers()

    interval = None
    if rate_limit_per_minute and rate_limit_per_minute > 0:
        interval = 60.0 / rate_limit_per_minute

    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        for idx, iterable in enumerate(iterables):
            if interval is not None and idx > 0:
                time.sleep(interval)
            futures.append(executor.submit(list, iterable if not isinstance(iterable, (type(x for x in []), type(iter([])))) else list(iterable)))

        for future in as_completed(futures):
            try:
                results.extend(future.result())
            except Exception as exc:
                print(f'鏈接可迭代對象時產生異常: {exc}')

    return results