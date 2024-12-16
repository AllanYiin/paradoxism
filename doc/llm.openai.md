
# OpenAIClient 類別

## 用途

`OpenAIClient` 是 `LLMClient` 的子類，專為與 OpenAI 平台交互設計，實現了同步與非同步的聊天完成請求方法。

## 屬性

- **client (OpenAI)**: 同步的 OpenAI 客戶端。
- **aclient (AsyncOpenAI)**: 非同步的 OpenAI 客戶端。
- **max_tokens (int)**: 模型最大 token 數。
- **model_info (dict)**: 模型信息字典。
- **params (dict)**: 請求參數字典。

## 方法

### `chat_completion_request`

```python
def chat_completion_request(self, message_with_context, stream=False, use_tool=False, is_json=None, **kwargs):
    ...
```

#### 說明

發送同步聊天完成請求。

#### 引數

- **message_with_context (list)**: 包含上下文的訊息列表。
- **stream (bool, optional)**: 是否使用流式傳輸，預設為 `False`。
- **use_tool (bool, optional)**: 是否使用工具，預設為 `False`。
- **is_json (bool, optional)**: 是否返回 JSON 格式，預設為 `None`。
- **kwargs**: 其他額外參數。

#### 返回

- **dict**: 聊天完成的回應。

#### 範例

```python
client = OpenAIClient(model='gpt-4')
response = client.chat_completion_request(
    message_with_context=[{"role": "user", "content": "Hello, AI"}],
    stream=False
)
print(response)
```

### `async_chat_completion_request`

```python
async def async_chat_completion_request(self, message_with_context, stream=False, use_tool=False, **kwargs):
    ...
```

#### 說明

發送非同步聊天完成請求。

#### 引數

與 `chat_completion_request` 相同。

#### 返回

- **dict**: 聊天完成的回應。

#### 範例

```python
client = OpenAIClient(model='gpt-4')
response = await client.async_chat_completion_request(
    message_with_context=[{"role": "user", "content": "Hello, AI"}],
    stream=False
)
print(response)
```

---

# LLMClientManager 類別

## 用途

`LLMClientManager` 用於管理和切換多個 LLM 客戶端，根據配置文件提供的參數創建客戶端實例。

## 屬性

- **default_model (str)**: 預設使用的模型名稱。
- **tools (list)**: 工具列表。
- **config (dict)**: 配置文件內容。
- **current_client (LLMClient)**: 當前選中的 LLM 客戶端。

## 方法

### `load_config`

```python
def load_config(self, config_file):
    ...
```

#### 說明

從指定的 JSON 文件加載配置並初始化客戶端。

#### 引數

- **config_file (str)**: 配置文件路徑。

#### 範例

```python
manager = LLMClientManager()
manager.load_config('path/to/config.json')
```

### `switch_model`

```python
def switch_model(self, provider, model=None, instance=None):
    ...
```

#### 說明

切換 LLM 提供者和模型。

#### 引數

- **provider (str)**: 提供者名稱，例如 `openai`、`azure` 等。
- **model (str, optional)**: 模型名稱。
- **instance (str, optional)**: 配置文件中定義的實例名稱。

#### 範例

```python
manager.switch_model(provider='openai', model='gpt-4')
```

### `chat_completion_request`

```python
def chat_completion_request(self, message_with_context, parameters, stream=False, use_tool=True):
    ...
```

#### 說明

調用當前選中客戶端的同步聊天完成請求。

#### 範例

```python
manager = LLMClientManager()
manager.switch_model(provider='openai', model='gpt-4')
response = manager.chat_completion_request(
    message_with_context=[{"role": "user", "content": "Hello"}],
    parameters={}
)
```

