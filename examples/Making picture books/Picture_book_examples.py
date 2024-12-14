# coding='utf-8-sig'
import time

from paradoxism.base.agent import agent
from paradoxism.base.flow import *
from paradoxism.tools import *
from paradoxism.ops.base import prompt,chain_of_thought
from paradoxism.tools.image_tools import *
from paradoxism.base.loop import PForEach
@agent('gpt-4o','你是一個暢銷的童書繪本作家，你擅長以孩童的純真眼光看這世界，製作出許多溫暖人心的作品。')
def generate_story(story_keyword:str)->dict:
    story = chain_of_thought(f'這是一個關於{story_keyword}的故事，會以擬人化動物作為主要角色，不要走主流路線，可以設計一些比較少人討論到的議題，主角應該要有明確的成長弧線，讓自己變得更好。請撰寫出對應故事綱要')
    pages = prompt(f'將故事大綱細分至預計15個跨頁的篇幅,pages是一個dict，它的key就是第幾頁，它的value也是dict，其中包括了"text"，"image_prompt"分別用來還存放每頁童書的文字(以繁體中文撰寫)以及預計生成出的圖像prompt(以英文撰寫)，請將分頁故事規劃儲存至pages物件中並將pages序列化為json，直接輸出無須解釋',input_kwargs={"story":story},output_type='dict')
    style_base = prompt(f'根據故事大綱思考圖像呈現的總體風格為何，請以5-9歲的孩童為主要客戶來規劃',input_kwargs={"story":story})
    return pages,style_base

@agent('gpt-4o','你是一個才華洋溢的童書繪本繪師')
def image_generation(image_prompt, style_base):
    time.sleep(10)
    img_path=text2im({"size" : "1792x1024", "n" :1, "prompt" :final_prompt,"save_folder":"C:/Users/Allan/OneDrive/Documents/paradoxism/examples/generate_books/book6"})
    return img_path


def make_picture_book():
    pages,style_base=generate_story('自我認同以及自我的價值')
    results=[]

    def make_page(page):
        image_prompt=page['image_prompt']
        text_content=page['text']
        img_path=image_generation(image_prompt, style_base)
        return {'image':img_path,'text':text_content}


    # results=PForEach(make_page,pages.values())
    # open("C:/Users/Allan/OneDrive/Documents/paradoxism/examples/generate_books/book6/results.json",'w',encoding='utf-8').write(json.dumps(results))
    # print(results)




make_picture_book()
