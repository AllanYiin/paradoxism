import json
from paradoxism.base.agent import agent
from paradoxism.base.flow import *
from paradoxism.base.tool import *
from paradoxism.ops.base import prompt,chain_of_thought
from paradoxism.tools.image_tools import *
from paradoxism.base.loop import PForEach
import os

print(os.getcwd())
style='A futuristic tarot card design with a technological feel. The characters depicted should be represented in abstract humanoid shapes without facial features. The background should be silver-white, and the card surface can have small areas with different colors, but should maintain a cool, technological glow.'
make_dir_if_need("C:/Users/Allan/OneDrive/Documents/paradoxism/examples/tarots")
@agent('gpt-4o','這是一個塔羅牌的卡片生成代理')
def card_generation(key,style=style):
    revised_promt = prompt(f'請畫出一張關於{key}的塔羅牌，基於這樣的風格:{style}，請同時考量{key}所代表的視覺意象，具體的用文字描述出來，將它拓展為更具體描述其視覺元素與數量相關內容的prompt，以英文撰寫，直接輸出無須解釋 ',output_type='str')
    img_path = text2im({"size": "1024x1792", "n": 1, "prompt": revised_promt,
                        "save_folder": "C:/Users/Allan/OneDrive/Documents/paradoxism/examples/tarots","save_filename":key.replace(" ","_")})
    return {"img_path":img_path,"revised_promt":revised_promt}



with open('../examples/tarot_card_prompts_modern.json','r',encoding='utf-8') as f:
    card_dict=json.load(f)
    results=PForEach(card_generation,card_dict.keys(),rate_limit_per_minute=15)
    with open('../examples/revised_promts.json','w',encoding='utf-8') as wf:
        json.dump(results,fw)
