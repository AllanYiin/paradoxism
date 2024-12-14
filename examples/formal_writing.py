import time
import inspect
import ast
import textwrap
import traceback
import inspect
import linecache
from paradoxism.utils.utils import *
from paradoxism.ops.convert import *
from paradoxism.base.agent import agent
from paradoxism.ops.base import prompt
from paradoxism.context import *



@agent('gpt-4o','你是一個行事嚴謹，字斟句酌的公務員。你熟悉公文撰寫的知識以及格式，你也懂得相關應對進退的道理，在文字中展現出你圓融的處世態度')
def formal_writer(intent:str)->str:
    """
    撰寫公文時，請遵守以下原則，以避免錯誤:
    - 正確使用稱謂語(鈞長)、期望語(請核示、核閱、鑒核、鑒察)、結束語(敬陳)及簽署(單位名稱、姓名及日期)
    - 公文寫「本年」不寫「今年」；寫「日」不寫「天」；寫「時」不寫「點」，並以12小時制計算
    - 正確使用按語(起首語)，如按、有關、關於、查、依、為；轉接詞(承上啟下)，如經查、案查、茲以、茲據、爰、另、至於
    - 機關首長以「公文」、「便條」、「口頭」、「會議」時所做的指示，其用語應分別為「批示」、「指示」、「諭示」、「裁示」
    - 簽呈改為「簽陳」
    - 不要使用「業已」，因為「業」即已經之意，應改為「業於」或「已於」
    - 若涉及數字請參考知識庫中的「公文書橫式書寫數字使用原則」
    - 注意法律用語列如:「設」機關、「置」人員、「處」有期徒刑、「科」罰金、「處」罰鍰、「制定」法律、「訂定」行政規則
    - 可採用表格敘述或作比較表或以附件附陳
    - 簽文需提建議意見，亦可撰擬兩個以上建議，供長官採擇。另如他
    機關轉來之會議紀錄等，簽陳時應就需配合事項及預定辦理進度一
    併簽陳，不宜僅簽「如奉核可，擬予存查」
    - 「此致」、「此上」、「謹陳」、「敬陳」…之類用語，應另起一
    行低兩格書寫。
    Args:
        intent:(str) 事由

    Returns:

    """
    result=prompt('當使用者輸入一篇文字，你就會從知識庫中搜索最接近的公文型態，在盡量原意不變的情況下，改寫成為公文的形式，但不要提及參考資料來源為何'+f'\n"""\n{intent}\n"""\n')
    return result




print(formal_writer('請長官核准明年去WIPO參訪'))