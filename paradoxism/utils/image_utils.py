from PIL import Image as pil_image
from PIL.ExifTags import TAGS, GPSTAGS
import numpy as np
import base64
import os
import io
from io import BytesIO
__all__ = ['image2array','array2image','mask2array','array2mask','encode_image','decode_base64','preprocess_image_in_memory']

def image2array(img):
    """

    Args:
        img (string, pillow image or numpy.ndarray): Image to be converted to ndarray.

    Returns:
        ndarray  (HWC / RGB)
    """
    if isinstance(img, str):
        if os.path.exists(img) and img.split('.')[-1].lower() in ('jpg', 'jpeg', 'png', 'bmp', 'tiff'):
            img = pil_image.open(img)


    arr = None
    if isinstance(img, PngImageFile):
        arr = np.array(img.im).astype(np.float32)
    if isinstance(img, pil_image.Image):
        arr = np.array(img).astype(np.float32)
    elif isinstance(img, np.ndarray):
        arr = img
        if arr.ndim not in [2, 3]:
            raise ValueError('image should be 2 or 3 dimensional. Got {} dimensions.'.format(arr.ndim))
        if arr.ndim == 3:
            if arr.shape[2] in [3, 4] and arr.shape[0] not in [3, 4]:
                pass
            elif arr.shape[0] in [1, 3, 4]:
                arr = arr.transpose([1, 2, 0])
            else:
                raise ValueError('3d image should be 1, 3 or 4 channel. Got {} channel.'.format(arr.shape[0]))
        arr = img.astype(_session.floatx)
    if not arr.flags['C_CONTIGUOUS']:
        arr = np.ascontiguousarray(arr)
    del img
    return arr.astype(np.float32)


def array2image(arr:np.ndarray):
    """
    Args
        arr  (ndarry)  : array need to convert back to image

    Returns
        pillow image


    """
    # confirm back to numpy
    arr=np.squeeze(arr)
    arr=np.clip(arr,0,255)
    if arr.ndim not in [2, 3]:
        raise ValueError('image should be 2 or 3 dimensional. Got {} dimensions.'.format(arr.ndim))
    mode = None

    if arr.ndim == 2:
        mode = 'L'
    elif arr.ndim == 3:
        if (_backend=='tensorflow' and  arr.shape[2] in [3, 4]) or (arr.shape[2] in [3, 4] and arr.shape[0] not in [3, 4]):
            pass
        elif (_backend!='tensorflow' and  arr.shape[0] in [3, 4] and arr.shape[2] not in [3, 4]):
            arr = arr.transpose([1, 2, 0])
        elif _backend in ['pytorch', 'cntk'] and arr.ndim == 3 and arr.shape[0] in [3, 4] :#and arr.shape[2] not in [3, 4]:
            arr = arr.transpose([1, 2, 0])
        else:
            raise ValueError('3d image should be 3 or 4 channel. Got {} channel.'.format(arr.shape[0]))
        if arr.shape[2] == 3:
            mode = 'RGB'
        elif arr.shape[2] == 4:
            mode = 'RGBA'

    arr = np.clip(arr, 0, 255).astype(np.uint8)
    img = pil_image.fromarray(arr, mode)
    return img


def mask2array(img):
    """

    Args
        img  (string), pillow image or numpy.ndarray): Image to be converted to ndarray.

    Returns
        ndarray  (HW / single channel)


    """
    if isinstance(img,str):
        if os.path.exists(img) and img.split('.')[-1].lower() in ('jpg','jepg','jfif','webp','png','bmp','tiff','ico'):
            img=pil_image.open(img).convert('L')
        else:
            return None
    arr=None
    if isinstance(img,pil_image.Image):
        arr = np.array(img).astype(_session.floatx)
    elif isinstance(img, np.ndarray):
        if arr.ndim not in [2, 3]:
            raise ValueError('image should be 2 or 3 dimensional. Got {} dimensions.'.format(arr.ndim))
        if arr.ndim == 3:
            if arr.shape[-1] in [3, 4] and arr.shape[0] not in [3, 4]:
                pass
            elif arr.shape[0] in [3, 4]:
                arr = arr.transpose([1, 2, 0])
            else:
                raise ValueError('3d image should be 3 or 4 channel. Got {} channel.'.format(arr.shape[0]))
        arr=img.astype(_session.floatx)
    if arr.flags['C_CONTIGUOUS'] == False:
        arr = np.ascontiguousarray(arr)
    return arr

def array2mask(arr:np.ndarray):
    """

    Args
        arr  ndarry  : array need to convert back to image

    Returns
        pillow image


    """
    # confirm back to numpy
    arr=np.squeeze(arr)
    if arr.ndim not in [2, 3]:
        raise ValueError('image should be 2 or 3 dimensional. Got {} dimensions.'.format(arr.ndim))
    mode = None
    if arr.max()==1:
        arr=arr*255
    if arr.ndim == 2:
        #arr = np.expand_dims(arr, 2)
        mode = 'L'
    elif arr.ndim == 3:
        if arr.shape[-1] in [3, 4] and arr.shape[0] not in [3, 4]:
            pass
        elif arr.shape[0] in [3, 4]:
            arr = arr.transpose([1, 2, 0])
        else:
            raise ValueError('3d image should be 3 or 4 channel. Got {} channel.'.format(arr.shape[0]))
        if arr.shape[-1] == 3:
            mode = 'RGB'
        elif arr.shape[-1] == 4:
            mode = 'RGBA'

    arr = np.clip(arr, 0, 255).astype(np.uint8)
    img = pil_image.fromarray(arr, mode)
    return img
def preprocess_image_in_memory(image_path, max_size_mb=20):
    """
    圖像前處理函數，將圖像轉換並壓縮到符合 OpenAI Vision API 的要求，並以 Pillow Image 格式返回。

    :param image_path: 輸入的圖像路徑
    :param max_size_mb: 圖像大小限制 (MB)
    :param target_format: 目標圖像格式 ('png', 'jpeg', 'gif', 'webp')
    :return: 處理後的 Pillow Image 物件
    """
    # 打開圖像
    with pil_image.open(image_path) as img:
        img_format = img.format.lower()
        target_format='png'

        # 檢查格式是否符合要求，不符合則轉換格式
        if img_format not in ['png', 'jpeg', 'gif', 'webp']:
            print(f"圖像格式 {img_format} 不支援，將轉換為 {target_format}")
            img = img.convert('RGB')  # 有些格式需要轉換為 RGB

        # 壓縮處理
        img_bytes = io.BytesIO()
        img.save(img_bytes, format=target_format)

        file_size_mb = len(img_bytes.getvalue()) / (1024 * 1024)  # 以 MB 為單位
        if file_size_mb > max_size_mb:
            print(f"圖像大小 {file_size_mb:.2f}MB 超過 {max_size_mb}MB 限制，將進行壓縮。")
            # 壓縮圖像
            img_bytes = io.BytesIO()
            img.save(img_bytes, format=target_format, quality=85, optimize=True)

        img_bytes.seek(0)  # 重置讀寫指標，準備讀取
        img = pil_image.open(img_bytes)  # 重新讀取為 Pillow Image 格式

    return img

def encode_image(image):
    # check if the image exists
    if isinstance(image,str) and os.path.isfile(image):
        image_path=image
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")
        image = pil_image.open(image_path)
    if isinstance(image, pil_image.Image):
        buffered = BytesIO()
        image.save(buffered, format=image.format)  # 可以更改格式，如JPEG
        image_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
        return image_base64






def decode_base64(base64_str):
    """
    將 Base64 編碼字串轉換為 Pillow Image

    :param base64_str: Base64 編碼字串
    :return: Pillow Image 物件
    """
    image_data = base64.b64decode(base64_str)
    buffered = BytesIO(image_data)
    image = pil_image.open(buffered)
    return image

