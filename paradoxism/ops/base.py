import json
import ast
import re
import time
import xmltodict  # 使用第三方庫處理複雜的 XML/HTML
import yaml
from typing import Dict, Any
from paradoxism.utils.utils import *
from paradoxism.base.agent import _thread_local,LLMClient

def prompt(prompt_text: str):
    """
    執行給定的 prompt 並返回解析後的 LLM 回應。
    支持多種格式：json, python, xml, html, markdown, yaml。

    :param prompt_text: 提示文本
    :return: 解析後的 Python 對象或原始字符串
    """
    # 獲取當前 FlowExecutor 的 LLMClient
    llm_client = getattr(_thread_local, 'llm_client', None)
    if not llm_client:
        raise RuntimeError("prompt 函數必須在 @agent 裝飾的函數內部調用。")

    start_time = time.time()  # 記錄開始時間
    # 生成完整的提示
    instruction = getattr(_thread_local, 'static_instruction', '')
    full_prompt = f"{instruction}\n{prompt_text}"
    response = llm_client.generate(full_prompt)

    # 處理代碼塊標記並解析
    parsed_response = parse_llm_response(response)

    end_time = time.time()  # 記錄結束時間
    execution_time = end_time - start_time  # 計算執行時間
    print(green_color(f"prompt:"), yellow_color(f"executed in {execution_time:.4f} seconds"),full_prompt.strip(),flush=True)  # 輸出執行時間

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
            raise ValueError(f"無法解析 Python 代碼塊內容: {e}")
    elif language == 'json':
        try:
            # 解析 JSON 內容
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
