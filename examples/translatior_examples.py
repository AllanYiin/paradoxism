from paradoxism.base.agent import agent
from paradoxism.ops.base import prompt
from paradoxism.utils.utils import *

@agent(model='gpt-4o',system_prompt='你是一個擅長多國語言的的翻譯高手，你懂得根據輸入內容的原意與語境，在最大程度保留原本文字的風格與言外之意的情況下，翻譯成兼具信達雅的指定語種版本')
def translator(input_string, to_language):
    translated_result= prompt(f'請將以下內容翻譯成{to_language}，直接輸出，無須解釋:\n\n"""{input_string}"""')
    return translated_result

@agent(model='gpt-4o',system_prompt='你是一個30年口譯經驗的專家')
def rethinker(input_string, translated_string, to_language):
    f"""
    你熟悉{to_language}語言的各種細膩的處理技巧，以下是你針對翻譯上的幾個重要堅持:
        - 你會檢視原文中有無字義未被納入在譯文裡，以及譯文中有無對於原文過度翻譯或者是意義背離的問題。
        - 如果因為語言間的差異有些幽默點或者是精心設計的文字趣味無法直接翻譯，以也會建議在{to_language}可以怎麼處理來致敬原文的設計精巧之處
        - 若是原文中有包括諷刺、暗喻、隱喻等修辭技巧，以應該要呈現在藝文之中
        - 如果是詩詞，則會重視發音的節奏與押韻，盡量能將原文的音律巧妙的重現於譯文中
        - 如果是涉及人名、地名、公司名...等專有名詞，則應與{to_language}中通用性稱呼一致
    """
    comment =prompt(f'以下兩段文字，第一段是原文，第二段是翻譯為{to_language}的譯文，請你針對這樣的翻譯是否還有可以更精進優化的空間給予具體的改進意見，以及那些是你覺得值得讚賞的優秀之處?你只提出觀點與看法，不要提供整份調整後譯文\n\n"""{input_string}"""\n\n"""{translated_string}"""')
    return comment

@agent(model='gpt-4o',system_prompt='你是一個擅長多國語言的的翻譯高手，你懂得根據輸入內容的原意與語境，在最大程度保留原本文字的風格與言外之意的情況下，翻譯成兼具信達雅的指定語種版本')
def reviser(input_string, translated_string, to_language, comment):
    revised_version =prompt(f'以下三段文字，第一段是原文，第二段是翻譯為{to_language}的譯文，以及第三段是其他翻譯專家針對這次翻譯給予的改進建議以及讚賞，請根據上述專家意見，將譯文進行修改與調整，優點處請務必保留，缺點處則需要調整，未提及之處則視狀況保留或是修正，以求兼具信達雅，直接輸出，無須解釋!!\n\n"""{input_string}"""\n\n"""{translated_string}"""\n\n"""{comment}"""')
    return revised_version

def full_translate(input_string,to_language):
    print(f'Original:\n{input_string}')
    translated_string=translator(input_string, to_language)
    n=1
    print(blue_color(f'Version {n}:\n{translated_string}'))
    for _ in range(3):
        comment=rethinker(input_string, translated_string, to_language)
        print(f'Version {n} comment:\n{comment}')
        revised_version=reviser(input_string, translated_string, to_language, comment)
        print(blue_color(f'Version {n+1} :\n{revised_version}'))
        translated_string=revised_version
        n+=1


input_string='昨夜雨疏風驟，濃睡不消殘酒。試問卷簾人，卻道海棠依舊。知否，知否？應是綠肥紅瘦'
#ainput_string="""To dissimulate is to feign not to have what one has. To simulate is to feign to have what one hasn't. One implies a presence, the other an absence. But the matter is more complicated, since to simulate is not simply to feign: "Someone who feigns an illness can simply go to bed and pretend he is ill. Someone who simulates an illness produces in himself some of the symptoms" (Littre). Thus, feigning or dissimulating leaves the reality principle intact: the difference is always clear, it is only masked; whereas simulation threatens the difference between "true" and "false", between "real" and "imaginary". Since the simulator produces "true" symptoms, is he or she ill or not? The simulator cannot be treated objectively either as ill, or as not ill. Psychology and medicine stop at this point, before a thereafter undiscoverable truth of the illness. For if any symptom can be "produced," and can no longer be accepted as a fact of nature, then every illness may be considered as simulatable and simulated, and medicine loses its meaning since it only knows how to treat "true" illnesses by their objective causes. Psychosomatics evolves in a dubious way on the edge of the illness principle. As for psychoanalysis, it transfers the symptom from the organic to the unconscious order: once again, the latter is held to be real, more real than the former; but why should simulation stop at the portals of the unconscious? Why couldn't the "work" of the unconscious be "produced" in the same way as any other symptom in classical medicine? Dreams already are."""

full_translate(input_string,to_language='jp-JP')