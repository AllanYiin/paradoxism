from paradoxism.base.agent import agent
from paradoxism.base.flow import *
from paradoxism.base.tool import *
from paradoxism.ops.base import prompt
from paradoxism.tools.image_tools import *
from paradoxism.tools.web_tools import *

@tool()
def query_yahoo_news(stock_id, stock_name)->dict:
    """
    Args:
        stock_id: 格式為4碼數字+'.TW'
        stock_name: stock_id此股票編號對應之公司名稱

    Returns:
        新聞清單
    '''
    json
    '''
    """
    s = open_url(f'https://tw.stock.yahoo.com/quote/{stock_id}/news')
    print(s,'/n/n')
    news = prompt(f'請基於以下文字中抽取出與指定公司{stock_id}{stock_name}相關之新聞資訊(包括標題、發布單位(發布媒體)、發布日期(請將相對日期根據轉換為絕對日期)、摘要、新聞連結url)，請以新聞標題找尋正確的新聞連結url(副檔名為*.html)，請務必確保內容真實精確，以markdown格式(換行符號請以空兩格再接著\n)輸出'+f'"""{s}"""')
    return news


def collect_news():
    results={}
    stocks={"2301.TW":"光寶科","2308.TW":"台達電"}
    for k,v in  stocks.items():
        print(f'{v}({k})')
        results[k]=query_yahoo_news({"stock_id":k,"stock_name":v})
        print(results[k], '/n/n')
    return results

collect_news()