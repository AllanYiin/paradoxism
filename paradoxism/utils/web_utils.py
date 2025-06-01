import builtins
import json
import logging
import random
import regex
import copy
import time
import uuid
import io
import threading
from typing import Iterable
from collections import OrderedDict
from urllib.parse import urlencode
from itertools import chain
# import markdownify
import numpy as np
import requests
from bs4 import BeautifulSoup, Tag, NavigableString
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait

from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException

from paradoxism.utils import *
from paradoxism.utils.markdown_utils import HTML2Text, htmltable2markdown
from paradoxism.utils.text_utils import seg_as_sentence, optimal_grouping
from paradoxism.utils.regex_utils import count_words,extract_json
from paradoxism.ops.convert import force_cast
from  paradoxism import context
__all__ = ["search_google", "search_bing", "user_agents", "get_html_content", "search_web"]

ignored_exceptions = (NoSuchElementException, StaleElementReferenceException,)
cxt=context._context()
import pysnooper


def prepare_chrome_options():

    chrome_options = Options()
    chrome_options.add_argument('--headless=old')
    chrome_options.add_argument('blink-settings=imagesEnabled=false')

    chrome_options.add_argument(f"--window-size=1920,1440")
    chrome_options.add_argument('--hide-scrollbars')
    chrome_options.add_argument("--enable-javascript")
    chrome_options.add_argument('--disable-logging')
    chrome_options.add_argument("--disable-browser-side-navigation")
    chrome_options.add_argument("--disable-web-security")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-setuid-sandbox")
    chrome_options.add_argument("--disable-software-rasterizer")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument("--proxy-server='direct://'")
    chrome_options.add_argument("--proxy-bypass-list=*")
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument("--allow-insecure-localhost")
    chrome_options.add_argument("--password-store=basic")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--enable-automation")
    chrome_options.add_argument('--allow-running-insecure-content')

    return chrome_options

user_agents = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.2151.97',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.2151.97',
    'Mozilla/5.0 (Linux; Android 10; HD1913) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.6045.193 Mobile Safari/537.36 EdgA/119.0.2151.78',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:88.0) Gecko/20100101 Firefox/88.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Version/14.1.2 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Version/14.1 Safari/537.36',
    'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:88.0) Gecko/20100101 Firefox/88.0'
]


def detect_table_like_structure(tag):
    if tag.name in ['table']:
        return True
    if tag.name not in ['div', 'section']:
        return False
    # div_children = tag.find_all(['div', 'section'], recursive=False)
    # if not div_children:
    #     return False
    for div_child in tag.contents:
        if div_child.name in ['ul', 'ol'] and  len(div_child.find_all('li')) > 1:
            return True
    return False


def table_like_to_table(table_soup, table_like_tag, title=''):
    if table_like_tag.name == 'table':
        return table_like_tag
    # 建立 table 標籤
    table_tag = table_soup.new_tag('table')
    caption_tag = table_soup.new_tag('caption') if table_like_tag.find('h2') else title
    table_tag.append(caption_tag)
    # 找到所有的行（假設每個 <div> 標籤代表一行）
    for div in table_like_tag.find_all('ul', recursive=True):
        # 創建一個 table row
        tr_tag = table_soup.new_tag('tr')

        # 處理每一列（假設 <div> 或 <li> 標籤內的內容代表一列）
        for cell in div.find_all('li', recursive=True):
            td_tag = table_soup.new_tag('td')
            td_tag.string = cell.get_text()
            tr_tag.append(td_tag)
        table_tag.append(tr_tag)

        # 將 table 標籤添加到 BeautifulSoup 對象
    return table_tag


def get_html_content(url: str) -> str:
    """
    Fetches the HTML content of a given URL using a headless Chrome browser.

    Args:
        url (str): The URL of the webpage to fetch.

    Returns:
        str: The filtered HTML content of the webpage.

    Example:
        >>> html_content = get_html_content('https://chatgpt.com/search?q=deepseek')
    """
    chrome_options = prepare_chrome_options()
    chrome_options.add_argument('user-agent=%s' % random.choice(user_agents))
    window_size=None
    html=None
    with webdriver.Chrome(options=chrome_options) as driver:
        driver.get(url)
        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR,'body'))
        )

        # 獲取頁面尺寸
        window_size = driver.get_window_size()
        # 先打上 data-uuid
        script_uuid = """
           var allNodes = document.querySelectorAll('body *, main *');
           for(var i=0; i<allNodes.length; i++){
              var node = allNodes[i];
              try {
              // 產生隨機 UUID
              if (!node.hasAttributes()) {
                node.setAttribute('attrs', '{}');
              } 
              node.setAttribute('data-uuid', '%s' + i);
           
              } catch (e) {
                  console.error('Error setting data-uuid for node:', node, e);
              }
           }

           """ % str(uuid.uuid4())  # 在這裡會是一樣的 prefix + 遞增 i
        driver.execute_script(script_uuid)

        # 取得 bounding box + data-uuid
        script_bbox = """
           var result = [];
           var allNodes = document.querySelectorAll('body *, main *');
           for (var i = 0; i < allNodes.length; i++) {
               var node = allNodes[i];
            try {
               var rect = node.getBoundingClientRect();
               result.push({
                   "dataUuid": node.getAttribute('data-uuid'),
                   "tagName": node.tagName,
                   "x": rect.x,
                   "y": rect.y,
                   "width": rect.width,
                   "height": rect.height
               });
            } catch (e) {
                console.error('Error getting bounding box for node:', node, e);
            }
           }
           return result;
           """
        bounding_info = driver.execute_script(script_bbox)

        # 拿到最終 HTML
        html = driver.page_source
    bounding_dict={item['dataUuid']:item for item in bounding_info}
    soup = BeautifulSoup(html, "html.parser")

    # 過濾: 若 "元素中心" 在邊緣 => 將來要刪除
    window_width,window_height=window_size['width'],window_size['height']
    left_margin = window_width * 0.1
    right_margin = window_width * 0.9
    top_margin = window_height * 0.1
    bottom_margin = window_height * 0.9

    to_remove_uuids = []
    for item in bounding_info:
        if item['dataUuid']:
            if  item['width']==0 or item['height'] ==0 or float( item['width'])*float(item['height'])<50:
                to_remove_uuids.append(item['dataUuid'])
            else:
                cx = item['x'] + builtins.min(item['width'],window_width) / 2
                cy = item['y'] + builtins.min(item['height'],window_height)/ 2
                in_core = (left_margin <= cx <= right_margin) and (top_margin <= cy <= bottom_margin)
                if not in_core:
                    to_remove_uuids.append(item['dataUuid'])
        else:
            logging.debug(item)

    # 6.1 移除「沒有任何文字或連結」的標籤
    def has_meaningful_text_or_link(tag: Tag) -> bool:
        # 有任何 a 元素即算有意義
        if tag.find('a'):
            return True
        # 或者自身文字不只空白
        text_content = tag.get_text(strip=True)
        return len(text_content) > 0

    # 6.2 展開只有一個子元素且自身沒文字的標籤
    def unwrap_single_child_tags(soup: BeautifulSoup) -> None:
        changed = True
        while changed:
            changed = False
            for tag in soup.find_all():
                children = list(tag.children)
                # 只計算真正的 tag，排除 NavigableString、Comment 等
                child_tags = [c for c in children if c.name]

                # 若只有一個子 tag，且父本身沒文字，就 unwrap
                # 注意：tag.get_text(strip=True) 會計算子孫的文字
                # 所以得先判斷自己（不含子孫）是否有文字
                # 這裡簡化做法：若 strip 後沒有文字，就當作自己沒文字
                own_text = ''.join(
                    c for c in tag.contents
                    if c.name is None  # c 為字串而非 tag
                ).strip()

                if len(child_tags) == 1 and not own_text:
                    tag.unwrap()
                    changed = True

    # 6.3 替換 <span>, <p>, <br> 為適當文字/換行
    def replace_inline_tags(soup: BeautifulSoup) -> None:
        for br in soup.find_all("br"):
            br.replace_with("\n")
        for span in soup.find_all("span"):
            # 取出原本的文字，再加一個空白
            span.replace_with(f"{span.get_text()} ")
        for p in soup.find_all("p"):
            p.replace_with(f"{p.get_text()}\n")

    # 6.4 將 <h1> ~ <h6>, <strong>, <b>, <em>, <i> 轉為對應的 Markdown
    def convert_to_markdown(soup: BeautifulSoup) -> None:
        header = soup.find("head")
        if header:
            title = header.find("title")
            if title:
                title_text = title.get_text(strip=True)
                title.replace_with(f"# {title_text}\n")
            header_text = header.get_text(strip=True)
            header.replace_with(f"{header_text}\n\n---\n")
        for strong in soup.find_all("strong"):
            text_content = strong.get_text(strip=True)
            strong.replace_with(f"**{text_content}**")
        # h1 ~ h6
        for i in range(1, 7):
            for hx in soup.find_all(f"h{i}"):
                markdown_heading = "#" * i
                text_content = hx.get_text(strip=True)
                hx.replace_with(f"{markdown_heading} {text_content}\n")

        # strong, b -> **...**

        for b_tag in soup.find_all("b"):
            text_content = b_tag.get_text(strip=True)
            b_tag.replace_with(f"**{text_content}**")

        # em, i -> *...*
        for em_tag in soup.find_all("em"):
            text_content = em_tag.get_text(strip=True)
            em_tag.replace_with(f"*{text_content}*")
        for i_tag in soup.find_all("i"):
            text_content = i_tag.get_text(strip=True)
            i_tag.replace_with(f"*{text_content}*")

        # ul, ol, li -> unordered and ordered lists
        for ul in soup.find_all("ul"):
            items = [f"- {li.get_text(strip=True)}" for li in ul.find_all("li")]
            ul.replace_with("\n".join(items))
        for ol in soup.find_all("ol"):
            items = [f"{idx+1}. {li.get_text(strip=True)}" for idx, li in enumerate(ol.find_all("li"))]
            ol.replace_with("\n".join(items))

        # Convert header to markdown


    # 6.5 （示例）移除「疑似選單」的表格 (或 div)
    #    假設判斷規則：若裡面全是 a，且文字很短 → 選單
    #    這裡僅作示範，可自行擴充
    def is_menu_table(tag: Tag) -> bool:
        # 檢查所有子孫 a
        # 抽取表格所有單元格
        cells = [cell.get_text(strip=True) for cell in tag.find_all("td")]
        if len(cells)==0:
            return True
        # 檢查字符長度分佈
        average_length = sum(count_words(cell) for cell in cells) / len(cells)

        # 檢測含數字的單元格比例
        numeric_cells = [cell for cell in cells if regex.search(r'\d', cell)]
        numeric_ratio = len(numeric_cells) / len(cells)
        if average_length < 8 and numeric_ratio < 0.1:
            return True
        if average_length>15 and numeric_ratio>0.8:
            return False
        # 提取行數與列數
        rows = tag.find_all("tr")
        row_lengths = [len(row.find_all("td")) for row in rows]

        # 判斷是否規律
        is_regular = all(abs(length-row_lengths[0])<=1 for length in row_lengths)
        if  len(row_lengths) >=3 :
            _std=np.array(row_lengths).std()
            if (not is_regular and np.array(row_lengths).std()>3):
                return True
        links = tag.find_all("a")
        if links and len(links) > 3:
            text_total_len = sum(len(a.get_text(strip=True)) for a in links)
            if text_total_len < 50:
                return True
        # 若是表格只有單筆 tr 則為 menu
        rows=tag.find_all("tr")
        if tag.name == "table" and len(tag.find_all("tr")) == 1:
            return True
        return False

    #print(soup.get_text(),flush=True)
    for t in soup.find_all():
        if len(t.get_text().strip())>100 :
            if t.name not in ["script", "style",'copyright']:
                continue
        if t.name in ["script", "style", "nav",  'copyright', 'footer','breadcrumb', 'crumb', 'menu', 'accordion', 'modal','loading', 'shopping_cart','svg','path','iframe','button', 'input', 'select', 'option', 'dd', 'dt', 'dl', 'abbr']:
            t.replace_with('')
            #t.decompose()
            continue
        if t and t.attrs:
            if t.attrs.get('data-uuid') in to_remove_uuids:
                t.replace_with('')
                #t.decompose()
            elif not has_meaningful_text_or_link(t):
                t.replace_with('')
                #t.decompose()

    # 處理類似表格的結構
    table_likes = soup.find_all(detect_table_like_structure)
    for i in range(len(table_likes)):
        tl=table_likes[::-1][i]
        if tl.name!="table":
            newtb=able_like_to_table(soup, tl)
            cells = [cell.get_text(strip=True) for cell in newtb.find_all("td")]
            if len(cells)==0:
                continue
            average_length = sum(count_words(cell) for cell in cells) / len(cells)
            rows = newtb.find_all("tr")
            row_lengths = [len(row.find_all("td")) for row in rows]
            if is_menu_table(newtb):
                #print('判斷為選單',newtb,flush=True)
                tl.decompose()
                continue
            if average_length>15 or len(rows)<=2 or np.array(row_lengths).std()>3:
                continue
            else:
                tablemd=htmltable2markdown(newtb.prettify(formatter=None))
        else:
            tablemd=htmltable2markdown(tl.prettify(formatter=None))
        if not isinstance(tablemd, str) and isinstance(tablemd, Iterable):
            tablemd=tablemd[0]
        tl.replace_with(tablemd)
    links = soup.find_all("a", href=True)
    for link in links:
        link_href = link['href']
        link_text = link.get_text(strip=True)
        # 綜合判斷
        if (
                link_href.startswith("http") and  # 有效 URL
                not link_href.startswith("#") and
                not link_href.startswith("javascript") and
                link_text.lower() not in {"home", "next", "previous", "more"} and
                "nav" not in link.get("class", [])  # 避免導航類別
        ):
            link.replace_with(f"\n[{link_text}]({link_href})\n")
        else:
            link.replace_with('')

    #print(soup.get_text(),flush=True)
    unwrap_single_child_tags(soup)
    #print(soup.get_text(),flush=True)
    replace_inline_tags(soup)
    #print(soup.get_text(),flush=True)
    convert_to_markdown(soup)

    cleaned_text = ("\n".join(soup.stripped_strings)).replace("\u00A0", " ").replace("\u200E", "")
    #print(cleaned_text,flush=True)
    return cleaned_text



def search_bing(query: str) -> list:
    """
    使用 Bing 搜索引擎根據指定查詢字串搜索信息。

    Args:
        query (str): 要搜索的查詢字串。

    Returns:
        list: 包含搜索結果的清單。每個結果是一個字典，包含 'title'（標題）, 'link'（鏈接）和 'snippet'（摘要）。

    Examples:
        >>> search_bing("site:github.com openai")
        []

        >>> search_bing("提示工程+prompt engineering")
        [{'title': '...', 'link': '...', 'snippet': '...'}, ...]

    注意:
        - 此函數使用 requests 和 BeautifulSoup 模塊來解析 Bing 的搜索結果頁面。
        - 函數捕獲網頁內容，然後從 HTML 中提取相關的標題、鏈接和摘要信息。
        - 如果搜索無結果或發生連接錯誤，將返回空清單。
    """
    query = urlencode({"q": query.replace(' ', '+')}).replace('%2B', '+')

    headers = {
        'User-Agent': random.choice(user_agents)}

    end_of_search = 'No results found for <strong>' + query + '</strong>'
    url_list = []
    search_results = []
    if_limit = True
    sw_next = True
    response = ''
    next = 1
    limit = (3 - 1) * 10 + 1
    # &qs=n&form=QBRE&sp=-1&p{query}&first={str(next)}
    session = requests.Session()
    session.headers.update(headers)
    search_url = f"https://www.bing.com/search?{query}"
    return get_html_content(search_url)


def search_google(query: str, language=None) -> list:
    """
    使用 Google 搜索引擎根據指定查詢字串搜索信息。

    Args:
        query (str): 要搜索的查詢字串。

    Returns:
        list: 包含搜索結果的清單。每個結果是一個字典，包含 'title'（標題）, 'link'（鏈接）和 'snippet'（摘要）。

    Examples:
        >>> search_google("https://www.google.com/search?q=%E8%8F%B1%E6%A0%BC%E7%B4%8B")
        []
        >>> search_google("提示工程+prompt engineering")
        [{'title': '...', 'link': '...', 'snippet': '...'}, ...]



    注意:
        - 此函數使用 requests 和 BeautifulSoup 模塊來解析 Google 的搜索結果頁面。
        - 函數捕獲網頁內容，然後從 HTML 中提取相關的標題、鏈接和摘要信息。
        - 如果搜索無結果或發生連接錯誤，將返回空清單。
    """
    base_url = "https://www.google.com"
    if language :
        if language[:-2:].lower() in ['tw','cn' ,'jp', 'kr', 'vn','th','ph','id','my','sg']:
            language = language[:-2:].lower()
        base_url = f"https://www.google.com.{language}"

    if base_url in query:
        url_parts = query.strip().split('q=')
        search_url = url_parts[0] + 'q=' + url_parts[-1].strip().replace(' ', '%2B').replace('+', '%2B').replace(':',
                                                                                                                 '%3A')
    else:
        query = urlencode({"q": query.strip().replace(' ', '+')}).replace('%2B', '+')
        search_url = f"{base_url}/search?{query}"

    results= get_html_content(search_url)
    return results


@pysnooper.snoop()
def search_web(url: str) -> list:
    return get_html_content(url)


