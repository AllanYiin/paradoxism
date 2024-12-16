import json
import os
import glob
from PIL import Image, ImageDraw, ImageFont
import cv2
import numpy as np
from paradoxism.utils import *
from tqdm import tqdm
# 設定字體
FONT_PATH = "C:/Users/Allan/OneDrive/Documents/prompt4all_liteon/prompt4all_liteon/assets/NotoSansTC-Thin.ttf"  # 替換為你系統的中文字體路徑
FONT_SIZE = 36
book_path='C:/Users/Allan/OneDrive/Documents/paradoxism/examples/Making picture books/book16'


def add_text_to_image(image_path, text, font_path, font_size):
    """在圖片下方添加文字，並返回帶文字的 numpy 圖像陣列"""
    image = Image.open(image_path).convert("RGB")
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(font_path, font_size)

    # 計算文字區域
    img_width, img_height = image.size
    text_width = draw.textlength(text, font=font,font_size=FONT_SIZE)
    text_height= draw.textlength(text[0], font=font,font_size=FONT_SIZE)
    x = (img_width - text_width) // 2
    y = img_height-text_height - 60  # 距離底部20像素

    # 添加文字背景
    draw.rectangle([x - 10, y - 30, x + text_width + 10, y + text_height + 30], fill="black")

    # 添加文字
    draw.text((x, y), text, fill="white", font=font)

    # 返回 numpy 陣列格式的圖片
    return np.array(image)


def create_video_from_json(json_path, image_folder, output_video, duration_per_frame=8, fps=15):
    """從 JSON 檔案和圖片資料夾生成影片"""
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    frames = []
    for page, content in tqdm(sorted(data.items(), key=lambda x: int(x[0]))):
        image_path = os.path.join(image_folder, f"{page}.png")  # 假設圖片格式為 jpg
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
    video = cv2.VideoWriter(output_video, fourcc, fps, (width, height))

    # 寫入每一幀
    for frame in tqdm(frames):
        video.write(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))  # PIL 是 RGB，OpenCV 是 BGR

    video.release()
    print(f"影片已成功生成：{output_video}")

folder, filename,ext=split_path(book_path)
# 設定檔案路徑

json_file = glob.glob(os.path.join(book_path,"*.json"))[0]  # JSON檔案路徑
image_folder = book_path  # 圖片資料夾路徑
OUTPUT_VIDEO = os.path.join(book_path,book_path.split('/')[-1]+".mp4")
# 生成影片
create_video_from_json(json_file, image_folder, OUTPUT_VIDEO)
