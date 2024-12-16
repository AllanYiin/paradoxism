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
    """
    你的主要目標讀者會是5~9歲之間的兒童˙
    你需要以他們生活中可以理解的概念與行為來表哪你書中的內容
    避免過度艱澀的語言以及沒有明確因果關係的劇情
    Args:
        story_keyword: (str) 劇情主軸

    Returns:

    """
    story = chain_of_thought(f'這是一個關於{story_keyword}的故事，會以擬人化動物作為主要角色(請多元的設定動物種類，同時也要考慮該種動物在繪本視覺呈現上的視覺效果，也要考慮他們應該是食物鏈上不會有吃了彼此的可能)，不需要走主流路線，可以設計一些童書比較少討論到的議題，主角應該要有明確的成長弧線，讓自己變得更好，但故事的劇情必須合理，請撰寫出對應故事綱要')
    pages = prompt(f'將故事大綱細分至預計15個跨頁的篇幅,pages是一個dict，它的key就是第幾頁，它的value也是dict，其中包括了"page_num","text"，"image_prompt"分別用來還存放頁碼、每頁童書的文字(以繁體中文撰寫)以及預計生成出的圖像prompt(以英文撰寫，但是出現角色仍以固定中文名作代稱)，請將分頁故事規劃儲存至pages，直接輸出無須解釋',input_kwargs={"story":story},output_type='dict',temperature=0.6)
    role_style=prompt(f'根據故事中會出現的所有角色，開始構思確保外觀一致性的視覺特徵描述，輸出形式為將角色固定中文名為key，視覺特徵描述為value，直接輸出無須解釋',input_kwargs={"story":story},output_type='dict',temperature=0.6)
    return pages,role_style

@agent('gpt-4o','你是一個才華洋溢的平面設計師兼童書繪本繪師')
def image_generation(image_prompt:str, style_base,role_style,save_folder,page_num=1)->str:
    final_prompt=prompt("在確保維持style_base為主風格的原則下，將原有的image_prompt補充構圖、環境背景等細節，並且本頁有出現的角色基於角色名稱將它代換成role_style中的外觀描述(所以輸出的prompt不該再有名字出現)。至少需要加入3個適合之專業效果詞(光照效果、渲染效果)，以及至少1種構圖技巧，所有圖片都直接滿版周遭不要留白，也不要出現文字",input_kwargs={"image_prompt":image_prompt,"style_base":style_base,"role_style":role_style})+',seed=42，直接輸出，無須解釋'
    img_path=text2im({"size" : "1792x1024", "n" :1, "prompt" :final_prompt,"quality":"hd", "style":'nature',"save_folder":save_folder,"save_filename":f"{page_num}.png"})
    return img_path


def make_picture_book():

    # 設定目前目錄為工作目錄
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    print(os.path.dirname(os.path.abspath(__file__)))
    folder = 'book16'
    style_base = '帶有3D立體感且每個角落都應該充滿細節具有照片等級真實的沉浸感效果，明亮而和諧的色彩，讓整個故事充滿溫暖和活力'
    print('style_base',style_base)
    make_dir_if_need(folder)
    topic_base=['我就是獨特的我','我也喜歡這樣的我','討好性人格','堅毅的友情','比金錢更重要的事','換位思考']
    pages,role_style=generate_story(random.choice(topic_base))
    if len(pages)==1:
        pages=list(pages.values())[0]
    open(os.path.join(folder, "pages.json"), 'w', encoding='utf-8').write(json.dumps(pages, ensure_ascii=False,indent=4))

    results=[]

    def make_page(page):
        image_prompt=page['image_prompt']
        text_content=page['text']
        page_num=page['page_num']
        img_path=image_generation(image_prompt, style_base,role_style,folder,page_num=page_num)
        new_path=os.path.join(folder,f"{page_num}.png")
        if new_path!=img_path and os.path.exists(new_path):
            os.remove(new_path)
        if new_path != img_path:
            os.rename(img_path,new_path)
        return {'image':new_path,'text':text_content}


    results=PForEach(make_page,pages.values())
    open(os.path.join(folder,"results.json"),'w',encoding='utf-8').write(json.dumps(results, ensure_ascii=False,indent=4))
    print(results)


from paradoxism.utils.input_dict_utils import get_input_dict
print(get_input_dict(generate_story))
print(get_input_dict(text2im))
print(get_input_dict(image_generation))
print(get_input_dict(make_picture_book))

make_picture_book()
