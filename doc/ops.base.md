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

`ops.bae.prompt` 函數的最終執行的完整提示（final prompt）的構成如下：

### Final Prompt 組成邏輯

**系統指令 (`system_prompt`)**

- 來自 `@agent` 的 `system_prompt`，這是一個對整體交互邏輯有指導意圖的描述，影響 LLM 的輸出風格或格式。
- 
  **靜態指令 (`static_instruction`)**

- 這部分通常是由 `@agent` 裝飾器提供的靜態上下文，通過 `_thread_local.static_instruction` 獲取。

**主提示文本 (`prompt_text`)**

- 這是用戶提供的主要提示內容。

**輸入參數格式化 (`input_info`)**

- 如果有提供輸入參數（`input_kwargs`），則通過 `reference` 函數將參數以指定格式嵌入到提示中。

**輸出格式後綴 (`output_type` 提示)**

- 如果 `output_type` 指定為 `json` 或 `dict`，會附加 `請以json的格式輸出` 的指令。

5. **合併構成**
   
   - 最終完整提示是以以下格式組合：
     ```
     {static_instruction}
     {prompt_text}
     {input_info}
     ```

---

### Mermaid 圖表表示

可以使用以下 `mermaid` 流程圖來表示構成：

````mermaid
graph TD
A[Start] --> B[讀取 @agent 的 system_prompt]
B --> C[檢查 static_instruction]
C --> D[讀取 prompt_text]
D --> E[檢查prompt的引數input_kwargs]
E -->|有指定輸入| F[格式化參數為 input_info]
E -->|無指定輸入| G[跳過參數]
F --> H[檢查 output_type 是否為 json/dict]
G --> H
H -->|是| I[附加 請以json的格式輸出]
H -->|否| J[保持原提示]
I --> K[組合: system_prompt + static_instruction + prompt_text + input_info + json 提示]
J --> K[組合: system_prompt + static_instruction + prompt_text + input_info]
K --> L[Final Prompt]
````



這個圖表表明了從開始到構建完整提示的邏輯流程，涵蓋了靜態指令、主要提示文本、輸入參數以及輸出格式化指令的整合過程。

