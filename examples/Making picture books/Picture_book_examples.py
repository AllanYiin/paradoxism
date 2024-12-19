# coding='utf-8-sig'
import time
import os
import random
import json
import os
import glob
from tqdm import tqdm
from PIL import Image, ImageDraw, ImageFont
import cv2
import numpy as np
from pydub import AudioSegment
from paradoxism.base.agent import agent
from paradoxism.base.flow import *
from paradoxism.tools import *
from paradoxism.ops.base import prompt, chain_of_thought
from paradoxism.tools.image_tools import *
from paradoxism.base.loop import PForEach
from paradoxism.utils import *
from moviepy.editor import VideoFileClip, ImageClip, concatenate_videoclips, AudioFileClip
import openai


@agent('gpt-4o', '你是一個暢銷的童書繪本作家，你擅長以孩童的純真眼光看這世界，製作出許多溫暖人心的作品。')
def generate_story(story_keyword: str) -> dict:
    """
    你的主要目標讀者會是5~9歲之間的兒童˙
    你需要以他們生活中可以理解的概念與行為來表達你書中的內容
    避免過度艱澀的語言、過度簡化或是沒有明確因果關係的劇情
    Args:
        story_keyword: (str) 劇情主軸

    Returns:

    """
    story = chain_of_thought(
        f'這是一個關於{story_keyword}的故事，會以擬人化動物作為主要角色(在兼顧該種動物在繪本視覺呈現上的視覺效果是否可愛的前提下請腦洞大開的多元的挑選主角的動物種類(可以是這世界上真實動物，也可以是古籍經典中的神獸)以及劇情背景發生地(未必是森林，也許是海洋、濕地、火山地...)，也要考慮主要角色間應該是不存在食物鏈會有吃了彼此的可能)，不需要走主流路線，可以討論童書比較少提到的議題，主角應該要有明確的成長弧線，讓自己變得更好，但故事的劇情必須合理，請撰寫出對應故事綱要',
        temperature=0.9)
    pages = prompt(
        f'將故事大綱細分至預計15個跨頁的篇幅,pages是一個dict，它的key就是第幾頁，它的value也是dict，其中包括了"page_num","text"，"image_prompt"分別用來還存放頁碼、每頁童書的文字(以繁體中文撰寫)以及預計生成出的圖像prompt(以英文撰寫，但是出現角色仍以固定中文名作代稱)，請將分頁故事規劃儲存至pages，直接輸出無須解釋',
        input_kwargs={"story": story}, output_type='dict', temperature=0.5)
    role_style = prompt(
        f'根據故事中會出現的所有角色，開始構思確保外觀一致性的視覺特徵描述，輸出形式為將角色固定中文名為key，視覺特徵描述為value，直接輸出無須解釋',
        input_kwargs={"story": story}, output_type='dict', temperature=0.6)
    return pages, role_style


@agent('gpt-4o', '你是一個才華洋溢的平面設計師兼童書繪本繪師')
def image_generation(image_prompt: str, style_base, role_style, save_folder, page_num=1) -> str:
    final_prompt = prompt(
        "在確保維持style_base為主風格的原則下，將原有的image_prompt補充構圖、環境背景等細節，並且本頁有出現的角色基於角色名稱將它代換成role_style中的外觀描述(所以輸出的prompt不該再有名字出現)。至少需要加入3個適合之專業效果詞(光照效果、渲染效果)，以及至少1種構圖技巧，所有圖片都直接滿版周遭不要留白，也不要出現文字",
        input_kwargs={"image_prompt": image_prompt, "style_base": style_base,
                      "role_style": role_style}) + ',seed=42，直接輸出，無須解釋'
    img_path = text2im({"size": "1792x1024", "n": 1, "prompt": final_prompt, "quality": "hd", "style": 'nature',
                        "save_folder": save_folder, "save_filename": f"{page_num}.png"})
    return img_path


def make_video_from_book(book_path, duration_per_frame=6, fps=15):
    def add_text_to_image(image_path, text, font_path, font_size):
        """在圖片下方添加文字，並返回帶文字的 numpy 圖像陣列"""
        image = Image.open(image_path).convert("RGB")
        draw = ImageDraw.Draw(image)
        font = ImageFont.truetype(font_path, font_size)

        # 計算文字區域
        img_width, img_height = image.size
        text_width = draw.textlength(text, font=font, font_size=FONT_SIZE)
        text_height = draw.textlength(text[0], font=font, font_size=FONT_SIZE)
        x = (img_width - text_width) // 2
        y = img_height - text_height - 60  # 距離底部20像素

        # 添加文字背景
        draw.rectangle([x - 10, y - 30, x + text_width + 10, y + text_height + 30], fill="black")

        # 添加文字
        draw.text((x, y), text, fill="white", font=font)

        # 返回 numpy 陣列格式的圖片
        return np.array(image)

    def create_video_from_json(json_path, image_folder, output_video_path, duration_per_frame=6, fps=15):
        """從 JSON 檔案和圖片資料夾生成影片"""
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        frames = []
        for page, content in tqdm(sorted(data.items(), key=lambda x: int(x[0]))):
            image_path = os.path.join(image_folder, f"{page}.png")  # 假設圖片格式為 png
            if not os.path.exists(image_path):
                print(f"圖片 {image_path} 不存在，跳過...")
                continue

            # 添加文字到圖片
            text = content["text"]
            frame = add_text_to_image(image_path, text, FONT_PATH, FONT_SIZE)
            frames.extend([frame] * (duration_per_frame * fps))  # 每張圖顯示 duration_per_frame 秒

        # 獲取影像大小
        height, width, layers = frames[0].shape

        # 初始化影片編碼器
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # 設定影片格式為 mp4
        video = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))

        # 寫入每一幀
        for frame in tqdm(frames):
            video.write(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))  # PIL 是 RGB，OpenCV 是 BGR

        video.release()
        print(f"影片已成功生成：{output_video_path}")

    FONT_PATH = "assets/NotoSansTC-Thin.ttf"
    FONT_SIZE = 36

    folder, filename, ext = split_path(book_path)
    # 設定檔案路徑

    json_file = glob.glob(os.path.join(book_path, "*.json"))[0]  # JSON檔案路徑
    image_folder = book_path  # 圖片資料夾路徑
    output_video_path = os.path.join(book_path, "book_video.mp4")
    # 生成影片
    create_video_from_json(json_file, image_folder, output_video_path)

#製作繪本影片
def make_video_from_book_with_audio(book_path, fps=15):
    def add_text_to_image(image_path, text, font_path, font_size):
        """在圖片下方添加文字，並返回帶文字的 numpy 圖像陣列"""
        image = Image.open(image_path).convert("RGB")
        draw = ImageDraw.Draw(image)
        font = ImageFont.truetype(font_path, font_size)

        # 計算文字區域
        img_width, img_height = image.size
        text_width = draw.textlength(text, font=font, font_size=FONT_SIZE)
        text_height = draw.textlength(text[0], font=font, font_size=FONT_SIZE)
        x = (img_width - text_width) // 2
        y = img_height - text_height - 90  # 距離底部20像素

        # 添加文字背景
        draw.rectangle([x - 10, y - 30, x + text_width + 10, y + text_height + 30], fill="black")

        # 添加文字
        draw.text((x, y), text, fill="white", font=font)

        return np.array(image)

    def generate_audio_from_text(text, output_path):
        """使用 OpenAI API 將文本轉換為音頻"""
        client = openai.OpenAI(timeout=60)
        response = client.audio.speech.create(
            model="tts-1",
            voice="onyx",
            input=text,
        )

        response.stream_to_file(output_path)

    def create_video_with_audio(json_path, image_folder, output_video_path, audio_folder, font_path, font_size, fps):
        """從 JSON 檔案和圖片資料夾生成帶音頻的影片"""
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        clips = []
        for page, content in tqdm(sorted(data.items(), key=lambda x: int(x[0]))):
            image_path = os.path.join(image_folder, f"{page}.png")  # 假設圖片格式為 png
            if not os.path.exists(image_path):
                print(f"圖片 {image_path} 不存在，跳過...")
                continue

            # 生成文字圖片
            text = content["text"]
            frame = add_text_to_image(image_path, text, font_path, font_size)

            # 保存當前圖片為臨時文件

            temp_image_path = os.path.join(image_folder, 'images', f"temp_{page}.png")
            if os.path.exists(temp_image_path):
                os.remove(temp_image_path)
            Image.fromarray(frame).save(temp_image_path)

            # 生成音頻
            audio_path = os.path.join(audio_folder, f"{page}.mp3")
            if os.path.exists(audio_path):
                os.remove(audio_path)
            generate_audio_from_text(text, audio_path)

            # 獲取音頻時長
            audio = AudioSegment.from_file(audio_path)
            duration = len(audio) / 1000

            # 創建視頻剪輯
            audio_clip = AudioFileClip(audio_path)
            video_clip = ImageClip(temp_image_path, duration=duration).set_audio(audio_clip)
            clips.append(video_clip)

        # 合併所有片段
        final_clip = concatenate_videoclips(clips)
        final_clip.write_videofile(output_video_path, fps=fps, codec="libx264", audio_codec="aac")

    FONT_PATH = "assets/NotoSansTC-Thin.ttf"
    FONT_SIZE = 36

    json_file = glob.glob(os.path.join(book_path, "*.json"))[0]  # JSON檔案路徑
    image_folder = book_path  # 圖片資料夾路徑
    audio_folder = os.path.join(book_path, "audio")
    os.makedirs(audio_folder, exist_ok=True)
    os.makedirs(os.path.join(book_path, "images"), exist_ok=True)
    output_video_path = os.path.join(book_path, "book_video_with_audio.mp4")

    # 生成影片
    create_video_with_audio(json_file, image_folder, output_video_path, audio_folder, FONT_PATH, FONT_SIZE, fps)
    print(f"影片已成功生成：{output_video_path}")


book_folder = 'book19'


def make_picture_book(book_folder):
    # 設定目前目錄為工作目錄
    example_path = os.path.dirname(os.path.abspath(__file__))
    book_path = os.path.join(example_path, book_folder)
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    print(os.path.dirname(os.path.abspath(__file__)))

    style_base = '帶有3D立體感且每個角落都應該充滿細節具有照片等級真實的沉浸感效果，明亮而和諧的色彩，讓整個故事充滿溫暖和活力'

    make_dir_if_need(book_path)
    topic_bases = ['我就是獨特的我', '我也喜歡這樣的我', '討好性人格', '堅毅的友情', '比金錢更重要的事', '換位思考']
    this_topic = random.choice(topic_bases)
    print('this_topic', this_topic, 'style_base', style_base)
    #
    # pages, role_style = generate_story(this_topic)
    # if len(pages) == 1:
    #     pages = list(pages.values())[0]
    # open(os.path.join(book_path, "pages.json"), 'w', encoding='utf-8').write(
    #     json.dumps(pages, ensure_ascii=False, indent=4))
    #
    # results = []
    #
    # def make_page(page):
    #     image_prompt = page['image_prompt']
    #     text_content = page['text']
    #     page_num = page['page_num']
    #     img_path = image_generation(image_prompt, style_base, role_style, book_path, page_num=page_num)
    #     new_path = os.path.join(book_path, f"{page_num}.png")
    #     if new_path != img_path and os.path.exists(new_path):
    #         os.remove(new_path)
    #     if new_path != img_path:
    #         os.rename(img_path, new_path)
    #     return {'image': new_path, 'text': text_content}
    #
    # # 透過PForEach並行處理每一頁
    # # Dalle速率上限每分鐘15頁
    # results = PForEach(make_page, pages.values(), rate_limit_per_minute=15)
    #
    # open(os.path.join(book_path, "results.json"), 'w', encoding='utf-8').write(
    #     json.dumps(results, ensure_ascii=False, indent=4))
    # print(results)
    # 製作童書動畫
    make_video_from_book_with_audio(book_path)


make_picture_book(book_folder)
