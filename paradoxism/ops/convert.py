import re
import json
import xml.etree.ElementTree as ET
from datetime import datetime
import markdown
import html
from typing import Any, Dict, List
from jsonschema import validate, ValidationError

__all__ = ["force_cast","target_types"]

target_types=["str", "int", "float", "date", "dict", "list", "json", "xml", "markdown", "html", "code"]

def force_cast(response: str, target_type: str,schema=None) -> Any:
    """
    根據指定型別強制轉型 LLM 回應
    :param response: LLM 回應字串
    :param target_type: 目標型別 ("str", "int", "float", "date", "dict", "list", "json", "xml", "markdown", "html", "code")
    :return: 轉型後的結果
    """

    # 直接根據不同的目標類型來進行處理
    try:
        # 對於數字類型 (int, float) 的特殊處理，直接抓取數字
        if target_type == "int":
            response = response.replace(",", "")  # 去除逗號
            number_match = re.search(r"-?\d+", response)
            if number_match:
                return int(number_match.group(0))
            return "Error: Could not convert to int"

        elif target_type == "float":
            response = response.replace(",", "")  # 去除逗號
            number_match = re.search(r"-?\d+\.?\d*([eE][-+]?\d+)?", response)
            if number_match:
                return float(number_match.group(0))
            return "Error: Could not convert to float"

        elif target_type == "date":
            date_match = re.search(r"\d{4}-\d{2}-\d{2}", response)
            if date_match:
                try:
                    return datetime.strptime(date_match.group(0), "%Y-%m-%d")
                except ValueError:
                    return "Error: Invalid date format"
            return "Error: Could not find a valid date"

            # JSON 和字典處理
        elif target_type in ["json", "dict", "list"]:
            # 使用正則表達式提取有效的 JSON 部分
            json_match = re.search(r"\{.*?\}|\[.*?\]", response)
            if json_match:
                clean_response = json_match.group(0)
                return json.loads(clean_response)
            return "Error: Not a valid JSON format"

            # JSON Schema 驗證
        elif target_type == "json_schema":
            # 首先提取 JSON
            json_match = re.search(r"\{.*?\}|\[.*?\]", response)
            if json_match:
                clean_response = json_match.group(0)
                parsed_json = json.loads(clean_response)
                # 驗證 JSON 是否符合指定的 schema
                if schema is not None:
                    try:
                        validate(instance=parsed_json, schema=schema)
                        return parsed_json  # 驗證通過，返回 JSON
                    except ValidationError as e:
                        return f"JSON Schema validation error: {str(e)}"
                return "Error: No schema provided for JSON schema validation"
            return "Error: Not a valid JSON format"

            # 處理 Markdown 中的程式碼區塊提取
        elif target_type == "code":
            # 優先匹配區塊程式碼 ```code block```
            code_block_match = re.search(r"```(.*?)```", response, re.DOTALL)
            if code_block_match:
                return code_block_match.group(1).strip()

            # 匹配行內程式碼 `inline code`
            inline_code_match = re.search(r"`([^`]+)`", response)
            if inline_code_match:
                return inline_code_match.group(1).strip()

            return "Error: No code block found"

        # XML 轉換
        elif target_type == "xml":
            try:
                return ET.fromstring(response)
            except ET.ParseError as e:
                return f"Error during XML conversion: {str(e)}"

        # 其他類型的處理
        elif target_type == "str":
            return response.strip()

        elif target_type == "markdown":
            return markdown.markdown(response.strip())

        elif target_type == "html":
            return html.unescape(response.strip())

        else:
            raise ValueError(f"Unsupported target type: {target_type}")

    except Exception as e:
        return f"Error during conversion: {str(e)}"
