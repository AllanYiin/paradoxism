
# 中文自然語言處理範例說明文件

## 案例背景

此案例展示了一個專門為中文設計的自然語言處理系統，包含分詞、情感分析、實體識別以及意圖檢測等功能。系統基於 GPT-4 小型模型進行處理，透過多個代理函數實現高效的中文處理工作。

## 主要功能

### 1. 中文分詞 (`chinese_seg`)
- 功能：根據中文語意在輸入句子中插入分隔符 `|`，實現中文分詞。
- 系統提示：模型被設置為一個擅長中文分詞的專家，對中文語意有深入理解。
- 輸出：返回分詞結果。

範例程式碼：
```python
@agent(model='gpt-4o-mini', system_prompt='你是一個擅長中文自然語言處理的超級幫手', temperature=0.2)
def chinese_seg(sentence: str) -> str:
    """
    請依照中文語意插入"|"以表示中文分詞。
    Args:
        sentence: 欲分詞的句子。
    Returns:
        分詞結果。
    """
```

### 2. 中文情感分析 (`emotion_detection`)
- 功能：從句子中偵測多種類型的正面和負面情緒。
- 系統提示：模型被設置為擅長偵測中文情感的超級助手。
- 輸出：返回情感類型及相關文字內容的字典。

範例程式碼：
```python
@agent(model='gpt-4o-mini', system_prompt='你是一個擅長中文情感偵測的超級幫手')
def emotion_detection(sentence: str) -> dict:
    """
    偵測句子中的情感類型並輸出相關文字內容。
    """
```

### 3. 中文實體識別 (`entity_detection`)
- 功能：從句子中識別中文實體類型（如人名、地點、品牌名等）。
- 系統提示：模型被設置為擅長中文實體識別的專家。
- 輸出：返回實體類型及相關文字內容的字典。

範例程式碼：
```python
@agent(model='gpt-4o-mini', system_prompt='你是一個擅長中文實體識別的超級幫手')
def entity_detection(sentence: str) -> dict:
    """
    偵測句子中的實體類型並輸出相關文字內容。
    """
```

### 4. 中文意圖識別 (`intent_detection`)
- 功能：偵測句子中潛在的意圖（如訂票、查詢資訊等）。
- 系統提示：模型被設置為擅長意圖識別的中文助手。
- 輸出：返回意圖類型及相關文字內容的字典。

範例程式碼：
```python
@agent(model='gpt-4o-mini', system_prompt='你是一個擅長中文意圖識別的超級幫手')
def intent_detection(sentence: str) -> dict:
    """
    偵測句子中的意圖並輸出相關文字內容。
    """
```

## 完整處理流程 (`chinese_nlp`)
- 功能：將多個功能結合在一起，對多個句子進行批量處理，輸出分詞、情感分析、實體識別和意圖識別的結果。
- 輸入：多個換行分隔的句子。
- 輸出：以 JSON 格式輸出每個句子的完整處理結果。

範例程式碼：
```python

def chinese_nlp(input_sentences: str) -> JSON:
    input_sentences = input_sentences.split('\n')
    all_outputs = {}
    for sent in input_sentences:
        sent = sent.strip()
        if not sent:
            continue
        output = {'sentence': sent}
        print(f"Processing: {sent}")
        output['chinese_seg'] = chinese_seg(sent)
        output['emotion_detection'] = emotion_detection(sent)
        output['entity_detection'] = entity_detection(sent)
        output['intent_detection'] = intent_detection(sent)
        all_outputs[sent]=output
    json_result = to_json(all_outputs)
    return json_result

```

## 測試範例
```python
test_sentences = """
大哥去二哥家，去找三哥說四哥被五哥騙去六哥家偷了七哥放在八哥房間裡的九哥借給十哥想要送給十一哥的1000元，請問誰是小偷。
我今天非常高興，因為我獲得了升職。
請幫我訂明天下午3點去台北的火車票。
"""

result = chinese_nlp(test_sentences.strip())
print(result)
```

## 附註
- 此範例需在已設定有效 OpenAI API 金鑰的環境下運行。
- 請確保安裝了所需的 `paradoxism` 庫。
