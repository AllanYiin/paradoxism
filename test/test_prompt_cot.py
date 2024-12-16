# from paradoxism.base.agent import agent
# from paradoxism.ops.base import *
# @agent('gpt-4o',system_prompt='你是潛台詞翻譯機')
# def subtext_translator_prompt(input_string):
#     results=prompt('請基於input_string反思，用冷靜且一針見血的語氣，使用**一句話**來詮釋這句話的背後最深沉最黑暗最冷血與殘酷的潛台詞。',
#                    input_kwargs={'input_string':input_string},temperature=0.1)
#     return results
#
# subtext_translator_prompt('年輕人別把錢看得那麼重要')

from paradoxism.base.agent import agent
from paradoxism.ops.base import *
@agent('gpt-4o', system_prompt='你是潛台詞翻譯機')
def subtext_translator_cot(input_string):
    results = chain_of_thought('請基於input_string反思，用冷靜且一針見血的語氣，使用**一句話**來詮釋這句話的背後最深沉最黑暗最冷血與殘酷的潛台詞。',
                     input_kwargs={'input_string': input_string},temperature=0.1)
    return results

subtext_translator_cot('年輕人別把錢看得那麼重要')