import builtins
import json
import logging
import random
import re
import copy
import time
import uuid
import io
import threading
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
from paradoxism.utils.regex_utils import count_words
from  paradoxism import context
__all__ = ["search_google", "search_bing", "user_agents", "md4html", "strip_tags", "retrieve_clear_html","get_html_content", "search_web"]

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



# import chromedriver_binary
# from selenium import webdriver
# from selenium.webdriver.chrome.options import Options

"""
https://stackoverflow.com/questions/45034227/html-to-markdown-with-html2text
https://beautiful-soup-4.readthedocs.io/en/latest/#multi-valued-attributes
https://beautiful-soup-4.readthedocs.io/en/latest/#contents-and-children
"""


# class CustomMarkdownConverter(markdownify.MarkdownConverter):
#     def convert_a(self, el, text, convert_as_inline):
#         classList = el.get("class")
#         if classList and "searched_found" in classList:
#             # custom transformation
#             # unwrap child nodes of <a class="searched_found">
#             text = ""
#             for child in el.children:
#                 text += super().process_tag(child, convert_as_inline)
#             return text
#         # default transformation
#         return super().convert_a(el, text, convert_as_inline)


# Create shorthand method for conversion
def md4html(html, **options):
    return CustomMarkdownConverter(**options).convert(html)


def check_useful_html_tag(tag):
    tag_list = ['header', 'copyright', 'footer', 'telephone', 'breadcrumb', 'crumb', 'menu', 'accordion', 'modal',
                'loading', 'shopping_cart']
    if 'class' in tag.attrs:
        _class = ''.join(tag.attrs['class']).lower()
        for t in tag_list:
            if t in _class:
                return False
    if 'id' in tag.attrs:
        _id = tag.attrs['id'].lower()
        for t in tag_list:
            if t in _id:
                return False
    return True


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

    response = session.get(search_url, headers=headers, verify=False)
    time.sleep(0.5)
    soup = BeautifulSoup(response.text, 'html.parser')
    total_words = len(soup.text)

    def h2_with_a(tag):
        return tag.name == 'h2' and tag.find_all('a')

    results = soup.find_all(h2_with_a)
    titles = [t.text for t in results]
    hrefs = [t.find_all('a')[0]['href'] for t in results]

    # results = soup.find_all('span', class_='c_tlbxTrg')
    contentinfos = soup.find_all('div', class_='b_caption')
    snippet_texts = []
    for (t, h, c) in zip(titles, hrefs, contentinfos):
        try:
            txt = c.contents[0].contents[0].text
            snippet_text = c.contents[0].text[len(txt):]
            href = h
            title = t
            search_results.append({'title': title, 'link': href, 'snippet': snippet_text})
        except Exception as e:
            print('Connection Error')
            print(e)
            PrintException()
    # if len(search_results) >= 5:
    #     search_results = search_results[:5]

    return search_results, session


def search_google(query: str) -> list:
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
    if 'https://www.google.com/search' in query:
        url_parts = query.strip().split('q=')
        search_url = url_parts[0] + 'q=' + url_parts[-1].strip().replace(' ', '%2B').replace('+', '%2B').replace(':',
                                                                                                                 '%3A')
    else:
        query = urlencode({"q": query.strip().replace(' ', '+')}).replace('%2B', '+')
        search_url = f"https://www.google.com/search?{query}"

    headers = {
        'User-Agent': random.choice(user_agents)}

    session = requests.Session()
    response = session.get(search_url, headers=headers, verify=False)
    if response and response.status_code ==429:
        print(429,'請求量過多!')
        raise Exception('429請求量過多!')
    soup = BeautifulSoup(response.content, 'html.parser')
    search_results = {}
    total_words = len(soup.text)

    def no_div_children(tag):
        return tag.name == 'div' and 0.2 > float(len(tag.text)) / total_words > 0.02 and (
                tag.find_all('h3') or tag.find_all('div', {"ariel_level": "3"})) and tag.find_all('a', href=True)

    def div_with_media(tag):
        return tag.name == 'div' and (
                (len([t for t in tag.contents if
                      t.name == 'img' and 'alt' in t.attrs and count_words(t.attrs['alt']) >= 8]) > 0)
                or (len([t for t in tag.contents if t.name == 'a' and count_words(t.get('aria-label')) >= 10]) > 0
                    and len([t for t in tag.find_all('svg')]) > 0))

    results = soup.find_all(no_div_children)
    media_results = soup.find_all(div_with_media)
    media_references = []
    for tag in media_results:
        vedio_url = [t.attrs['data-url'] for t in tag.find_all('div') if
                     'dara-url' in t.attrs and len(t.attrs['data-url']) > 0]
        if len(vedio_url) > 0:
            cxt.citations.append(
                '<video width="148" height="83" controls><source src="{0}" type="video/mp4"></video>'.format(
                    vedio_url[0]))
    if len(cxt.citations) > 0:
        print('citations', cyan_color('\n' + '\n'.join(cxt.citations)))
    for r in results:
        part = BeautifulSoup(str(r), 'html.parser')
        links = part.find_all('a', href=True)
        if len(links) > 0:
            link = links[0]['href']
            title = part.find_all('h3')[0].text
            if part.span:
                snippet_text0 = part.span.text
                part.span.extract()
            snippet_text = part.get_text(strip=True).replace(snippet_text0, '')
            if link not in search_results:
                search_results[link] = {'title': title, 'url': link, 'summary': snippet_text}
            else:
                if len(snippet_text) > len(search_results[link]['summary']):
                    search_results[link] = {'title': title, 'url': link, 'summary': snippet_text}
            # search_results.append({'title': title, 'url': link, 'summary': snippet_text})

    # links = soup.find_all('div', class_='egMi0 kCrYT')
    #
    # links = [
    #     [k.split('=')[-1] for k in t2.contents[0].attrs['href'].split('?')[-1].split('&') if k.startswith('url')][0] for
    #     t2 in links]
    # titles = [t.text for t in soup.find_all('div', class_='BNeawe vvjwJb AP7Wnd UwRFLe')]
    # snippet_texts = [t.text for t in soup.find_all('div', class_='BNeawe s3v9rd AP7Wnd')]
    # for i in range(len(links)):
    #     title = titles[i]
    #     href = links[i]
    #     snippet_text = snippet_texts[i]
    #     search_results.append({'title': title, 'link': href, 'snippet': snippet_text})
    search_results = list(search_results.values())
    # if len(search_results) >= 5:
    #     search_results = search_results[:5]
    print('google search results:', green_color(str(search_results)), flush=True)
    return search_results, session


def detect_table_like_structure(tag):
    if tag.name not in ['div', 'section']:
        return False
    div_children = tag.find_all(['div', 'section'], recursive=False)
    if not div_children:
        return False
    for div in div_children:
        ul_children = [ul for ul in div.find_all('ul', recursive=True) if len(ul.find_all('li')) > 1]
        if not ul_children:
            return False

    return True


def table_like_to_table(table_soup, table_like_tag, title):
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


def simplify_structure(tag):
    if tag.name not in ['a', 'img']:
        if tag and tag.children and len(list(tag.children))==0 :
            tag.decompose()
        for child in list(tag.children):
            if not isinstance(child, NavigableString):
                simplify_structure(child)
                if not child.contents:
                    child.decompose()
                # 檢查子元素數量，若為1則用子元素替代當前標籤
                elif len(list(child.children)) == 1 and not isinstance(child.contents[0], NavigableString):
                    child.replace_with(child.contents[0])
    return tag


def strip_tags(html):
    """
    移除沒有實質內容或者是選單功能列的 HTML 標籤，並且將除了id以及class以外的attribute都剝除
    tag_list是比對一些選單或無實質內容的物件常用命名
    並將 span 標籤的內容提取出來，並用適當的分隔符號包裹（例如逗號）。
    透過simplify_structure把只有一個子層成員的物件以子層成員替代
    偵測有無div-ul-li的表格，將它轉成<table>
    Args:
        html:

    Returns:

    """
    tag_list = ['header', 'copyright', 'footer', 'telephone', 'breadcrumb', 'crumb', 'menu', 'accordion', 'modal',
                'loading', 'shopping_cart']

    soup = BeautifulSoup(html, 'html.parser')
    # 移除所有標籤的屬性
    for tag in soup.find_all(True):
        if tag.name in ['style', 'script', 'nav', 'button', 'input', 'select', 'option', 'dd', 'dt', 'dl', 'abbr',
                        'svg', 'menu','svg','path']:
            tag.decompose()
        else:
            if tag.name == 'a':
                attr = {}
                if "href" in tag:
                    attr['href'] = tag['href']
                if "href" in tag.attrs:
                    attr['href'] =tag.attrs['href']
                tag.attrs=attr
                if len(attr['href'] )>320:
                    tag.decompose()
                # if (tag.attrs and "href" in tag.attrs and len( tag.attrs['href'])>320) or ( "href" in tag and len( tag['href'])>320):
                #     tag.decompose()
                # else:
                #     continue
                # href = ""
                # _class = ""
                # _id = ""
                # if "href" in tag:
                #     href = tag['href']
                # if tag.attrs:
                #     if "class" in tag.attrs:
                #         _class = tag.attrs['class']
                #     if "id" in tag.attrs:
                #         _id = tag.attrs['id']
                # tag.attr = {}
                # tag['href'] = href
                # tag.attr['class'] = _class
                # tag.attr['id'] = _id

                # if tag.attrs and "class" in tag.attrs and len(tag.attrs["class"]) > 64:
                #     tag.decompose()

            elif tag.name == 'img':
                src = ""
                alt = ""
                if "src" in tag:
                    src = tag['src']
                if "alt" in tag:
                    alt = tag['alt']
                tag.attr = {}
                tag['src'] = src
                tag['alt'] = src
            elif tag.name  in ['h1','h2','h3','h4','h5','h6']:
                tagtext=tag.get_text()
                tag.attrs={}
                tag.attrs['text']=tagtext
                if tag.attrs and "id" in tag.attrs:
                    if len([t for t in tag_list if t.lower() in tag.attrs["id"].lower()]) > 0:
                        tag.decompose()
                if tag.attrs and "class" in tag.attrs:
                    if len([t for t in tag_list if t.lower() in ' '.join(tag.attrs["class"]).lower()]) > 0:
                        tag.decompose()

            if tag.attrs and tag.name not in [ 'a']:
                atts = copy.deepcopy(tag.attrs)
                tag.attrs = {k: v for k, v in atts.items() if k in ['id', 'class', 'src', 'alt'] and len(atts[k]) < 64}
                if atts and "id" in atts:
                    if len([t for t in tag_list if t.lower() in atts["id"].lower()]) > 0:
                        tag.decompose()
                    else:
                        if atts and "class" in atts:
                            if len([t for t in tag_list if t.lower() in ' '.join(atts["class"]).lower()]) > 0:
                                tag.decompose()


    # 將 span 標籤的內容提取出來，並用適當的分隔符號包裹（例如逗號）
    for span in soup.find_all('span'):
        span.replace_with(span.get_text())

    for _p in soup.find_all('p'):
        _p.replace_with('\n' + _p.get_text() + '\n')
    soup = simplify_structure(soup)
    title = ''
    if soup.find('title'):
        title = soup.find('title').text.strip()
    table_likes = soup.find_all(detect_table_like_structure)

    for tl in table_likes:
        tl.replaceWith(table_like_to_table(soup, tl, title))
    return soup


def retrieve_clear_html(url):
    """

      Args:
          url:


      Returns:

      Examples:
          >>> clear_html=retrieve_clear_html('https://pubmed.ncbi.nlm.nih.gov/?term=Interstitial+Cystitis+and+Painful+Bladder+Syndrome&sort=pubdate&page=1')

    """
    local = threading.local()
    lock = threading.Lock()
    if url.startswith('http://') or url.startswith('https://'):
        chrome_options = prepare_chrome_options()
        chrome_options.add_argument('user-agent=%s' % random.choice(user_agents))

        # session = requests.Session()
        # session.headers.update(headers)
        # response = session.get(url, headers=headers, allow_redirects=True)
        # 建立Chrome瀏覽器物件
        resulttext = ''
        title = ''
        banners = []
        contents = []

        lock.acquire()
        if not hasattr(local, 'driver'):
            local.driver = webdriver.Chrome(options=chrome_options)
        html = ''
        try:

            local.driver.get(url)

            local.driver.implicitly_wait(4)

            body_rect = copy.deepcopy(local.driver.find_element(By.TAG_NAME, 'body').rect)
            windows_rect = local.driver.get_window_rect()
            window_width = body_rect['width']
            window_height = body_rect['height']
            head_html = local.driver.find_element(By.TAG_NAME, 'head').get_attribute('outerHTML')
            body_html = local.driver.find_element(By.TAG_NAME, 'body').get_attribute('outerHTML')
            local.driver.refresh()
            for d in local.driver.find_elements(By.TAG_NAME, 'div'):
                try:
                    drect = copy.deepcopy(d.rect)
                    drect['outerHTML'] = d.get_attribute('outerHTML').strip()
                    drect['text'] = d.get_attribute("textContent").strip()
                    if not d.is_displayed():
                        pass
                    elif drect['height'] is None or drect['width'] is None or drect['height'] == 0 or drect[
                        'width'] == 0:
                        pass
                    elif drect['height'] * drect['width'] < 100:
                        pass
                    elif window_height > 0 and drect['height'] / float(window_height) > 0.6 and drect['width'] / float(
                            window_width) > 0.6 and not (drect['x'] == 0 and drect['y'] == 0):
                        if len(drect['text']) > 10:
                            if len(contents) == 0 or drect['outerHTML'] not in contents[-1]['outerHTML']:
                                if len(contents) > 0 and drect['text'] in contents[-1]['text'] and len(
                                        drect['text']) > 50 and len(contents[-1]['text']) > 50:
                                    pass
                                else:
                                    contents.append(drect)
                    elif drect['height'] / drect['width'] > 5 and drect['height'] > 0.5 * window_height and (
                            drect['x'] < window_height / 4 or drect['x'] > 3 * window_height / 4):
                        if len(banners) == 0 or drect['outerHTML'] not in banners[-1]['outerHTML']:
                            banners.append(drect)
                    elif drect['height'] > 0 and window_width > 0 and (drect['width'] / drect['height']) / (
                            window_width / window_height) > 5 and drect[
                        'width'] > 0.5 * window_width and (
                            drect['y'] < windows_rect['height'] / 4 or drect['y'] > 3 * window_height / 4):
                        if len(banners) == 0 or drect['outerHTML'] not in banners[-1]['outerHTML']:
                            banners.append(drect)
                    elif drect['height'] and 0.5 < drect['width'] / drect['height'] < 2 and drect[
                        'width'] > 0.5 * window_width and \
                            drect['height'] > 0.5 * window_height and (drect['y'] < window_height / 3):
                        if count_words(drect['text']) > 10:
                            if len(contents) == 0 or drect['outerHTML'] not in contents[-1]['outerHTML']:
                                if len(contents) > 0 and drect['text'] in contents[-1]['text'] and count_words(
                                        drect['text']) > 50 and count_words(contents[-1]['text']) > 50:
                                    pass
                                else:
                                    contents.append(drect)
                    else:
                        pass
                except NoSuchElementException:
                    pass
                except StaleElementReferenceException:
                    pass
                except Exception as e:
                    print(d, flush=True)
                    PrintException()

            final_content = []

            def get_banner_overlap_areas(c):
                areas = 0
                c_html = c['outerHTML']
                for b in banners:
                    b_html = b['outerHTML']
                    if b_html in c_html:
                        areas += int(b['width']) * int(b['height'])
                return areas

            if len(contents) > 0:
                areas = [get_banner_overlap_areas(c) for c in contents]
                min_area = np.array(areas).min()
                final_content = [contents[cidx] for cidx in range(len(contents)) if areas[cidx] == min_area]
            if len(final_content) > 0:
                content_html = '<html>' + head_html + '<body>' + ''.join(
                    [c['outerHTML'] for c in final_content]) + '</body></html>'
                html = content_html
            else:
                content_html = '<html>' + head_html + body_html + '</html>'
                html = content_html
        except Exception as e:
            PrintException()
            print(e)
            html = local.driver.page_source
        lock.release()
        local.driver.quit()

        if html:
            try:
                # tables = htmltable2markdown(html)
                html = html.replace(u'\xa0', u' ')
                for banner in banners:
                    html = html.replace(banner['outerHTML'], '')
            except:
                PrintException()
            soup = strip_tags(html)

            for tag_ul in soup.find_all('ul'):
                if (tag_ul.text is None) or (len(tag_ul.text)<len(soup.text)*0.2):
                    tag_ul.decompose()

            return soup.prettify(formatter=None)
        else:
            return None
    else:
        return None


def optimize_html(html):
    tag_list = ['header', 'copyright', 'footer', 'telephone', 'breadcrumb', 'crumb', 'menu', 'accordion', 'modal',
                'loading', 'shopping_cart']
    remove_tags = ['style', 'script', 'noscript']

    soup = BeautifulSoup(html, 'html.parser')
    title = ''
    if soup.find('title'):
        title = soup.find('title').text.strip()
        soup.name=title
    # 1. 刪除所有封閉且無內容的標籤
    for tag in soup.find_all(True, recursive=True):  # True 表示找到所有標籤
        if not tag.contents:  # 檢查標籤是否為空
            tag.decompose()
    # 2. 刪除指定的標籤，一次性處理
    tags_to_remove = ['style', 'script', 'nav', 'button', 'input', 'select', 'option', 'dd', 'dt', 'dl', 'abbr', 'svg',
                      'menu', 'path', 'iframe', 'img','form']
    for match in soup.find_all(tags_to_remove, recursive=True):
        match.decompose()  # 完全刪除指定的標籤

    # 3. 將僅作為容器的特定標籤用其子標籤替代
    container_tags = ['div', 'li', 'ul', 'ol', 'section', 'article', 'header', 'footer', 'aside', 'span']

    for tag in soup.find_all(container_tags, recursive=True):
        # 若該標籤的 get_text 與所有子標籤的 get_text 加總相同，則替換為子標籤
        if tag.get_text(strip=True) == '\n'.join(child.get_text(strip=True) for child in tag.find_all(recursive=False)):
            tag.unwrap()

    # 4. 替換 <span> 標籤為純文字
    for span in soup.find_all('span'):
        span.replace_with(span.get_text())

    # 5. 替換 <p> 標籤，並在文字前後加換行符號
    for _p in soup.find_all('p'):
        _p.replace_with('\n' + _p.get_text() + '\n')

    # 6. 處理 <h1> 至 <h6> 標籤
    for tag in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
        tagtext = tag.get_text()
        tag.attrs = {}  # 清空所有屬性
        tag.attrs['text'] = tagtext  # 設定 text 屬性為純文字內容

    # 根據 tag_list 進行條件判斷刪除
    if tag.attrs and tag.attrs.get("id") and any(t.lower() in tag.attrs["id"].lower() for t in tag_list):
        tag.decompose()
    elif tag.attrs and tag.attrs.get("class") and any(t.lower() in ' '.join(tag.attrs["class"]).lower() for t in tag_list):
        tag.decompose()

    # 7. 處理 <a> 標籤：只保留 href 屬性且 href 長度不超過 320
    for a_tag in soup.find_all('a'):
        href = a_tag.get('href') if 'href' in a_tag else a_tag.attrs.get('href') if a_tag.attrs else ''
        # 若 href 存在且長度不超過 320，則只保留 href 屬性；否則刪除該 <a> 標籤
        if href:
            # 檢查是否符合 ".html" 後有 ; 或 : 的情況，並進行截斷
            match = re.match(r'(.+?\.html)([;:].*)', href)
            if match:
                href = match.group(1)  # 截斷至 .html

            # 若 href 超過 320 字元，則刪除整個 <a> 標籤；否則僅保留 href 屬性
            if len(href) <= 320:
                a_tag.attrs = {'href': href}
            else:
                a_tag.decompose()  # 移除 href 過長的 <a> 標籤
        else:
            a_tag.decompose()  # 若 href 不存在，則直接移除 <a> 標籤

    # 處理類似表格的結構
    table_likes = soup.find_all(detect_table_like_structure)
    for tl in table_likes:
        tl.replaceWith(table_like_to_table(soup, tl, title))

    return soup


# 在主函數中使用
def get_html_content(url):
    chrome_options = prepare_chrome_options()
    chrome_options.add_argument('user-agent=%s' % random.choice(user_agents))
    html_content = None
    window_size = None

    try:
        try:
            with webdriver.Chrome(options=chrome_options) as driver:
                driver.get(url)
                driver.implicitly_wait(5)
                #WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))

                # 獲取頁面尺寸
                window_size = driver.get_window_size()
                #outer_divs = driver.find_elements(By.XPATH, "//body/div | //body/div/* | //body/div/*/*| //body/div/*/*/*| //body/*/*/*/div| //body/*/*/*/*/div")

                # 設置分類清單
                contents = []
                banners = []

                # 計算文字單詞數
                def count_words(text):
                    return len(text.split())

                # 遍歷所有 div 元素並應用條件
                for d in driver.find_elements(By.XPATH, "//body/div | //body/div/* | //body/div/*/*| //body/div/*/*/*| //body/*/*/*/div| //body/*/*/*/*/div"):
                    try:
                        if d.text=='' or not d.is_displayed() or d.rect['height'] is None or d.rect['width'] is None or d.rect['height'] == 0 or d.rect['width'] == 0 or (d.rect['height'] * d.rect['width']< 100):
                            banners.append(d)
                            continue
                        elif d.rect['height'] / d.rect['width'] > 5:
                            banners.append(d)
                            continue
                        # drect = copy.deepcopy(d.rect)
                        # drect['outerHTML'] = d.get_attribute('outerHTML').strip()
                        # drect['text'] = d.get_attribute("textContent").strip()
                        #
                        # # 基本過濾條件
                        # if not d.is_displayed():
                        #     continue
                        # if drect['height'] is None or drect['width'] is None or drect['height'] == 0 or drect['width'] == 0:
                        #     continue
                        # if drect['height'] * drect['width'] < 100:
                        #     continue
                        #
                        # # 判斷「重要內容」
                        # if (window_height > 0 and drect['height'] / window_height > 0.6 and drect[
                        #     'width'] / window_width > 0.6 and
                        #         not (drect['x'] == 0 and drect['y'] == 0)):
                        #     if len(drect['text']) > 10:
                        #         if len(contents) == 0 or drect['outerHTML'] not in contents[-1]['outerHTML']:
                        #             if len(contents) > 0 and drect['text'] in contents[-1]['text'] and len(
                        #                     drect['text']) > 50 and len(contents[-1]['text']) > 50:
                        #                 pass
                        #             else:
                        #                 contents.append(drect)
                        #
                        # # 判斷「橫幅區域」
                        # elif (drect['height'] / drect['width'] > 5 and drect['height'] > 0.5 * window_height and
                        #       (drect['x'] < window_width / 4 or drect['x'] > 3 * window_width / 4)):
                        #     if len(banners) == 0 or drect['outerHTML'] not in banners[-1]['outerHTML']:
                        #         banners.append(drect)
                        #
                        # # 判斷寬橫幅
                        # elif (drect['height'] > 0 and window_width > 0 and (drect['width'] / drect['height']) / (
                        #         window_width / window_height) > 5 and
                        #       drect['width'] > 0.5 * window_width and (
                        #               drect['y'] < window_height / 4 or drect['y'] > 3 * window_height / 4)):
                        #     if len(banners) == 0 or drect['outerHTML'] not in banners[-1]['outerHTML']:
                        #         banners.append(drect)
                        #
                        # # 進一步的「重要內容」判斷
                        # elif (drect['height'] and 0.5 < drect['width'] / drect['height'] < 2 and
                        #       drect['width'] > 0.5 * window_width and drect['height'] > 0.5 * window_height and drect[
                        #           'y'] < window_height / 3):
                        #     if count_words(drect['text']) > 10:
                        #         if len(contents) == 0 or drect['outerHTML'] not in contents[-1]['outerHTML']:
                        #             if len(contents) > 0 and drect['text'] in contents[-1]['text'] and count_words(
                        #                     drect['text']) > 50 and count_words(contents[-1]['text']) > 50:
                        #                 pass
                        #             else:
                        #                 contents.append(drect)

                    except Exception as e:
                        print(f"元素處理失敗：{e}")


                # 獲取HTML內容
                head_html = driver.find_element(By.TAG_NAME, 'head').get_attribute('outerHTML')
                body_html = driver.find_element(By.TAG_NAME, 'body').get_attribute('outerHTML')
                # # 如果確實需要 refresh，先執行
                # driver.refresh()
                # # refresh 後給瀏覽器和網頁一些時間，讓 DOM 結構穩定下來
                # WebDriverWait(driver, 4).until(EC.presence_of_element_located((By.TAG_NAME, "body")))

                for elem in banners:
                    _html=elem.get_attribute('outerHTML')
                    if _html in body_html:
                        body_html=body_html.replace(_html,'')
                html_content ='<html>' + head_html + body_html + '</html>'
        except StaleElementReferenceException:
            # 遇到 stale，代表此元素又被DOM刷新或其他原因
            # 依需求，可直接跳過或重新抓一次
            pass
        # WebDriver 在這裡被釋放

        if html_content:
            soup = optimize_html(html_content)
            if not soup.name :
                soup.name='web'
            return soup.prettify(formatter="html")
        else:
            logging.error(f"Failed to retrieve HTML content from {url}")
            return None

    except Exception as e:
        logging.error(f"Error accessing {url}: {str(e)}")
        PrintException()
        return None

@pysnooper.snoop()
def search_web(url: str) -> list:
    """

    Args:
        url:


    Returns:

    Examples:
        >>> search_web('https://tw.stock.yahoo.com/quote/2301.TW/revenue')

    """
    print(cyan_color("search_web:{0}".format(url)), flush=True)

    text_frags = []
    title = ''
    clear_html = retrieve_clear_html(url)
    if clear_html is None:
        return None, '', 200

    soup = BeautifulSoup(clear_html, 'html.parser')

    def no_div_children(tag):
        return (tag.name == 'table') or (tag.name == 'p' and tag.text and len(tag.text.strip()) > 0) or (tag.name == 'a' and 'href' in tag ) or (
                tag.name == 'div' and tag.text and len(tag.text.strip()) > 0 and len(tag.find_all('p')) == 0 and not [d
                                                                                                                      for
                                                                                                                      d
                                                                                                                      in
                                                                                                                      tag.find_all(
                                                                                                                          'div')
                                                                                                                      if
                                                                                                                      len(d.text.strip()) > 20])

    title_tag = soup.find('title')
    if title_tag:
        title = title_tag.text.strip()
        # total_words = count_words(soup.text.strip())

        # for tag in soup.find_all('div'):
        #     div_children = tag.find_all('div')
        #     div_children = [count_words(d.text.strip()) for d in div_children if
        #                     d.text and len(d.text.strip()) > 0]
        #     if len(div_children) > 0:
        #         mean_len = np.array(div_children).mean()
        #         if len(div_children) > 5 and mean_len < 10:
        #             tag.decompose()

    total_words = count_words(soup.text.strip())

    def tag2markdown(tag, idx, text_frags):
        if text_frags is None:
            text_frags = []
        if tag.name == 'table':
            _parts_text = htmltable2markdown(tag.prettify(formatter=None))[0]
            _text = tag.find('caption').text.strip() if tag.find('caption') else ''
            _text += '\n' + '\n'.join([tr.text.strip() for tr in tag.find_all('tr')[:2]])
        else:
            h = HTML2Text(baseurl=url)
            _parts_text = h.handle(
                '<html>' + title_tag.prettify() + '<body>' + tag.prettify(formatter=None) + '</body></html>')

        return _parts_text

    def process_long_item(p):
        paras = []
        for s in p.text.strip().split('\n'):
            if len(s) == 0:
                pass
            elif count_words(s) <= 300:
                paras.append(s)
            elif count_words(s) > 300:
                paras.extend(seg_as_sentence(s))

        # 選單
        if count_words(p.text.strip()) / len(paras) < 10:
            return []
        elif np.array([1.0 if _p.strip().startswith('^') else 0.0 for _p in paras if
                       len(_p.strip()) > 1]).mean() > 0.9:
            return []  # 參考文獻、引用
        group_results = optimal_grouping([count_words(_p.strip()) for _p in paras], min_sum=200,
                                         max_sum=300)
        results = []
        # slot_group = copy.deepcopy(group_results)
        current_idx = 0

        # 把字數分組當作插槽插入tag
        slot_group = copy.deepcopy(group_results)
        for n in range(len(group_results)):
            this_group = group_results[n]
            if len(this_group) > 1:
                for g in range(len(this_group)):
                    slot_group[n][g] = paras[current_idx]
                    current_idx += 1
            elif len(this_group) == 1:
                slot_group[n][0] = paras[current_idx]
                current_idx += 1

        for idx in range(len(slot_group)):
            g = slot_group[idx]
            if len(g) > 0:
                this_text = ''.join(g) if len(g) > 1 else g[0]
                if len(this_text) > 0:
                    tag = Tag(soup, name="div")
                    text = NavigableString(this_text)
                    tag.insert(0, text)
                    results.append(tag)
        return results

    try:
        parts = soup.find_all(no_div_children)
        new_parts = []
        for p in parts:
            if p.name == 'table':
                tag2markdown(p, 0, text_frags=text_frags)

                new_parts.append(p)
            elif count_words(p.text.strip()) > 300:
                lparts = process_long_item(p)
                new_parts.extend(lparts)
                lparts = [build_text_fragment(source=url, title=title, page_num=0, paragraph_num=0,
                                              text=lp.get_text().strip(), content=lp.get_text().strip()) for lp in
                          lparts if len(lp.get_text().strip()) > 10]

            else:
                new_parts.append(p)
        parts = new_parts
        if len(parts) == 1 and (parts[0].name == 'table' or count_words(parts[0].text.strip()) < 300):
            md = tag2markdown(parts[0], 0, text_frags)
            cxt.memory.bulk_update(url, text_frags)
            text_frags = []
            return md, title, 200
        group_results = optimal_grouping([count_words(p.text.strip()) if p.name != 'table' else 300 for p in parts],
                                         min_sum=200,
                                         max_sum=300)
        grouped_parts = []
        # slot_group = copy.deepcopy(group_results)
        current_idx = 0

        # 把字數分組當作插槽插入tag
        slot_group = copy.deepcopy(group_results)
        for n in range(len(group_results)):
            this_group = group_results[n]
            if len(this_group) > 1:
                for g in range(len(this_group)):
                    slot_group[n][g] = parts[current_idx]
                    current_idx += 1
            elif len(this_group) == 1:
                slot_group[n][0] = parts[current_idx]
                current_idx += 1

        # 逐一檢查插槽，將插槽內tag合併
        for n in range(len(slot_group)):
            this_group = slot_group[n]
            this_text = '\n'.join([t.text.strip() for t in this_group]) if len(this_group) > 1 else this_group[
                0].text.strip() if len(this_group) == 1 else ''
            if len(this_group) > 1:
                tag = Tag(soup, name="div")
                tag.insert(0, this_text)
                grouped_parts.append(tag)

            elif len(this_group) == 1:
                grouped_parts.append(slot_group[n][0])
        parts_text = [tag2markdown(p, i, text_frags) for i, p in enumerate(grouped_parts)]

        tables = htmltable2markdown(soup.prettify(formatter=None))
        _tables = soup.find_all("table")
        for idx in range(len(_tables)):
            t = _tables[idx]
            tag = Tag(soup, name="div")

            text = NavigableString("@placeholder-table-{0}".format(idx))
            tag.insert(0, text)
            t.replaceWith(tag)

        h = HTML2Text(baseurl=url)
        resulttext = h.handle(soup.prettify(formatter=None))

        for idx in range(len(tables)):
            t = tables[idx]
            resulttext = resulttext.replace("@placeholder-table-{0}".format(idx), t)

        # content = '\n'.join(['\n'.join(list(div.stripped_strings)) for div in divs])
        text_len = len(resulttext)
        return resulttext, title, 200
    except Exception as e:
        PrintException()
        print(e)
        return None, '', 400


def search_webpilot(url: str, *args, **kwargs) -> str:
    """

    Args:
        url:
        *args:
        **kwargs:

    Returns:

    Examples:
        >>> search_webpilot("https://tw.stock.yahoo.com/quote/2301.TW/revenue")
        []

    """

    header = {
        "Content-Type": "application/json",
        "WebPilot-Friend-UID": str(uuid.uuid4()),
    }

    data = {
        "link": url,
        "ur": "search",
        "l": 'zh-TW',
        "lp": True,
        "rt": False
    }
    endpoint = "https://webreader.webpilotai.com/api/visit-web"
    resp = requests.post(endpoint, headers=header, json=data, verify=False)

    logging.debug("webpilot resp: {}".format(resp.json()))
    # temp = resp.json()
    # if 'content' in temp:
    #     temp['content'] = cleasing_web_text(temp['content'])

    return json.dumps(resp.json(), ensure_ascii=False)


def second_derivative(x):
    return np.gradient(np.gradient(x))


def cleasing_web_text(text: str):
    """

    Args:
        url:
        *args:
        **kwargs:

    Returns:

    Examples:
        >>> cleasing_web_text(eval(search_webpilot("https://www.businesstoday.com.tw/article/category/80394/post/202104150009/"))['content'])
        []

    """

    lines = []
    is_valuable = []
    for t in text.replace(' ', '\n\n').split('\n'):
        if len(t) > 300:
            ss = seg_as_sentence(t)
            lines.extend(ss)
            is_valuable.extend([1] * len(ss))
        elif len(t) > 0:
            lines.append(t)
            is_valuable.append(0)

    is_valuable = np.array(is_valuable)
    text_lens = np.array([len(t) for t in lines])
    total_words = np.array(text_lens).sum()
    freq = {}
    for t in lines:
        if len(t) > 0:
            if len(t) not in freq:
                freq[len(t)] = 0
            freq[len(t)] += 1
    sorted_freq = sorted(freq.items(), key=lambda kv: (kv[0], kv[1]), reverse=True)
    sorted_freq = {k: v for k, v in sorted_freq}
    keys = list(sorted_freq.keys())
    remain_text = total_words
    current_len = None
    need_check = True
    while remain_text > 0.05 * total_words and (current_len is None or current_len > 10) and need_check:
        this_len = keys.pop(0)
        match_cnt = len(text_lens[text_lens == this_len])
        if match_cnt == 1:
            is_valuable[text_lens == this_len] = 1
            remain_text -= this_len
        else:
            if current_len and this_len / current_len > 0.5:
                is_valuable[text_lens == this_len] = 1
                remain_text -= this_len * match_cnt
            elif current_len and this_len / current_len < 0.5:
                need_check = False
        current_len = this_len

    results = []
    in_valid_zone = False
    partial_words = ''
    for idx in range(len(lines)):
        t = lines[idx]
        check = is_valuable[idx]
        if check == 1:
            if not in_valid_zone:
                in_valid_zone = True
            if len(partial_words) == 0:
                partial_words = t
            else:
                partial_words += '\n\n' + t
            if len(partial_words) > 100:
                results.append(partial_words)
                print(green_color(partial_words), flush=True)
                partial_words = ''
        else:
            if in_valid_zone:
                if (idx > 0 and is_valuable[idx - 1] == 1) or (idx < len(lines) - 1 and is_valuable[idx + 1] == 1):
                    if len(partial_words) > 20:
                        results.append(partial_words)
                        print(green_color(partial_words), flush=True)
                    partial_words = t
            else:
                print(magenta_color(t), flush=True)
    return results

# def cleasing_web_text(text: str):
#     lines = text.replace(' ', '\n\n').split('\n')
#     text_lens = [len(t) for t in lines if len(t) > 0]
#     freq = {}
#     for t in lines:
#         if len(t) > 0:
#             if len(t) not in freq:
#                 freq[len(t)] = 0
#             freq[len(t)] += len(t)
#     sorted_freq = sorted(freq.items(), key=lambda kv: (kv[1], kv[0]), reverse=True)
#     sorted_freq = {k: v for k, v in sorted_freq}

#     total_words = np.array(text_lens).sum()
#     keys = np.array(list(sorted_freq.keys()))
#     text_lens_ratio = np.array(list(sorted_freq.values())) / total_words
#     text_lens_accu_ratio = np.array([text_lens_ratio[:i + 1].sum() for i in range(len(sorted_freq))])
#     x_array = np.array([sorted_freq[k] / k / len(text_lens) for k in keys])
#     accu_x_array = np.array([x_array[:i + 1].sum() for i in range(len(sorted_freq))])
#     slop_array = text_lens_accu_ratio / accu_x_array
#     slop_array_1 = np.array(
#         [slop_array[i] - slop_array[i - 1] if i > 0 else slop_array[i] for i in range(len(slop_array))])
#     return text_lens_accu_ratio
