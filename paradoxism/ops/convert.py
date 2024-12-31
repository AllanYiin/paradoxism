import html
import json
import logging
import regex
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Any, Iterable
from collections import OrderedDict
import markdown
from jsonschema import validate, ValidationError
from paradoxism.utils import *
from paradoxism.utils.regex_utils import *
__all__ = ["force_cast","target_types","to_json","is_json_serializable"]

target_types=["str", "int", "float", "date", "dict", "list", "json", "xml", "markdown", "html", "code"]

def force_cast(response: str, target_type: str, schema=None) -> Any:
    """
    Force cast the LLM response to the specified type.

    Args:
        response (str): The LLM response string.
        target_type (str): The target type ("str", "int", "float", "date", "dict", "list", "json", "xml", "markdown", "html", "code").
        schema (dict, optional): The JSON schema for validation.

    Returns:
        Any: The result after type casting.
    """

    try:
        # 針對沒有指定 target_type 的情況
        if not target_type:
            return response
        if not isinstance(target_type, str):
            target_type = target_type.__name__
        if target_type == 'string':
            target_type = 'str'
        if not isinstance(response, str):
            response = str(response)

        # ---------- int ----------
        if target_type == "int":
            response = response.replace(",", "")  # 去除逗號
            number_match = regex.search(r"-?\d+", response)
            if number_match:
                return int(number_match.group(0))
            return "Error: Could not convert to int"

        # ---------- float ----------
        elif target_type == "float":
            response = response.replace(",", "")  # 去除逗號
            number_match = regex.search(r"-?\d+\.?\d*([eE][-+]?\d+)?", response)
            if number_match:
                return float(number_match.group(0))
            return "Error: Could not convert to float"

        # ---------- date ----------
        elif target_type == "date":
            date_match = regex.search(r"\d{4}-\d{2}-\d{2}", response)
            if date_match:
                try:
                    return datetime.strptime(date_match.group(0), "%Y-%m-%d")
                except ValueError:
                    return "Error: Invalid date format"
            return "Error: Could not find a valid date"

        # ---------- json / dict / list ----------
        elif target_type in ["json", "dict", "list"]:
            response_cleaned = regex.sub(r"OrderedDict\(\[.*?\]\)", "{}", response)
            json_match = regex.search(json_uncompile_pattern, response_cleaned, regex.DOTALL | regex.VERBOSE)

            # 如果能抓到符合 JSON 格式
            if json_match:
                clean_response = json_match.group(0)
                clean_obj = eval(clean_response)

                # 這裡先判斷是否為 dict 或 list
                if isinstance(clean_obj, dict):
                    if target_type == 'dict':
                        return clean_obj
                    elif target_type == 'list':
                        # 如果是 dict 且要轉成 list，就將 values() 做 list 化
                        return list(clean_obj.values())
                elif isinstance(clean_obj, list):
                    if target_type == 'list':
                        return clean_obj
                    elif target_type == 'dict':
                        # 如果是 list 且要轉成 dict，就用 enumerate 轉成 {idx:val, ...}
                        return {i: k for i, k in enumerate(clean_obj)}

            # 如果 json_match 抓不到有效 JSON，且目標是 'list'，就嘗試從文字中抓取列表
            if target_type == 'list':
                # 嘗試抓取有序或無序列表項目
                # (1) 有序列表 e.g. "1. 內容"、"2. 內容"
                # (2) 無序列表 e.g. "* 內容"、"- 內容"、"+ 內容"
                # 使用 MULTILINE 模式以支援多行偵測
                bullet_pattern = r"(?m)^\s*(?:\d+\.\s+|[\*\-\+]\s+)(.*)"
                found_items = regex.findall(bullet_pattern, response)

                if found_items:
                    # 將每個項目去除前後空白後回傳
                    return [item.strip() for item in found_items]
                else:
                    # 代表既不是 JSON，也沒找到符合模式的列表
                    print("Error: Not a valid JSON format or list pattern in text")
                    return "Error: Could not parse as a bullet or ordered list"

            # 如果不是要轉換成 list/dict，就直接報錯 (因為前面已經失敗)
            print("Error: Not a valid JSON format", red_color(response), flush=True)
            return "Error: Not a valid JSON format: "

        # ---------- json_schema ----------
        elif target_type == "json_schema":
            json_match = regex.search(r"\{.*?\}|\[.*?\]|OrderedDict\(\[.*?\]\)", response, regex.DOTALL)
            if json_match:
                clean_response = json_match.group(0)
                if clean_response.startswith("OrderedDict"):
                    clean_response = clean_response.replace("OrderedDict(", "").rstrip(")")
                    clean_response = clean_response.replace("[", "").replace("]", "")
                    items = clean_response.split("), (")
                    items = [item.replace("(", "").replace(")", "").replace(", ", ": ", 1) for item in items]
                    clean_response = "{" + ", ".join(items) + "}"
                    clean_response = clean_response.replace(": ", ": '").replace(", ", "', ").replace("}", "'}")
                parsed_json = eval(clean_response)

                if schema is not None:
                    try:
                        validate(instance=parsed_json, schema=schema)
                        return parsed_json
                    except ValidationError as e:
                        print("Error: Not a valid JSON format", red_color(response), flush=True)
                        return f"JSON Schema validation error: {str(e)}"
                return "Error: No schema provided for JSON schema validation"
            else:
                print("Error: Not a valid JSON format", red_color(response), flush=True)
                return "Error: Not a valid JSON format"

        # ---------- code ----------
        elif target_type == "code":
            code_block_match = regex.search(r"```(.*?)```", response, regex.DOTALL)
            if code_block_match:
                return code_block_match.group(1).strip()

            inline_code_match = regex.search(r"`([^`]+)`", response)
            if inline_code_match:
                return inline_code_match.group(1).strip()
            return "Error: No code block found"

        # ---------- xml ----------
        elif target_type == "xml":
            try:
                return ET.fromstring(response)
            except ET.ParseError as e:
                return f"Error during XML conversion: {str(e)}"

        # ---------- str ----------
        elif target_type == "str":
            return response.strip()

        # ---------- markdown ----------
        elif target_type == "markdown":
            return markdown.markdown(response.strip())

        # ---------- html ----------
        elif target_type == "html":
            return html.unescape(response.strip())

        else:
            raise ValueError(f"Unsupported target type: {target_type}")

    except NameError:
        PrintException()
        return response_cleaned
    except Exception as e:
        return f"Error during conversion: {str(e)}"


def json_serialize(data):
    return json.dumps(data, ensure_ascii=False, indent=4)

def is_json_serializable(value):
    if isinstance(value, (dict, list, tuple, str, int, float, bool, type(None))):
        return True
    elif hasattr(value, "__dict__"):
        # 檢查 __dict__ 的內容是否都可序列化
        return all(is_json_serializable(v) for v in value.__dict__.values())
    else:
        return False

def to_json(data):
    """
    Convert the given data to a JSON string.

    Args:
        data: The data to be converted to JSON. It can be of any type.

    Returns:
        str: The JSON string representation of the input data.
    """
    try:
        # 如果是字典，先確認所有值是否可序列化
        if isinstance(data, dict):
            serializable_dict = {k: (to_json(v) if hasattr(v, "__dict__") else v if is_json_serializable(v) else str(v)) for k, v in data.items()}
            return json_serialize(serializable_dict)
        # 如果是自訂類別的物件，將其屬性轉換為字典後再進行轉換
        elif hasattr(data, "__dict__"):
            # 先檢查屬性是否可序列化
            if is_json_serializable(data):
                return json_serialize(data.__dict__)
            else:
                serializable_dict = {k: (to_json(v) if hasattr(v, "__dict__") else v if is_json_serializable(v) else str(v)) for k, v in data.__dict__.items()}
                return json_serialize(serializable_dict)
        # 如果是可迭代的其他資料類型 (排除字串)
        elif isinstance(data, Iterable) and not isinstance(data, (str, bytes)):
            return json_serialize([to_json(item) if hasattr(item, "__dict__") else item for item in data])
        # 其他可被 JSON 序列化的資料類型
        else:
            return json_serialize(data)
    except (TypeError, ValueError) as e:
        # 捕捉不能被序列化的例外，記錄錯誤並返回錯誤訊息
        logging.error(f"Unable to serialize object: {str(e)}", exc_info=True, stack_info=True)
        return json_serialize({"error": f"Unable to serialize object: {str(e)}"})