from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import os
from itertools import accumulate, combinations
from paradoxism.context import get_optimal_workers

def PCombinations(enumerable, r, func, max_workers=None, retries=3):
    """
    平行地計算一個可迭代對象中所有長度為 r 的組合，並應用給定的函數到每個組合。

    :param enumerable: 可迭代的對象（如列表或集合）
    :param r: 組合的長度
    :param func: 需要對每個組合應用的函數，函數唯一參數是組合值
    :param max_workers: 最大的工作者數量，控制並行的數量，默認為 CPU 的核心數量
    :param retries: 當函數執行失敗時的最大重試次數
    :return: 字典，其中包含每個組合及其對應的處理結果。

    Example:
        >>> def example_function(comb):
        ...     return sum(comb)
        >>> data = [1, 2, 3, 4]
        >>> PCombinations(data, 2, example_function)
        {(1, 2): 3, (1, 3): 4, (1, 4): 5, (2, 3): 5, (2, 4): 6, (3, 4): 7}
    """
    if isinstance(enumerable, (type(x for x in []), type(iter([])))):
        enumerable = list(enumerable)

    if max_workers is None:
        max_workers = get_optimal_workers()

    results = {}
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {}
        for combination in combinations(enumerable, r):
            future = executor.submit(func, combination)
            futures[future] = combination

        for future in as_completed(futures):
            combination = futures[future]
            _process_combination_future(future, combination, results, executor, func, retries)

    return results


def _process_combination_future(future, combination, results, executor, func, retries):
    """
    處理單個已提交的 future，針對組合的情境。

    :param future: 提交的 future
    :param combination: 與該 future 關聯的組合值
    :param results: 用於存儲結果的字典
    :param executor: ThreadPoolExecutor 實例
    :param func: 需要執行的函數
    :param retries: 當函數執行失敗時的最大重試次數
    """
    retry_count = 0
    while retry_count < retries:
        try:
            result = future.result()
            results[combination] = result
            break
        except Exception as exc:
            retry_count += 1
            if retry_count >= retries:
                print(f'組合 {combination} 執行時產生異常，已達到最大重試次數: {exc}')
                results[combination] = None
            else:
                print(f'組合 {combination} 執行失敗，正在重試 ({retry_count}/{retries})...')
                future = executor.submit(func, combination)


def PForEach(enumerable, func, max_workers=None, retries=3):
    """
    平行執行對於每個枚舉值的函數操作。

    :param enumerable: 可枚舉的列表或集合（不支持 generator 類型）
    :param func: 需要執行的函數，函數唯一參數是枚舉值
    :param max_workers: 最大的工作者數量，控制並行的數量，默認為 CPU 的核心數量
    :param retries: 當函數執行失敗時的最大重試次數
    :return: 字典，其中包含每個枚舉值及其對應的處理結果。適合執行有副作用的操作，例如寫入資料庫等。

    Example:
        >>> def example_function(item):
        ...     return item * 2
        >>> data = [1, 2, 3, 4, 5]
        >>> PForEach(data, example_function)
        {1: 2, 2: 4, 3: 6, 4: 8, 5: 10}
    """
    if isinstance(enumerable, (type(x for x in []), type(iter([])))):
        enumerable = list(enumerable)
    if max_workers is None:
        max_workers = get_optimal_workers()

    results = {}
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for value in enumerable:
            future = executor.submit(func, value)
            _process_future(future, value, results, executor, func, retries)

    return results


def _process_future(future, value, results, executor, func, retries):
    """
    處理單個已提交的 future。

    :param future: 提交的 future
    :param value: 與該 future 關聯的值
    :param results: 用於存儲結果的字典
    :param executor: ThreadPoolExecutor 實例
    :param func: 需要執行的函數
    :param retries: 當函數執行失敗時的最大重試次數
    """
    retry_count = 0
    while retry_count < retries:
        try:
            result = future.result()
            results[value] = result
            break
        except Exception as exc:
            retry_count += 1
            if retry_count >= retries:
                print(f'枚舉值 {value} 執行時產生異常，已達到最大重試次數: {exc}')
                results[value] = None
            else:
                print(f'枚舉值 {value} 執行失敗，正在重試 ({retry_count}/{retries})...')
                future = executor.submit(func, value)


def PRange(start, end, func, enumerable=None, max_workers=None):
    """
    平行化處理一個範圍的數值，類似於 for i in range(start, end)。
    如果提供了枚舉值列表，則根據索引取出對應位置作為輸入。

    :param start: 起始值（包含）
    :param end: 結束值（不包含）
    :param func: 需要執行的函數，函數唯一參數是枚舉值
    :param enumerable: 可選的枚舉值列表，用於根據索引進行處理
    :param max_workers: 最大的工作者數量，控制並行的數量，默認為 CPU 的核心數量

    Example:
        >>> def example_function(item):
        ...     return item * 2
        >>> PRange(1, 5, example_function)
        {1: 2, 2: 4, 3: 6, 4: 8}
    """
    if max_workers is None:
        max_workers = get_optimal_workers()

    if enumerable is not None:
        if isinstance(enumerable, (type(x for x in []), type(iter([])))):
            enumerable = list(enumerable)
        values = [enumerable[i] for i in range(start, min(end, len(enumerable)))]
    else:
        values = range(start, end)
    return PForEach(values, func, max_workers)


def PEnumerate(enumerable, func, max_workers=None):
    """
    平行化處理一個枚舉值列表，根據索引取出對應位置作為輸入。

    :param enumerable: 可枚舉的列表或集合
    :param func: 需要執行的函數，函數的參數是 (索引, 值)
    :param max_workers: 最大的工作者數量，控制並行的數量，默認為 CPU 的核心數量

    Example:
        >>> def example_enumerate_function(index, item):
        ...     return f"索引 {index}: {item * 2}"
        >>> data = [1, 2, 3]
        >>> PEnumerate(data, example_enumerate_function)
        {0: '索引 0: 2', 1: '索引 1: 4', 2: '索引 2: 6'}
    """
    if isinstance(enumerable, (type(x for x in []), type(iter([])))):
        enumerable = list(enumerable)
    if max_workers is None:
        max_workers = get_optimal_workers()

    results = {}
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for index, value in enumerate(enumerable):
            future = executor.submit(func, index, value)
            _process_future(future, index, results, executor, func, retries=3)

    return results


def PAccumulate(enumerable, func=lambda x, y: x + y, max_workers=None):
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


def PMap(enumerable, func, max_workers=None):
    """
    平行地對每個枚舉值應用函數並返回結果的列表。

    :param enumerable: 可枚舉的列表或集合
    :param func: 需要應用的函數，函數唯一參數是枚舉值
    :param max_workers: 最大的工作者數量，控制並行的數量，默認為 CPU 的核心數量
    :return: 包含每個函數應用結果的列表。適合需要對每個元素做處理並收集結果的情境，例如數據轉換。

    Example:
        >>> def example_function(item):
        ...     return item * 2
        >>> data = [1, 2, 3, 4]
        >>> PMap(data, example_function)
        [2, 4, 6, 8]
    """
    if isinstance(enumerable, (type(x for x in []), type(iter([])))):
        enumerable = list(enumerable)
    if max_workers is None:
        max_workers = get_optimal_workers()

    results = [None] * len(enumerable)
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(func, value): index for index, value in enumerate(enumerable)}
        for future in as_completed(futures):
            index = futures[future]
            try:
                results[index] = future.result()
            except Exception as exc:
                print(f'枚舉值 {enumerable[index]} 執行時產生異常: {exc}')
    return results


def PFilter(enumerable, predicate, max_workers=None):
    """
    平行地對每個枚舉值應用判斷函數，並返回符合條件的值。

    :param enumerable: 可枚舉的列表或集合
    :param predicate: 判斷函數，函數唯一參數是枚舉值，返回 True 或 False
    :param max_workers: 最大的工作者數量，控制並行的數量，默認為 CPU 的核心數量
    :return: 包含符合條件的值的列表

    Example:
        >>> def is_even(item):
        ...     return item % 2 == 0
        >>> data = [1, 2, 3, 4, 5]
        >>> PFilter(data, is_even)
        [2, 4]
    """
    if isinstance(enumerable, (type(x for x in []), type(iter([])))):
        enumerable = list(enumerable)
    if max_workers is None:
        max_workers = get_optimal_workers()

    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(predicate, value): value for value in enumerable}
        for future in as_completed(futures):
            value = futures[future]
            try:
                if future.result():
                    results.append(value)
            except Exception as exc:
                print(f'枚舉值 {value} 執行判斷時產生異常: {exc}')
    return results


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