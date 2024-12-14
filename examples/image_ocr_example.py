import time
from paradoxism.utils.utils import *
from paradoxism.base.agent import agent
from paradoxism.ops.base import prompt
from paradoxism.tools.image_tools import *

imgs=['C:/Users/Allan/OneDrive/Documents/paradoxism/examples/vckeditor-61835a703d2c3.png','C:/Users/Allan/OneDrive/Documents/paradoxism/examples/assets/pleague-3pt.png']
for img in imgs:
    caption=im2text({'prompt':'請讀取圖片，並且仔細檢視刻度後，將圖片中的數據點抄錄出來，請盡量確保數據精確性，提供給我之前務必檢查正確性','img_path':img})
    print(caption)