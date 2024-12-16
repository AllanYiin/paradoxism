# LLMClient 類別

## 用途

`LLMClient` 是一個基礎類別，用於封裝與大語言模型 (LLM) 交互的基本功能。該類別可被子類繼承並實現特定的請求方法，如同步或異步的聊天完成請求。

## 屬性

- **model (str)**: LLM 模型名稱。
- **tools (list)**: 工具列表。
- **client (object)**: 同步 LLM 客戶端。
- **aclient (object)**: 非同步 LLM 客戶端。
- **system_prompt (str)**: 系統提示詞。
- **temperature (float)**: 文本生成的隨機性參數。
- **params (dict)**: 用於配置請求參數的字典。

## 方法

### `chat_completion_request`

```python
def chat_completion_request(self, message_with_context, parameters=None, stream=False, use_tool=True):
    raise NotImplementedError("Subclasses should implement this method")
```

#### 說明

必須在子類中實現的同步聊天完成請求方法。

#### 引數

- **message_with_context (list)**: 含上下文的訊息列表。
- **parameters (dict, optional)**: 附加參數。
- **stream (bool, optional)**: 是否使用流式傳輸，預設為 `False`。
- **use_tool (bool, optional)**: 是否使用工具，預設為 `True`。

### `async_chat_completion_request`

```python
async def async_chat_completion_request(self, message_with_context, parameters=None, stream=False, use_tool=True):
    raise NotImplementedError("Subclasses should implement this method")
```

#### 說明

必須在子類中實現的非同步聊天完成請求方法。

#### 引數

與 `chat_completion_request` 相同。
----------


