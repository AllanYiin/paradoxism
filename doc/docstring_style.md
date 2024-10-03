在paradoxism中，docstring是一種常用來附載偽代碼邏輯的容器。目前paradoxism中支持多種常見的 `docstring` 格式，如 Plain風格、Google 風格、Numpy 風格、epytext 風格和 reStructuredText 風格。解析結果將會被轉換為結構化的字典，包含靜態描述、輸入參數及返回值等信息，方便對 `docstring` 進行進一步的分析和處理。

---

### 支援的docstring格式

### 1. Plain 風格

`Plain` 風格的 `docstring` 是最簡單的一種，它不使用任何特殊的標記來描述參數或返回值，而是簡單地以自然語言來描述函數的功能、輸入和輸出。這種風格的 `docstring` 結構相對自由，但在解析時仍然可以提取相關信息。

#### 範例

```python
def emotion_detection(sentence: str) -> dict:
    """
    This function detects emotions in a given sentence.

    The function analyzes the sentence and identifies emotional content. It categorizes the emotions into positive and negative types.

    - Positive emotions: 自信, 快樂, 體貼, 幸福, 信任, 喜愛, 尊榮, 期待, 感動, 感謝, 熱門, 獨特, 稱讚
    - Negative emotions: 失望, 危險, 後悔, 冷漠, 懷疑, 恐懼, 悲傷, 憤怒, 擔心, 無奈, 煩悶, 虛假, 討厭, 貶責, 輕視

    Parameters:
    - sentence (str): The input sentence to analyze for emotional content.

    Returns:
    - dict: A dictionary where the keys are the detected emotions and the values are the corresponding phrases from the sentence.
    """
    results = prompt(&#39;input:&#39;+sentence)
    return results
```

#### 2. Google 風格

Google 風格的 `docstring` 通常以清晰的 `Args` 和 `Returns` 標題來描述參數和返回值。這種風格結構清晰易讀，非常適合用於詳細的文檔撰寫。

#### 範例

```python
def emotion_detection(sentence: str) -> dict:
    """
    Detect emotions in a given sentence.

    Args:
        sentence (str): The sentence to analyze for emotional content.

    Returns:
        dict: A dictionary where the keys are the detected emotions, and the values are the corresponding phrases from the sentence.

    Positive emotions:
    - 自信, 快樂, 體貼, 幸福, 信任, 喜愛, 尊榮, 期待, 感動, 感謝, 熱門, 獨特, 稱讚

    Negative emotions:
    - 失望, 危險, 後悔, 冷漠, 懷疑, 恐懼, 悲傷, 憤怒, 擔心, 無奈, 煩悶, 虛假, 討厭, 貶責, 輕視
    """
    results = prompt('input:'+sentence)
    return results
```

---

#### 3. Numpy 風格

Numpy 風格常用於科學計算相關的文檔，這種格式對於參數、返回值的描述更加規範，並且以較為正式的格式呈現。

#### 範例

```python
def emotion_detection(sentence: str) -> dict:
    """
    Detect emotions in a given sentence.

    Parameters
    ----------
    sentence : str
        The sentence to analyze for emotional content.

    Returns
    -------
    dict
        A dictionary where the keys are detected emotions, and the values are corresponding phrases from the sentence.

    Positive emotions:
    - 自信, 快樂, 體貼, 幸福, 信任, 喜愛, 尊榮, 期待, 感動, 感謝, 熱門, 獨特, 稱讚

    Negative emotions:
    - 失望, 危險, 後悔, 冷漠, 懷疑, 恐懼, 悲傷, 憤怒, 擔心, 無奈, 煩悶, 虛假, 討厭, 貶責, 輕視
    """
    results = prompt('input:'+sentence)
    return results
```

---

#### 4. epytext 風格

epytext 是一種用於 Python 的 `docstring` 格式，廣泛用於 `Javadoc` 風格的文檔撰寫，特點是參數和返回值以 `@param` 和 `@return` 標記進行描述。

#### 範例

```python
def emotion_detection(sentence: str) -> dict:
    """
    Detect emotions in a given sentence.

    @param sentence: The sentence to analyze for emotional content.
    @type sentence: str

    @return: A dictionary where keys are detected emotions and values are the corresponding phrases from the sentence.
    @rtype: dict

    Positive emotions:
    - 自信, 快樂, 體貼, 幸福, 信任, 喜愛, 尊榮, 期待, 感動, 感謝, 熱門, 獨特, 稱讚

    Negative emotions:
    - 失望, 危險, 後悔, 冷漠, 懷疑, 恐懼, 悲傷, 憤怒, 擔心, 無奈, 煩悶, 虛假, 討厭, 貶責, 輕視
    """
    results = prompt('input:'+sentence)
    return results
```

---

#### 5. reStructuredText 風格

reStructuredText 是一種靈活、易擴展的標記語言，通常用於撰寫 Python 文檔。這種格式使用 `:param` 和 `:return` 來標記參數和返回值。

#### 範例

```python
def emotion_detection(sentence: str) -> dict:
    """
    Detect emotions in a given sentence.

    :param sentence: The sentence to analyze for emotional content.
    :type sentence: str

    :returns: A dictionary where keys are detected emotions and values are the corresponding phrases from the sentence.
    :rtype: dict

    Positive emotions:
    - 自信, 快樂, 體貼, 幸福, 信任, 喜愛, 尊榮, 期待, 感動, 感謝, 熱門, 獨特, 稱讚

    Negative emotions:
    - 失望, 危險, 後悔, 冷漠, 懷疑, 恐懼, 悲傷, 憤怒, 擔心, 無奈, 煩悶, 虛假, 討厭, 貶責, 輕視
    """
    results = prompt('input:'+sentence)
    return results
```

---

### 支援的風格總覽

1. **Plain 風格** - 沒有使用任何特殊標記，自然語言描述參數和返回值。
2. **Google 風格** - 通過 `Args` 和 `Returns` 標題來清晰地描述參數和返回值。
3. **Numpy 風格** - 使用 `Parameters` 和 `Returns` 格式化地描述參數和返回值，常見於科學計算領域。
4. **epytext 風格** - 使用 `@param` 和 `@return` 標記來描述參數和返回值，類似於 Javadoc。 5. **reStructuredText 風格** - 使用 `:param` 和 `:returns:` 標記，靈活且擴展性好，常用於 Python 文檔撰寫。

