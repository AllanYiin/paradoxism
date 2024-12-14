# 平行迴圈 Parallel Loop 函式庫

這個函式庫提供了一些工具函數，可以幫助你更容易地平行化處理迴圈和可迭代對象。同時平行作業中若有發生異常，則會自動重新執行

## 函數列表

* PCombinations：平行地計算一個可迭代對象中所有長度為 r 的組合。
* PForEach：平行執行對於每個枚舉值的函數操作。
* PRange：平行化處理一個範圍的數值，類似於 for i in range(start, end)。
* PEnumerate：平行化處理一個枚舉值列表，根據索引取出對應位置作為輸入。
* PAccumulate：平行地累加每個枚舉值，類似於 itertools.accumulate。
* PMap：平行地對每個枚舉值應用函數並返回結果的列表。
* PFilter：平行地對每個枚舉值應用判斷函數，並返回符合條件的值。
* PChain：平行地鏈接多個可迭代對象，類似於 itertools.chain。

## 函數說明

### PCombinations

平行地計算一個可迭代對象中所有長度為 r 的組合，並應用給定的函數到每個組合。

**參數：**

* enumerable: 可迭代的對象（如列表或集合）
* r: 組合的長度
* func: 需要對每個組合應用的函數，函數唯一參數是組合值
* max_workers: 最大的工作者數量，控制並行的數量，默認為 CPU 的核心數量
* retries: 當函數執行失敗時的最大重試次數

**返回：**

字典，其中包含每個組合及其對應的處理結果。

**範例：**

```python
def example_function(comb):
    return sum(comb)

data = [1, 2, 3, 4]
result = PCombinations(data, 2, example_function)
print(result)  # 輸出: {(1, 2): 3, (1, 3): 4, (1, 4): 5, (2, 3): 5, (2, 4): 6, (3, 4): 7}
```

### PForEach

平行執行對於每個枚舉值的函數操作。

**參數：**

* enumerable: 可枚舉的列表或集合（不支持 generator 類型）
* func: 需要執行的函數，函數唯一參數是枚舉值
* max\_workers: 最大的工作者數量，控制並行的數量，默認為 CPU 的核心數量
* retries: 當函數執行失敗時的最大重試次數

**返回：**

字典，其中包含每個枚舉值及其對應的處理結果。適合執行有副作用的操作，例如寫入資料庫等。

**範例：**

**Python**

```
def example_function(item):
    return item * 2

data = [1, 2, 3, 4, 5]
result = PForEach(data, example_function)
print(result)  # 輸出: {1: 2, 2: 4, 3: 6, 4: 8, 5: 10}
```
### PRange

平行化處理一個範圍的數值，類似於 for i in range(start, end)。 如果提供了枚舉值列表，則根據索引取出對應位置作為輸入。

**參數：**

* start: 起始值（包含）
* end: 結束值（不包含）
* func: 需要執行的函數，函數唯一參數是枚舉值
* enumerable: 可選的枚舉值列表，用於根據索引進行處理
* max\_workers: 最大的工作者數量，控制並行的數量，默認為 CPU 的核心數量

**返回：**

字典，其中包含每個數值及其對應的處理結果。

**範例：**

```python
def example_function(item):
    return item * 2

result = PRange(1, 5, example_function)
print(result)  # 輸出: {1: 2, 2: 4, 3: 6, 4: 8}
```


### PEnumerate

平行化處理一個枚舉值列表，根據索引取出對應位置作為輸入。

**參數：**

* enumerable: 可枚舉的列表或集合
* func: 需要執行的函數，函數的參數是 (索引, 值)
* max\_workers: 最大的工作者數量，控制並行的數量，默認為 CPU 的核心數量

**返回：**

字典，其中包含每個索引及其對應的處理結果。

**範例：**

```python
def example_enumerate_function(index, item):
    return f"索引 {index}: {item * 2}"

data = [1, 2, 3]
result = PEnumerate(data, example_enumerate_function)
print(result)  # 輸出: {0: '索引 0: 2', 1: '索引 1: 4', 2: '索引 2: 6'}
```

**請**[謹慎使用](/faq#coding)程式碼。

### PAccumulate

平行地累加每個枚舉值，類似於 itertools.accumulate。

**參數：**

* enumerable: 可枚舉的列表或集合
* func: 累加函數，兩個參數，默認為加法操作
* max\_workers: 最大的工作者數量，控制並行的數量，默認為 CPU 的核心數量

**返回：**

累加結果的列表

**範例：**

```python
data = [1, 2, 3, 4]
result = PAccumulate(data)
print(result)  # 輸出: [1, 3, 6, 10]
```
### PMap

平行地對每個枚舉值應用函數並返回結果的列表。

**參數：**

* enumerable: 可枚舉的列表或集合
* func: 需要應用的函數，函數唯一參數是枚舉值
* max\_workers: 最大的工作者數量，控制並行的數量，默認為 CPU 的核心數量

**返回：**

包含每個函數應用結果的列表。適合需要對每個元素做處理並收集結果的情境，例如數據轉換。

**範例：**

```python
def example_function(item):
    return item * 2

data = [1, 2, 3, 4]
result = PMap(data, example_function)
print(result)  # 輸出: [2, 4, 6, 8]
```
### PFilter

平行地對每個枚舉值應用判斷函數，並返回符合條件的值。

**參數：**

* enumerable: 可枚舉的列表或集合
* predicate: 判斷函數，函數唯一參數是枚舉值，返回 True 或 False
* max\_workers: 最大的工作者數量，控制並行的數量，默認為 CPU 的核心數量

**返回：**

包含符合條件的值的列表

**範例：**

```python
def is_even(item):
    return item % 2 == 0

data = [1, 2, 3, 4, 5]
result = PFilter(data, is_even)
print(result)  # 輸出: [2, 4]
```


### PChain

平行地鏈接多個可迭代對象，類似於 itertools.chain。

**參數：**

* iterables: 多個可迭代的對象
* max\_workers: 最大的工作者數量，控制並行的數量，默認為 CPU 的核心數量

**返回：**

鏈接後的所有元素的列表

**範例：**

```python
result = PChain([1, 2], [3, 4], [5, 6])
print(result)  # 輸出: [1, 2, 3, 4, 5, 6]
```



