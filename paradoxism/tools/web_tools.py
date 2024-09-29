import json
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

from paradoxism.utils.utils import *
from paradoxism.utils import regex_utils, web_utils


__all__ = ["quick_search","open_url","detail_search"]



#sem = threading.Semaphore(3)



def get_pdf_content(pdf_url):
    from paradoxism.utils import pdf_utils
    _pdf = pdf_utils.PDF(pdf_url)
    _pdf.parsing_save()
    return _pdf.doc_text


def better_keywords(query_intent, keywords_cnt=3):
    _prompt = """
        你是一個專業的網路搜索達人，你能夠根據使用者提供的搜索意圖中的關鍵概念，根據以下原則轉化為{0}組實際查詢的關鍵字組合，輸出格式為markdown的有序清單，關鍵字間請用加號分隔)
         - 請基於第一性原則，思考這樣的使用者意圖會在甚麼樣的網頁中出現
         - 從使用者意圖以及剛才思考的網頁特性，思考出最重要關鍵字再加上1~2個次要的關鍵詞切忌整個句子丟進去。
         - 請確認有將足夠的限定詞放入關鍵字中，以確保查詢出來的內容不至於有語意模糊，或是查詢結果過度雜亂的問題。
         - 如果查詢要限定時間範圍，請以'關鍵詞  + before: 或 after:+ 年份(**不包含該年份**) '的形式呈現，例如要2022年至今，就應該是:'關鍵詞 after:2021'
         -  每次查詢關鍵字不應超過3個，為了控制在此數量建議採取通稱(例如將營業收入、營業成本、毛利、毛利率通稱為損益表)，或者是分批查詢
         - 直接輸出，無須解釋
        """.format(keywords_cnt)
    client = get_azure_openai(model="gpt-4-32k")
    response = client.chat.completions.create(
        model="gpt-4-32k",
        messages=[
            {'role': 'system', 'content': _prompt},
            {'role': 'user', 'content': "用戶意圖:{0}".format(query_intent)}
        ],
        temperature=0.8,
        n=1,
        stream=False,

    )
    if response and response.choices and response.choices[0].message:
        response_message = response.choices[0].message.content
        results_list = [t.replace(regex_utils.extract_numbered_list_member(t), '').strip() for t in
                        response_message.split('\n') if len(t) > 0]
        print('better search:{0}'.format(results_list))
        return results_list
    else:
        return None
def better_search(query_intent, keywords_cnt=3, search_domain=None,it=None):
    if it is not None and  it=='full_list':
        keywords_cnt=5
    results_list=better_keywords(query_intent, keywords_cnt)
    if results_list:
        all_search_list = None
        for item in results_list:
            query =item.replace('+',' ')
            if search_domain:
                query=query+" site:{0}".format(search_domain)

            google_search_lists, _ = web_utils.search_google(query)
            # search_url_bing = f"https://www.bing.com/search?{query}"
            print(item, google_search_lists)
            if all_search_list is None:
                all_search_list = google_search_lists
            else:
                cnt_limit=8 if it=='full_list' else 5 if it=='reasearch' else 3
                all_search_list.extend(
                    google_search_lists if len(google_search_lists) <= cnt_limit else
                    google_search_lists[:cnt_limit])
            # search_list.extend(search_url_bing)
        url_deup = {}
        webpage_list = []
        for item in all_search_list:
            if item['url'] not in cxt.memory.urls:
                if item['url'] not in url_deup:
                    url_deup[item['url']] = 1
                    webpage_list.append(item)
        all_search_list = webpage_list
        print('better search results:', green_color(str(all_search_list)), flush=True)
        return all_search_list
    else:
        query =query_intent.replace('+',' ')
        google_search_lists, _ = web_utils.search_google(query)
        print('google search results:', green_color(str(google_search_lists)), flush=True)
        return google_search_lists


def search_rag(ur, top_k=5, min_similarity=0.88, internal_similarity=0.97,use_question_variants=True,variants_cnt=3,it=None):
    """

    Args:
        internal_similarity:
        variants_cnt:
        use_question_variants:
        ur:
        top_k:
        min_similarity:
        it: Information extraction types: gathering (understanding a concept),answer(find an ansewer),news,full_list(search a full list,except news),stock(about 光寶科技liteon, 2301 or it's competitors'  revenure , stock price and public  financial data) ,datasets,  profile, commodity, prices...."

    Returns:

    """
    return_results = {}
    if cxt.memory.vector is None or (len( cxt.memory.vector)<10):
        return return_results
    try:
        query_results = cxt.memory.lookup(ur, top_k, min_similarity=min_similarity,internal_similarity=internal_similarity,use_question_variants=use_question_variants,variants_cnt=variants_cnt)



        rag_label='<img src="./images/rag.png" alt = "rag" title = "powered by RAG" width="48" height="48"/>'
                   #'![web](./images/rag.png) [{0}]'.format('powered by RAG', ''))
        if rag_label not in cxt.citations:
            cxt.citations.append(rag_label)
        # for k, v in query_results.items():
        #     cxt.citations.append('![web](../images/web.png) [{0}]({1})'.format(
        #         v['text'][:15] + '...' if len(v['text']) > 15 else v['text'], v['source']))
        rag_tokens=0
        if it in ['full_list','answer', 'gathering']:
            return_results = {
                "prompt": "以下為RAG機制所提取出來的查詢結果，請整合你原有的知識，將查詢結果整理成人類高可讀性的形式，並將細節以有序列表的形式整合其中來做為回覆內容，回覆內容確保知識點不至於遺漏，務必引述出處。請以markdown格式來撰寫回復，輸出包括標題階層(開頭要有個一級標題)、內容的詳細說明。**若是RAG查詢結果不足以回答問題**，也請思考新的查詢參數，重新調用webpage_reader，以補充答案不足之處"}
        elif it in ['table']:
            return_results = {
                "prompt": "以下為RAG機制從網頁中取得之表格或數據，請先讀取內容後，請仔細思考後，參考其內容來回答使用者，請盡可能保留與使用者需求相符之內容，包括需要引述出處，不要過度簡化或是刪減。輸出格式建議為markdown格式的表格再加上說明文字"}
        else:
            return_results = {
                "prompt": "以下為RAG機制所提取出來的參考資料，將參考資料整理成適合使用者閱讀以及理解的形式來做為回覆內容，回覆內容應該盡可能**保留細節**，務必引述出處。以markdown格式來書寫，請以markdown來撰寫回復，輸出包括標題階層(開頭要有個一級標題)、內容的詳細說明。**若是RAG查詢結果不足以回答問題**，也請思考新的查詢參數，重新調用webpage_reader，以補充答案不足之處"}
        rag_tokens+=estimate_used_tokens(str(return_results))
        return_results['user intent']=ur
        rag_tokens+=(estimate_used_tokens(str(ur))+4)
        new_query_results=[]
        for k,v in query_results.items():
            this_tokens=(estimate_used_tokens(str(v))+4)
            if rag_tokens+this_tokens<int(cxt.oai[cxt.baseChatGpt.llm.model]["max_tokens"])*0.5:
                new_query_results.append(v)
                rag_tokens+=this_tokens
            else:
                break

        return_results['search_results'] = new_query_results
        #print('RAG', 'Q: {0}\n'.format(ur), orange_color(json.dumps(return_results, ensure_ascii=False)), flush=True)
        return json.dumps(return_results, ensure_ascii=False)
    except:
        PrintException()
        return json.dumps(return_results, ensure_ascii=False)

def quick_search(ur, kw,dm=None,l=None,**kwargs):
    print(yellow_color(f"quick_search user request:{ur},  kw:{kw}, dm:{dm}"), flush=True)
    kw=kw.split('+')
    # 避免關鍵字被分拆 世界紀錄=>世界 紀錄
    kw='+'.join(['"'+w+'"' if len(w)>2 else w for w in kw])
    return_results =[]
    if dm and dm not in kw:
        kw=kw+" site:{0}".format(dm)
    results=web_utils.search_google(kw)[0]
    if results and len(results)>0:
        return_results.extend(results)
    return json.dumps(return_results, ensure_ascii=False)

def open_url(url,**kwargs):
    print(yellow_color(f"open_url url:{url}"), flush=True)
    response = requests.head(url)
    if 'application/pdf' in response.headers.get('Content-Type', '') or url.endswith('.pdf'):
        try:
            pdf_doc_text = get_pdf_content(url)
            cxt.citations.append(f'![pdf](./image/pdf.png) [{link.split("/")[-1]}]({url})')
            return pdf_doc_text
        except:
            PrintException()
    else:
        new_results = web_utils.retrieve_clear_html(url)
        return new_results

def detail_search(ur, dm=None, l: str='zh-TW', it: str=None,**kwargs):
    print(yellow_color(f"detail_search user request:{ur},  it:{it}, dm:{dm}"), flush=True)
    returnData = OrderedDict()
    if it in ['full_list','news']:
        search_lists = better_search(ur,  search_domain='tw.stock.yahoo.com') if it == 'stock' and lv == 0 else better_search(
            ur, search_domain=dm)
        threads = []
        if len(search_lists) > 5:
            search_lists = search_lists[:5]
        with ThreadPoolExecutor(max_workers=5) as executor:
            for item in search_lists:
                if 'url' in item and item['url'] not in list(cxt.memory._cache.keys()):
                    _url = item['url']
                    # 使用 run_in_thread_with_loop 確保事件循環正確設置
                    th = executor.submit(open_url, _url)
                    # threads.append(th)
                    # if len(threads) == 5:
                    #     break

            for future in as_completed(threads):
                try:
                    url, results = future.result()
                    print(url, results, flush=True)
                    returnData[url] = results
                except Exception as e:
                    print(f"Error processing URL: {e}", flush=True)
    else:
        rag_results = eval(search_rag(ur, 1, 0.88, it=it, use_question_variants=False))
        if len(rag_results['search_results']) >= 5:
            return rag_results
        else:
            search_lists = better_search(ur, search_domain='tw.stock.yahoo.com') if it == 'stock' and lv == 0 else better_search(ur,search_domain=dm)
            threads = []
            if len(search_lists)>5:
                search_lists=search_lists[:5]
            with ThreadPoolExecutor(max_workers=5) as executor:
                for item in search_lists:
                    if 'url' in item and item['url'] not in list(cxt.memory._cache.keys()):
                        _url = item['url']
                        # 使用 run_in_thread_with_loop 確保事件循環正確設置
                        th = executor.submit(open_url,_url)
                        threads.append(th)
                        # if len(threads) == 5:
                        #     break

                for future in as_completed(threads):
                    try:
                        url, results = future.result()
                        print(url, results, flush=True)
                        returnData[url] = results
                    except Exception as e:
                        print(f"Error processing URL: {e}", flush=True)
    return json.dumps(returnData, ensure_ascii=False)


