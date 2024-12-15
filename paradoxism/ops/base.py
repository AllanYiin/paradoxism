import json
import ast
import re
import time
import asyncio
import xmltodict  # 使用第三方庫處理複雜的 XML/HTML
import yaml
from typing import Dict, Any
from paradoxism.utils import *
from paradoxism.utils.regex_utils import *
from paradoxism.base.agent import _thread_local,LLMClient
from paradoxism.ops.convert import *
from concurrent.futures import ThreadPoolExecutor

__all__ = ["prompt","chain_of_thought"]

def reference(*args, **kwargs):
    """
    根據輸入的參數生成格式化的字串。
    - 單個參數會直接格式化為： '\n\n\"\"\"\n\n
    {input}\n\n\"\"\"\n\n'
        - 多個參數會格式化為： '\n\n\"\"\"\n\n{input1}\n\n\"\"\"\n\n\"\"\"\n\n{input2}\n\n\"\"\"\n\n'
        - 若提供標題（kwargs）會生成對應的格式： '\n\n\"\"\"\n\n  # {title}\n\n{input}\n\n\"\"\"\n\n'
    """
    if kwargs:
        # 處理有標題的情況
        result = []
        for title, content in kwargs.items():
            result.append(f'\n\n"""\n\n# {title}\n\n{content}\n\n"""\n\n')
        return "".join(result)

    elif len(args) == 1:
        # 處理單個輸入的情況
        return f'\n\n"""\n\n{args[0]}\n\n"""\n\n'

    elif len(args) > 1:
        # 處理多個輸入的情況
        result = []
        for content in args:
            result.append(f'\n\n"""\n\n{content}\n\n"""\n\n')
        return "".join(result)

    else:
        raise ValueError("至少需要一個輸入參數或標題鍵值對。")
def prompt(prompt_text: str, input_kwargs=None,output_type:str='str',**kwargs):
    """
    執行給定的 prompt 並返回解析後的 LLM 回應。
    支持多種格式：json, python, xml, html, markdown, yaml。

    Args:
        prompt_text (str): 提示文本。
        output_type (str): 指定輸出型別。

    Returns:
        Any: 解析後的 Python 對象或原始字符串。
    """


    if not isinstance(output_type,str):
        output_type=output_type.__name__
    # 獲取當前 FlowExecutor 的 LLMClient
    llm_client = getattr(_thread_local, 'llm_client', None)
    if not llm_client:
        raise RuntimeError("prompt 函數必須在 @agent 裝飾的函數內部調用。")

    input_args = getattr(_thread_local, 'input_args', '')
    if not input_kwargs:
        input_kwargs={}
        if input_kwargs:
            for k,v in input_args.items():
                input_kwargs[k]=v['arg_value']

    returns = getattr(_thread_local, 'returns', '')
    variables_need_to_replace = re.findall(r'{(.*?)}', prompt_text)

    start_time = time.time()  # 記錄開始時間

    # 生成完整的提示
    static_instruction = getattr(_thread_local, 'static_instruction', '')
    input_info=reference(**input_kwargs) if len(input_kwargs)>0 else ''
    full_prompt = f"{static_instruction}\n{prompt_text}\n{input_info}"
    is_json=False
    if output_type in ['dict','json']:
        full_prompt = full_prompt+"\n\n請以json的格式輸出"
        is_json=True

    # 使用 ThreadPoolExecutor 非同步執行 llm_client.generate
    with ThreadPoolExecutor() as executor:
        future = executor.submit(llm_client.generate, full_prompt,is_json, **kwargs)
        response = future.result()  # 等待回應並取出結果

    # 處理代碼塊標記並解析
    #parsed_response = parse_llm_response(response)
    if output_type=='str':
        parsed_response = response
    else:
        parsed_response=force_cast(response,output_type)
    end_time = time.time()  # 記錄結束時間
    execution_time = end_time - start_time  # 計算執行時間
    print(yellow_color(f"executed in {execution_time:.4f} seconds"),
          gray_color('prompt:\n' + full_prompt.strip()),
          green_color('result:\n' + str(parsed_response)),flush=True)  # 輸出執行時間

    return parsed_response



def chain_of_thought(prompt_text: str, output_type:str='str',**kwargs):
    """
    執行給定的 prompt 並返回chain_of_thought解析後的 LLM 回應。
    支持多種格式：json, python, xml, html, markdown, yaml。

    Args:
        prompt_text (str): 提示文本。
        output_type (str): 指定輸出型別。

    Returns:
        Any: 解析後的 Python 對象或原始字符串。
    """
    system_prompt="""在使用者輸入後，即使**看起來再簡單的問題**，都必須針對使用者所輸入內容中的關鍵概念進行**概念對齊**，若涉及**歧義**請同時將各種可能性都陳述給使用者，並請以人類的角度思考歧義的合理性，若涉及專有名詞請上網查詢相關資訊並整理成詳實的概念對齊筆記，概念對齊筆記開頭請先以markdown 3級標題列印出"Concept Alignment"，然後概念對齊筆記每一列都要用含markdown引用符號的無序清單"> - "開頭。
在**產生答案之前**或是**反思過程之後**，則需要進行Chain-of-thought解題思路規劃，也就是透過一步一步地思考各種可能性、考慮反思(如果前面有的話)的觀點、排除不可能選項、推導最後找到答案，Chain-of-thought開頭請先以markdown 3級標題列印出"Chain-of-thought"，然後Chain-of-thought每一列都要用markdown引用符號"> "開頭。思路清晰後才可以向下產出答案。
每次產生答案後，必須執行反思過程，在反思過程中你將扮演冷酷客觀的第三者，檢核答案有無錯誤、誤解或是推理錯誤的狀況，同時反思先前的答案，思考有無其他的可能或改進之處，反思過程開頭請先以markdown 3級標題列印出"Rethink"，然後反思過程每一列都要用markdown引用符號">> "開頭。反思過程的結束後請根據反思結果的建議透過Chain-of-thought來調整與修改先前的答案，若是覺得有必要還可以多一次反思與Chain-of-thought的循環
所有**涉及數據的引用**絕對禁止憑記憶回答或是隨意杜撰，都必須先上網查詢、確認並附上引用來源資料
#zh-TW 請以繁體中文回答"""

    if not isinstance(output_type,str):
        output_type=output_type.__name__
    # 獲取當前 FlowExecutor 的 LLMClient
    llm_client = getattr(_thread_local, 'llm_client', None)
    if not llm_client:
        raise RuntimeError("prompt 函數必須在 @agent 裝飾的函數內部調用。")

    input_args = getattr(_thread_local, 'input_args', '')
    returns = getattr(_thread_local, 'returns', '')
    variables_need_to_replace = re.findall(r'{(.*?)}', prompt_text)

    start_time = time.time()  # 記錄開始時間

    # 生成完整的提示
    static_instruction = getattr(_thread_local, 'static_instruction', '')
    full_prompt = f"{static_instruction}\n{prompt_text}"
    is_json=False
    if output_type in ['dict','json']:
        full_prompt = full_prompt+"\n\n請以json的格式輸出"
        is_json=True

    # 使用 ThreadPoolExecutor 非同步執行 llm_client.generate
    with ThreadPoolExecutor() as executor:
        kwargs={'temperature':1.0}
        future = executor.submit(llm_client.generate, full_prompt,is_json,False,system_prompt, **kwargs)
        response = future.result()  # 等待回應並取出結果

    # 處理代碼塊標記並解析
    #parsed_response = parse_llm_response(response)
    if output_type=='str':
        parsed_response = response
    else:
        parsed_response=force_cast(response,output_type)
    end_time = time.time()  # 記錄結束時間
    execution_time = end_time - start_time  # 計算執行時間
    print(yellow_color(f"executed in {execution_time:.4f} seconds"),
          gray_color('prompt:\n' + full_prompt.strip()),
          green_color('result:\n' + str(parsed_response)),flush=True)  # 輸出執行時間

    return parsed_response

def parse_llm_response(response: str) -> Any:
    """
    解析 LLM 返回的包含代碼塊的字符串，轉換為相應的 Python 對象。
    支持 json, python, xml, html, markdown, yaml 格式。

    :param response: LLM 的回應字符串
    :return: 解析後的 Python 對象或原始字符串
    """
    # 使用正則表達式匹配代碼塊
    code_block_pattern = r'```(\w+)?\n([\s\S]*?)\n```'
    match = re.match(code_block_pattern, response.strip())
    if not match:
        # 如果不符合代碼塊格式，直接返回原始字符串
        return response.strip()

    language = match.group(1).lower() if match.group(1) else 'text'
    content = match.group(2)

    if language in ['python', 'py']:
        try:
            # 使用 ast.literal_eval 安全地解析 Python 字典
            parsed = ast.literal_eval(content)
            return parsed
        except Exception as e:
            PrintException()
            print(response,flush=True)
            raise ValueError(f"無法解析 Python 代碼塊內容: {e}")
    elif language == 'json':
        try:
            # 解析 JSON 內容
            content=extract_json(content)
            parsed = json.loads(content)
            # 如果解析結果是空字典，轉換為空列表
            if parsed == {}:
                return []
            return parsed
        except json.JSONDecodeError as e:
            raise ValueError(f"無法解析 JSON 代碼塊內容: {e}")
    elif language == 'xml':
        try:
            # 解析 XML 內容並轉換為字典
            parsed = xml_to_dict(content)
            return parsed
        except Exception as e:
            raise ValueError(f"無法解析 XML 代碼塊內容: {e}")
    elif language == 'html':
        try:
            # 解析 HTML 內容並轉換為字典
            parsed = html_to_dict(content)
            return parsed
        except Exception as e:
            raise ValueError(f"無法解析 HTML 代碼塊內容: {e}")
    elif language == 'markdown':
        # 返回原始 Markdown 字符串
        return content.strip()
    elif language == 'yaml':
        try:
            parsed = yaml.safe_load(content)
            return parsed
        except yaml.YAMLError as e:
            raise ValueError(f"無法解析 YAML 代碼塊內容: {e}")
    else:
        # 如果是其他語言，返回原始內容
        return content.strip()

def xml_to_dict(xml_str: str) -> Dict[str, Any]:
    """
    將 XML 字符串轉換為 Python 字典。

    :param xml_str: XML 字符串
    :return: Python 字典
    """
    return xmltodict.parse(xml_str)

def html_to_dict(html_str: str) -> Dict[str, Any]:
    """
    將 HTML 字符串轉換為 Python 字典。

    :param html_str: HTML 字符串
    :return: Python 字典
    """
    return xmltodict.parse(html_str)
