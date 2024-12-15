# 平行遞迴函數庫 (Parallel Loop Library)

## 概述

本函數庫旨在高效執行多項平行操作，尤其針對語言模型的應用場景，具有以下特性：

1. ✅**執行格式檢查與強制轉型**：所有輸入數據都會經過型別檢查，並在需要時進行強制轉型以確保輸出符合預期格式。
2. ✅**錯誤處理與重執行機制**：若在執行過程中發生錯誤，或者輸出未通過格式驗證，系統將自動啟動重試機制，最多可重試指定次數。
3. ✅**速率限制**：可設定每分鐘最大執行速率，確保在資源受限或服務器限制的環境下平穩運行。
4. ✅**有序輸出**：無論輸出是 `list` 或 `dict`，都能保持輸入數據的原有順序，`dict` 的鍵對應於輸入的可迭代對象，值為處理結果。
5. ✅**動態資源分配**：根據系統可用資源，自動調整工作者數量以優化性能。
6. ✅**支持惰性求值**：通過返回迭代器的方式延遲計算，適合處理大型數據集，減少不必要的資源消耗。

此外，本函數庫專為語言模型應用設計，可在批量處理、動態生成和數據篩選等場景中發揮強大作用。

---

## 函數清單與詳解

---

### `PAccumulate`

#### 功能

平行地對輸入數據進行累加操作，類似於 `itertools.accumulate`。

#### 引數

- **`func`** (`Callable[[Any, Any], Any]`)：累加函數。
- **`enumerable`** (`Iterable[Any]`)：可迭代的輸入數據。
- **`max_workers`** (`int`, 選填)：最大工作者數量。
- **`rate_limit_per_minute`** (`int`, 選填)：每分鐘執行速率限制。

#### 返回值

累加結果的列表。

#### 範例

```python
from loop import PAccumulate

result = PAccumulate(lambda x, y: x + y, [1, 2, 3, 4])
print(result)  # 輸出: [1, 3, 6, 10]
```

---

### `PCombinations`

#### 功能

計算輸入數據的所有指定長度組合，並應用函數處理每個組合，返回有序結果。

#### 引數

- **`func`** (`Callable[[Any], Any]`)：應用於組合的函數。
- **`enumerable`** (`Iterable[Any]`)：可迭代的輸入數據。
- **`r`** (`int`)：組合的長度。
- **`max_workers`** (`int`, 選填)：最大工作者數量。
- **`max_retries`** (`int`, 選填)：每個元素的最大重試次數。
- **`delay`** (`float`, 選填)：重試間隔時間。
- **`output_type`** (`str`, 選填)：輸出類型，"list" 或 "dict"。
- **`rate_limit_per_minute`** (`int`, 選填)：每分鐘執行速率限制。

#### 返回值

包含組合結果的列表或字典。

#### 範例

```python
from loop import PCombinations

def comb_sum(comb: tuple) -> int:
    return sum(comb)

result = PCombinations(comb_sum, [1, 2, 3, 4], 2)
print(result)  # 輸出: {(1, 2): 3, (1, 3): 4, ...}
```

---

### `PForEach`

#### 功能

平行執行函數並返回結果集合，可選擇輸出類型（`list` 或 `dict`）。支援自定義重試機制和速率限制。

#### 引數

- **`func`** (`Callable[[Any], Any]`)：要應用的函數。
- **`enumerable`** (`Iterable[Any]`)：可迭代的輸入數據。
- **`max_workers`** (`int`, 選填)：最大工作者數量。
- **`max_retries`** (`int`, 選填)：每個元素的最大重試次數。
- **`delay`** (`float`, 選填)：重試間隔時間。
- **`output_type`** (`str`, 選填)：輸出類型，"list" 或 "dict"。
- **`rate_limit_per_minute`** (`int`, 選填)：每分鐘執行速率限制。

#### 返回值

包含每個輸入結果的列表或字典。

#### 範例

```python
from loop import PForEach

def cube(x: int) -> int:
    return x ** 3

result = PForEach(cube, [1, 2, 3, 4], output_type="dict")
print(result)  # 輸出: {1: 1, 2: 8, 3: 27, 4: 64}
```

---

### `PFilter`

#### 功能

對每個元素應用條件函數，平行返回符合條件的值列表。

#### 引數

- **`predicate`** (`Callable[[Any], bool]`)：判斷函數，返回布林值。
- **`enumerable`** (`Iterable[Any]`)：可迭代的輸入數據。
- **`max_workers`** (`int`, 選填)：最大工作者數量。
- **`max_retries`** (`int`, 選填)：每個元素的最大重試次數。
- **`delay`** (`float`, 選填)：重試間隔時間。
- **`rate_limit_per_minute`** (`int`, 選填)：每分鐘執行速率限制。

#### 返回值

符合條件的元素列表。

#### 範例

```python
from loop import PFilter

def is_even(x: int) -> bool:
    return x % 2 == 0

result = PFilter(is_even, range(10))
print(result)  # 輸出: [0, 2, 4, 6, 8]
```

---

### `PMap`

#### 功能

平行地對每個輸入值應用函數，返回結果的惰性求值迭代器。適用於需要高效處理大型數據集並保持輸出順序的場景。

#### 引數

- **`func`** (`Callable[[Any], Any]`)：要應用的函數。
- **`enumerable`** (`Iterable[Any]`)：可迭代的輸入數據。
- **`max_workers`** (`int`, 選填)：最大工作者數量，默認為最佳計算資源。
- **`max_retries`** (`int`, 選填)：每個元素的最大重試次數，默認為 3 次。
- **`delay`** (`float`, 選填)：重試間隔時間（秒），默認為 0.5 秒。
- **`rate_limit_per_minute`** (`int`, 選填)：每分鐘執行速率限制。

#### 返回值

惰性求值的迭代器，按輸入順序返回每個元素的處理結果。

### `PMap` 與 `PForEach` 的差別

- **`PMap`** 支持惰性求值，返回的是迭代器，適合處理大型數據集且希望延遲計算的情境；
- **`PForEach`** 則會立刻返回所有計算結果，可以選擇輸出為 `list` 或 `dict`，適合需要立即取得完整結果的場景。

#### 範例

```python
from loop import PMap

def square(x: int) -> int:
    return x * x

result = PMap(square, range(5))
print(list(result))  # 輸出: [0, 1, 4, 9, 16]
```

