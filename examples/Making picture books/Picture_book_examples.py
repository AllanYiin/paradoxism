# coding='utf-8-sig'
import time
import os
import random
from paradoxism.base.agent import agent
from paradoxism.base.flow import *
from paradoxism.tools import *
from paradoxism.ops.base import prompt,chain_of_thought
from paradoxism.tools.image_tools import *
from paradoxism.base.loop import PForEach
@agent('gpt-4o','你是一個暢銷的童書繪本作家，你擅長以孩童的純真眼光看這世界，製作出許多溫暖人心的作品。')
def generate_story(story_keyword:str)->dict:
    story = chain_of_thought(f'這是一個關於{story_keyword}的故事，會以擬人化動物作為主要角色(請多元的設定動物種類)，不需要走主流路線，可以設計一些比較少人討論到的議題，主角應該要有明確的成長弧線，讓自己變得更好，但故事的劇情必須合理，請撰寫出對應故事綱要')
    pages = prompt(f'將故事大綱細分至預計15個跨頁的篇幅,pages是一個dict，它的key就是第幾頁，它的value也是dict，其中包括了"page_num","text"，"image_prompt"分別用來還存放頁碼、每頁童書的文字(以繁體中文撰寫)以及預計生成出的圖像prompt(以英文撰寫，而且請將角色的名字改以他實際是什麼動物以及外觀特徵替代)，請將分頁故事規劃儲存至pages物件中並將pages序列化為json，直接輸出無須解釋',input_kwargs={"story":story},output_type='dict',temperature=0.6)
    style_base = prompt(f'根據故事大綱思考圖像呈現的總體風格為何，請以5-9歲的孩童為主要客戶來規劃',input_kwargs={"story":story})
    return pages,style_base

@agent('gpt-4o','你是一個才華洋溢的童書繪本繪師')
def image_generation(image_prompt, style_base,save_folder,page_num=1)->str:
    final_prompt=prompt("請根據style_base為主風格再加上image_prompt以及補充構圖、環境背景、這張圖有出現的角色外觀等細節。至少需要加入3個專業效果詞(光罩效果、渲染效果、視覺風格、筆觸質感)，以及至少1種構圖技巧",input_kwargs={"image_prompt":image_prompt,"style_base":style_base})+'seed=42，直接輸出，無須解釋'
    img_path=text2im({"size" : "1792x1024", "n" :1, "prompt" :final_prompt,"save_folder":save_folder,"save_filename":f"{page_num}.png"})
    return img_path


def make_picture_book():

    # 設定目前目錄為工作目錄
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    print(os.path.dirname(os.path.abspath(__file__)))
    folder = 'book4'

    make_dir_if_need(folder)
    topic_base=['我就是獨特的我','我也喜歡這樣的我','討好性人格','堅毅的友情','比金錢更重要的事','換位思考']
    pages,style_base=generate_story(random.choice(topic_base))
    if len(pages)==1:
        pages=list(pages.values())[0]
    open(os.path.join(folder, "pages.json"), 'w', encoding='utf-8').write(json.dumps(pages))

    results=[]

    def make_page(page):
        image_prompt=page['image_prompt']
        text_content=page['text']
        page_num=page['page_num']
        img_path=image_generation(image_prompt, style_base,folder,page_num=page_num)
        new_path=os.path.join(folder,f"{page_num}.png")
        if new_path!=img_path and os.path.exists(new_path):
            os.remove(new_path)
        if new_path != img_path:
            os.rename(img_path,new_path)
        return {'image':new_path,'text':text_content}


    results=PForEach(make_page,pages.values())
    open(os.path.join(folder,"results.json"),'w',encoding='utf-8').write(json.dumps(results))
    print(results)




make_picture_book()
