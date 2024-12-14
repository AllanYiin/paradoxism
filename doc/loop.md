# 平行迴圈 Parallel Loop 函式庫

這個函式庫提供了一些工具函數，可以幫助你更容易地平行化處理迴圈和可迭代對象。同時平行作業中若有發生異常，則會自動重新執行。

## 函數列表

* PCombinations：平行地計算一個可迭代對象中所有長度為 r 的組合。
* PForEach：平行執行對於每個枚舉值的函數操作。
* PAccumulate：平行地累加每個枚舉值，類似於 itertools.accumulate。
* PMap：平行地對每個枚舉值應用函數並返回結果的列表。
* PFilter：平行地對每個枚舉值應用判斷函數，並返回符合條件的值。
* PChain：平行地鏈接多個可迭代對象，類似於 itertools.chain。

## 函數說明

### PCombinations

平行地計算一個可迭代對象中所有長度為 r 的組合，並應用給定的函數到每個組合。

**參數：**

* `enumerable`: 可迭代的對象（如列表或集合）
* `r`: 組合的長度
* `func`: 需要對每個組合應用的函數，函數唯一參數是組合值
* `max_workers`: 最大的工作者數量，控制並行的數量，默認為 CPU 的核心數量
* `max_retries`: 當函數執行失敗時的最大重試次數
* `delay`: 每次重試之間的延遲時間
* `output_type`: 輸出類型，"list" 或 "dict"
* `rate_limit_per_minute`: 每分鐘的速率限制

**返回：**

字典，其中包含每個組合及其對應的處理結果。

**範例：**

```python
def example_function(comb):
    return sum(comb)

data = [1, 2, 3, 4]
result = PCombinations(example_function, data, 2)
print(result)  # 輸出: {(1, 2): 3, (1, 3): 4, (1, 4): 5, (2, 3): 5, (2, 4): 6, (3, 4): 7}
```


```
