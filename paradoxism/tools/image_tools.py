import os
from paradoxism.tools import *
from paradoxism.utils import make_dir_if_need,split_path
from paradoxism.utils.image_utils import preprocess_image_in_memory, encode_image
from PIL import Image, PngImagePlugin
import hashlib
import time
import requests
from io import BytesIO

__all__ = ['text2im','im2text']
client=openai.OpenAI()
def generate_image_filename(prompt: str, n) -> str:
    clean_prompt = ''.join(e for e in prompt if e.isalnum() or e.isspace()).lower().replace(' ', '_').split('_')
    if len(clean_prompt)>=8:
        clean_prompt=clean_prompt[:8]
    clean_prompt='_'.join(clean_prompt)
    timestamp = int(time.time())
    unique_hash = hashlib.md5(f"{prompt}_{timestamp}".encode()).hexdigest()[:8]
    filename = f"{clean_prompt}_{unique_hash}_{n}.png"
    return filename


def save_image_with_metadata(image: Image.Image, prompt: str, filename: str):
    meta = PngImagePlugin.PngInfo()
    if prompt:
        meta.add_text("DALL-E Prompt", prompt)
        image.save(filename, "PNG", pnginfo=meta)
    else:
        image.save(filename, "PNG")
@tool('gpt-4o')
def text2im(prompt, size="1792x1024", quality="standard", style='natural',save_folder="./generate_images",save_filename=None,**kwargs):
    """
    輸入文字prompt以生成圖片的工具函數
    Args:
        prompt: 最終用來生圖的文字prompt，其生成步驟:請評估使用者的視覺需求以轉換為初步prompt底稿，再加入prompt底稿要使用的風格元素，並且prompt底稿中再加入至少3種以上專業風格詞，以及一種以上的構圖技巧，以英文撰寫
        size: 共計有"1792x1024", "1024x1024", "1024x1792"三種選項  若是要做簡報或是提案書建議使用"1792x1024"，若是做logo請使用"1024x1024"，預設為"1792x1024"
        quality:預設皆為"standard"
        style:可用選項為'natural'以及vivid,預設為'natural'
        save_folder:圖片存放路徑
        save_filename:圖片檔名
        **kwargs:

    Returns:
        生成之圖檔

    """

    response = client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        size=size,
        quality=quality,
        style=style,
        n=1
    )
    n=1
    images = []
    make_dir_if_need(save_folder)
    if save_filename:
        name, extension = os.path.splitext(save_filename)
        if not extension:
            save_filename=save_filename+'.png'


    for _i in range(n):
        revised_prompt=response.data[_i].revised_prompt
        image_file = os.path.join(save_folder,save_filename if save_filename else generate_image_filename(revised_prompt, _i))
        img_data = requests.get(response.data[_i].url).content
        save_image_with_metadata(Image.open(BytesIO(img_data)), revised_prompt, image_file)

    return image_file

@tool('gpt-4o')
def im2text(prompt,img_path,**kwargs):
    """

    Args:
        prompt:
        img_path:
        **kwargs:

    Returns:

    """
    content_list = [{
        "type": "text",
        "text": prompt
    }]
    if isinstance(img_path, str) and os.path.isfile(img_path) and split_path(img_path)[-1].lower() in ['.png', '.jpg', '.jpeg', '.webp',  '.bmp', '.tiff', '.ico']:
        base64_image = encode_image(preprocess_image_in_memory(img_path))
        content_list.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{base64_image}"
            }
        })
    response = client.chat.completions.create(
        model='gpt-4o',
        messages=[
            {"role": "system", "content": '你是萬能的視覺助理'},
            {"role": 'user', "content": content_list}
        ],
        temperature=0.2

    )
    return response.choices[0].message.content.strip()
