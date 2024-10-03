from paradoxism.utils.docstring_utils import parse_docstring
from paradoxism.utils.utils import *
import json





#  Plain docstring (簡單文本格式)
docstr1="""
    This function detects emotions in a sentence.

    Emotions detected:
    - Positive emotions: 自信, 快樂, 體貼, 幸福, 信任, 喜愛, 尊榮, 期待, 感動, 感謝, 熱門, 獨特, 稱讚
    - Negative emotions: 失望, 危險, 後悔, 冷漠, 懷疑, 恐懼, 悲傷, 憤怒, 擔心, 無奈, 煩悶, 虛假, 討厭, 貶責, 輕視

    Parameters:
    sentence (str): The input sentence to analyze emotions.

    Returns:
    dict: A dictionary with detected emotions as keys and corresponding phrases from the sentence as values.
    
    Examples:
    >>> analyze_emotion("I'm so happy!")
    """

print(json.dumps(parse_docstring(docstr1), indent=4, ensure_ascii=False))

#epyText docstring


docstr2="""
   This function detects emotions in a sentence.

   @param sentence: The input sentence to analyze emotions.
   @type sentence: str

   @return: A dictionary with detected emotions as keys and corresponding phrases from the sentence.
   @rtype: dict

   Emotions detected:
   - Positive emotions: 自信, 快樂, 體貼, 幸福, 信任, 喜愛, 尊榮, 期待, 感動, 感謝, 熱門, 獨特, 稱讚
   - Negative emotions: 失望, 危險, 後悔, 冷漠, 懷疑, 恐懼, 悲傷, 憤怒, 擔心, 無奈, 煩悶, 虛假, 討厭, 貶責, 輕視
   """
print(json.dumps(parse_docstring(docstr2,style= 'epytext'), indent=4, ensure_ascii=False))



#Google docstring
docstr3="""
    Detect emotions in a given sentence.

    Args:
        sentence (str): The sentence that will be analyzed for emotional content.

    Returns:
        dict: A dictionary where keys are the detected emotion types and values are the corresponding phrases from the sentence.

    Examples:
    >>> analyze_emotion("I'm so happy!")
    
    Positive emotions:
    - 自信, 快樂, 體貼, 幸福, 信任, 喜愛, 尊榮, 期待, 感動, 感謝, 熱門, 獨特, 稱讚

    Negative emotions:
    - 失望, 危險, 後悔, 冷漠, 懷疑, 恐懼, 悲傷, 憤怒, 擔心, 無奈, 煩悶, 虛假, 討厭, 貶責, 輕視
    """

print(json.dumps(parse_docstring(docstr3, style='google'), indent=4, ensure_ascii=False))




#Numpy docstring
docstr4= """
    Detect emotions in a sentence.

    Parameters
    ----------
    sentence : str
        The input sentence to analyze emotions.

    Returns
    -------
    dict
        A dictionary where the keys are detected emotions and the values are corresponding phrases from the sentence.

    Positive emotions:
    - 自信, 快樂, 體貼, 幸福, 信任, 喜愛, 尊榮, 期待, 感動, 感謝, 熱門, 獨特, 稱讚

    Negative emotions:
    - 失望, 危險, 後悔, 冷漠, 懷疑, 恐懼, 悲傷, 憤怒, 擔心, 無奈, 煩悶, 虛假, 討厭, 貶責, 輕視
    """




print(json.dumps(parse_docstring(docstr4,style= 'numpy'), indent=4, ensure_ascii=False))



#reStructuredText docstring
docstr5="""
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

print(json.dumps(parse_docstring(docstr5,style= 'restructured'), indent=4, ensure_ascii=False))