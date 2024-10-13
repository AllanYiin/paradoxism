from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import os
from itertools import accumulate, combinations
from paradoxism.context import get_optimal_workers
from concurrent.futures import ThreadPoolExecutor, Future
from typing import Callable, Any, List, Dict


__all__ = ["PCombinations", "PForEach", "PRange", "PEnumerate", "PAccumulate", "PMap", "PFilter", "PChain"]


def retry_with_fallback(func: Callable, value, max_retries=3, delay=0.5):
    """
    通用重試函數，處理異常或不符合預期的返回值。
    """
    for attempt in range(max_retries):
        try:
            result = func(value)
            if result is not None:  # 確保返回值有效
                return result
            else:
                print(f"重試 {attempt + 1}/{max_retries} 遇到異常: {e}")
        except Exception as e:
            print(f"重試 {attempt + 1}/{max_retries} 遇到異常: {e}")
        time.sleep(delay)  # 延遲後重試
    return None  # 重試失敗返回 None



def PCombinations(func, enumerable, r, max_workers=None, max_retries=3, delay=0.5):
    """
    平行計算所有長度為 r 的組合，並將指定函數應用於每個組合，結果順序與輸入順序一致。
    """
    if isinstance(enumerable, (type(x for x in []), type(iter([])))):
        enumerable = list(enumerable)

    if max_workers is None:
        max_workers = get_optimal_workers()

    combinations_list = list(combinations(enumerable, r))  # 預先計算組合，保證順序
    results = [None] * len(combinations_list)  # 初始化列表以保持順序

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(retry_with_fallback, func, combination, max_retries, delay): idx
                   for idx, combination in enumerate(combinations_list)}

        for future in as_completed(futures):
            index = futures[future]
            try:
                results[index] = future.result()
            except Exception as exc:
                print(f'組合 {combinations_list[index]} 執行失敗: {exc}')
                results[index] = None  # 記錄異常情況

    return results

def PForEach(func, enumerable, max_workers=None, max_retries=3, delay=0.5):
    if isinstance(enumerable, (type(x for x in []), type(iter([])))):
        enumerable = list(enumerable)
    if max_workers is None:
        max_workers = get_optimal_workers()

    results = [None] * len(enumerable)  # 使用列表來保證順序

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(retry_with_fallback, func, value, max_retries, delay): idx
                   for idx, value in enumerate(enumerable)}

        for future in as_completed(futures):
            index = futures[future]
            try:
                results[index] = future.result()
            except Exception as exc:
                results[index] = f"Error after retries: {exc}"

    return results

def PAccumulate(func,enumerable, max_workers=None):
    """
    平行地累加每個枚舉值，類似於 itertools.accumulate。

    :param enumerable: 可枚舉的列表或集合
    :param func: 累加函數，兩個參數，默認為加法操作
    :param max_workers: 最大的工作者數量，控制並行的數量，默認為 CPU 的核心數量
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
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        batch_size = max(1, len(enumerable) // max_workers)
        for i in range(0, len(enumerable), batch_size):
            batch = enumerable[i:i + batch_size]
            futures.append(executor.submit(lambda b: list(accumulate(b, func)), batch))

        for future in as_completed(futures):
            try:
                results.extend(future.result())
            except Exception as exc:
                print(f'批次累加時產生異常: {exc}')

    return results


def PMap(func: Callable, enumerable: Iterable, max_workers=None, max_retries=3, delay=0.5) -> Iterator:
    """
    平行地對每個枚舉值應用函數並返回惰性求值的迭代器。
    :param func: 需要應用的函數
    :param enumerable: 可枚舉的列表或集合
    :param max_workers: 最大工作者數量，默認為 CPU 核心數量
    :param max_retries: 每個元素的最大重試次數
    :param delay: 每次重試間的延遲時間
    :return: 包含每個元素結果的惰性迭代器
    """
    if max_workers is None:
        max_workers = get_optimal_workers()

    # 使用 ThreadPoolExecutor.map 確保順序並發運行
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 包裝帶重試的函數應用到每個元素
        results = executor.map(lambda x: retry_with_fallback(func, x, max_retries, delay), enumerable)

        # 返回迭代器以支援惰性求值
        return results

def PFilter(predicate, enumerable, max_workers=None, max_retries=3, delay=0.5):
    if isinstance(enumerable, (type(x for x in []), type(iter([])))):
        enumerable = list(enumerable)
    if max_workers is None:
        max_workers = get_optimal_workers()

    results = [None] * len(enumerable)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(retry_with_fallback, predicate, value, max_retries, delay): idx
                   for idx, value in enumerate(enumerable)}

        for future in as_completed(futures):
            index = futures[future]
            try:
                if future.result():
                    results[index] = enumerable[index]
            except Exception as exc:
                print(f'枚舉值 {enumerable[index]} 執行判斷時產生最終異常: {exc}')

    return [result for result in results if result is not None]

def PChain(*iterables, max_workers=None):
    """
    平行地鏈接多個可迭代對象，類似於 itertools.chain。

    :param iterables: 多個可迭代的對象
    :param max_workers: 最大的工作者數量，控制並行的數量，默認為 CPU 的核心數量
    :return: 鏈接後的所有元素的列表

    Example:
        >>> PChain([1, 2], [3, 4], [5, 6])
        [1, 2, 3, 4, 5, 6]
    """
    if max_workers is None:
        max_workers = get_optimal_workers()

    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(list, iterable if not isinstance(iterable,
                                                                    (type(x for x in []), type(iter([])))) else list(
            iterable)) for iterable in iterables]
        for future in as_completed(futures):
            try:
                results.extend(future.result())
            except Exception as exc:
                print(f'鏈接可迭代對象時產生異常: {exc}')

    return results