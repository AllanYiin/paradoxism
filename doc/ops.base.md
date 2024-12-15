# ops.base

## 概述

`base.py` 是一個提供**與大型語言模型（LLM）交互的工具模組**，旨在通過標準化的輸入與輸出流程，實現靈活的提示構建與結果解析。主要用途包括：

1. 利用自然語言提示（Prompt）與 LLM 模型進行交互。
2. 提供 Chain-of-Thought (CoT) 方法來支持逐步推理。
3. 支援多種格式的結果解析，包括 JSON、XML、YAML 等。

---

## 函數詳解

### `reference(*args, **kwargs)`

生成格式化的多行字符串，適用於構建輸入提示。

#### 輸入參數：

- **`*args` (str)**: 任意數量的字串，將按順序組合成格式化段落。
- **`**kwargs` (dict)**: 可選的鍵值對，提供標題（`title`）與內容（`content`）。

#### 輸出：

- **`str`**: 格式化後的多行字符串。

---

### `prompt(prompt_text: str, input_kwargs=None, output_type: str = 'str', **kwargs)`

執行給定的提示（Prompt），並解析來自 LLM 的回應。

#### 輸入參數：

- **`prompt_text` (str)**: 提示文本。
- **`input_kwargs` (dict, optional)**: 輸入參數，作為提示的附加內容。
- **`output_type` (str)**: 指定輸出格式，可選值為 `'str'`, `'json'`, `'dict'`, `'python'`, `'yaml'`, `'xml'` 等。
- **`**kwargs`**: 其他額外參數傳遞給 LLM。

#### 輸出：

- **`Any`**: 經過解析後的 Python 對象或原始字符串。

---

### `chain_of_thought(prompt_text: str, output_type: str = 'str', **kwargs)`

執行帶有 Chain-of-Thought 方法的提示，返回逐步推理過程的結果。

#### 輸入參數：

- **`prompt_text` (str)**: 提示文本。
- **`output_type` (str)**: 指定輸出格式。
- **`**kwargs`**: 傳遞至內部 LLM 交互的其他參數。

#### 輸出：

- **`Any`**: 包括推理過程的結構化結果。

## 使用案例

### 使用 Prompt 方法

```python
result = prompt("請總結以下文本內容：", input_kwargs={"text": "這是一段示例文本"}, output_type="json")
print(result)
```
