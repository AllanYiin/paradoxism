<img src='images/PARADOXISM_LOGO.png' height=360 width=360/>

## Prompt like a Human, Perform like a Machine

在當前的生成式 AI 開發環境中，如何有效管理**大型語言模型（LLM）**的工作流成為開發者面臨的一大挑戰。LLM 的工作流往往涉及複雜的邏輯流程、控制結構，以及低可控的輸出難以符合嚴格的輸出格式要求。傳統上，這些流程需要以繁瑣的代碼來實現，導致開發過程變得冗長且難以維護。

**Paradoxism** 的誕生正是為了解決這一難題。通過引入創新的雙重模式，Paradoxism 將工作流的流程控制以代碼形式呈現，而具體執行細節則使用類似人類語言的Prompt 撰寫，而這種混合模式將其無縫轉換為可執行、高效率、輸出格式確定的真實python代碼的。這樣的設計不僅簡化了開發者的工作負擔，還提升了開發效率與結果的可預測性。

## 核心理念

* **雙重性**: **Paradoxism** 融合了人類語言的表達自由與程式語言的邏輯嚴謹，完美地兼具了創意與執行的雙重性。你可以使用自然語言編寫偽代碼，而系統將它轉化為準確的可執行代碼。
* **跨越邊界**: 不再需要在思考模式與編程邏輯之間來回切換，**Paradoxism** 幫助你跨越人類語言與機器語言的邊界，將兩者自然融合。
* **簡潔與效率**: **Paradoxism** 強調易用性和高效性，你只需像自然語言一樣撰寫偽代碼，程式語言的實現部分將自動生成，提升開發效率。

## 功能特點

* **代碼中融入自然語言**: 透過裝飾器、docstring、以及prompt函數來維護自然語言的邏輯。
* **強制型別檢查確保可控**: 透過docstring或是type hinting的設定來執行強制型別檢查與輸出抽取，以確保輸出格式可控。
* **高效能的併行以及局部重執行**: 無論是初學者還是資深開發者，**Paradoxism** 都能提供靈活的解決方案，適應不同項目的需求。

## 使用範例

只需要在函數上方加入@agent即可設定語言模型，system prompt，而在docstring還可以設定固定的static instruction。在函數上的type hinting會轉為強制型別檢查。而其中的prompt則是根據

```python
# paradoxism
@agent('gpt-4o',system_prompt='你是一個有10年以上口譯經驗且曾經旅居海外的英語翻譯師')
def en_translator(sentence:str)->str:
    """
    你懂得根據輸入內容的原意與語境，在最大程度保留原本文字的風格與言外之意的情況下，翻譯成兼具信達雅的英文版本
    """
    result=prompt(f'請將以下內容翻譯成英文，直接輸出，無須解釋:\n\n"""{sentence}"""')
    return result
```

執行@agent的函數：

```python
print(en_translator('紅豆生南國，春來發幾枝。願君多採擷，此物最相思')) 
-----------------------------------------------------------------------

"""紅豆生南國，春來發幾枝。願君多採擷，此物最相思"""
agent en_translator executed in 3.0094 seconds
Red beans grow in the southern land, how many sprout in springtime's hand. I wish you to gather more, for this is what most evokes longing.
```

## 安裝與教程

安裝程式包

```python
pip install paradoxism
```

要開始使用前請注意你必須要擁有有效的語言模型API，並將api儲存於本機環境變數中
`
openai: "OPENAI_API_KEY"

claude: "ANTHROPIC_API_KEY"`

azure由於一次可能需要維護數台instance，所以無法儲存於單一環境變數，需要將相關資訊維護於oai.json之中，請參考再專案中有放置oai_sample.json，只要以相同格式維護，將檔名修改為oai.json即可

## 專案願景

**Paradoxism** 旨在革新編程的思維方式，讓開發者不再受限於傳統的語法結構，並能輕鬆將想法轉換為實際代碼。我們的願景是創造一個既自由又嚴謹的編程環境，讓創意得以快速落地，同時保持高效的執行。

## 測試方式

安裝開發依賴後，執行所有測試：

```bash
python -m pytest
```
