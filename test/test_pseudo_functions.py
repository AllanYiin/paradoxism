

from paradoxism.base.agent import agent
from paradoxism.ops.base import prompt


@agent(model='gpt-4o',system_prompt='你是一個擅長中文情感偵測的超級幫手')
def emotion_detection(sentence: str) -> dict:
    """
    - 需要偵測的情感類型:
        正面情緒(positive_emotions)=[自信,快樂,體貼,幸福,信任,喜愛,尊榮,期待,感動,感謝,熱門,獨特,稱讚]
        負面情緒(negative_emotions)=[失望,危險,後悔,冷漠,懷疑,恐懼,悲傷,憤怒,擔心,無奈,煩悶,虛假,討厭,貶責,輕視]
    """
    results = prompt('input:'+sentence+'\n\n'+ '當句子中有符合以上任何情感類型時，請盡可能的將符合的「情感類型」(key)及句子中的那些「觸及到情感類型的句子文字內容」(value)成對的列舉出來，一個句子可以觸及不只一種情感，請以dict形式輸出')
    return results

print(emotion_detection('真是好棒棒，你們家沒有活人了嗎'))
print(emotion_detection('記得不要浪費時間與笨蛋爭論，所以你說什麼我都贊同'))