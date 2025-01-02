import re
from collections import OrderedDict
from typing import Any, Dict, List, Tuple
__all__ = ["parse_docstring","extract_function_info"]
_target_types=["str", "int", "float", "date", "dict", "list", "json", "xml", "markdown", "html", "code"]

def detect_style(docstring: str) -> str:
    """
    根據給定的結構和內容檢測 docstring 的風格。

    Args:
        docstring (str): 要分析的 docstring。

    Returns:
        str: 檢測到的風格（'plain'，'google'，'numpy'，'epytext'，'restructured'）。

    當 docstring 為空時，默認返回 'plain'，表示未檢測到特定的格式。
    """
    if not docstring:
        return 'plain'

    if re.search(r'Args:|Returns:', docstring):
        return 'google'
    elif re.search(r'Parameters\s*[-]+', docstring) and re.search(r'Returns\s*[-]+', docstring):
        return 'numpy'
    elif re.search(r'@param|@return', docstring):
        return 'epytext'
    elif re.search(r':param|:returns:', docstring):
        return 'restructured'
    else:
        return 'plain'
def parse_docstring(docstring: str,style=None) -> dict:
    """
    將給定的 docstring 解析為結構化的字典。

    支援的 docstring 格式包括：
    - Google 風格（以 "Args:" 和 "Returns:" 為標識）
    - Numpy 風格（以 "Parameters" 和 "Returns" 標題為標識）
    - Epytext 風格（以 "@param" 和 "@return" 為標識）
    - RestructuredText 風格（以 ":param" 和 ":returns:" 為標識）
    - Plain（無特定標識的簡單描述）

    Args:
        docstring (str): 要解析的 docstring。

    Returns:
        dict: 包含以下結構的字典：
            - 'static_instruction'：靜態描述的文字部分。
            - 'input_args'：輸入參數的清單。
            - 'return'：返回值的描述清單。
    """
    result = {
        'static_instruction': '',
        'input_args': [],
        'return': []
    }

    if not docstring:
        return result
    if not style:
        style = detect_style(docstring)

    parsers = {
        'numpy': parse_numpy_style,
        'epytext': parse_epytext_style,
        'google': parse_google_style,
        'restructured': parse_restructuredtext_style,
        'plain': parse_plain_style
    }

    parse_function = parsers.get(style, parse_plain_style)
    return parse_function(docstring)
def validate_arg_type(arg_type: str) -> str:
    """
    驗證並標準化參數型別。

    Args:
        arg_type (str): 輸入的型別名稱。

    Returns:
        str: 驗證後的型別名稱，未知則返回 "Unknown"。
    """
    normalized_type = arg_type.lower()
    if normalized_type in _target_types:
        return normalized_type
    return "Unknown"

def remove_special_sections(docstring: str) -> str:
    """
    移除 docstring 中的特殊段落，例如 Examples、Exceptions 和 Raises。

    Args:
        docstring (str): 要清理的 docstring。

    Returns:
        str: 清理後的 docstring。
    """
    special_section_patterns = [r'Examples?:', r'Exceptions?:', r'Raises?:']
    for pattern in special_section_patterns:
        docstring = re.split(pattern, docstring)[0].strip()
    return docstring



def parse_plain_style(docstring: str) -> dict:
    """
    解析簡單格式的 docstring。

    Args:
        docstring (str): 要解析的 docstring。

    Returns:
        dict: 包含靜態描述、輸入參數及返回值的資訊。

    適用情境：
        當 docstring 不符合 Google、Numpy、Epytext 或 RestructuredText 格式時，
        將其作為簡單的靜態描述進行處理，僅返回純文本內容。
    """
    result = {
        'static_instruction': docstring.strip(),
        'input_args': [],
        'return': []
    }

    return result


def parse_google_style(docstring: str) -> dict:
    """
    Parse docstring in Google style.

    Args:
        docstring (str): The docstring to parse.

    Returns:
        dict: Parsed information.
    """
    result = {
        'static_instruction': '',
        'input_args': [],
        'return': []
    }

    docstring = remove_special_sections(docstring)

    params_pattern = re.compile(r'Args:', re.IGNORECASE)
    returns_pattern = re.compile(r'Returns:', re.IGNORECASE)

    params_match = params_pattern.search(docstring)
    returns_match = returns_pattern.search(docstring)

    if params_match:
        result['static_instruction'] = docstring[:params_match.start()].strip()
        params_section = docstring[params_match.end():returns_match.start() if returns_match else None]

        for line in params_section.strip().splitlines():
            match = re.match(r'\s*(\w+)\s*\(?([\w, ]*)\)?\s*:?(.*)', line)
            if match:
                arg_name, arg_type, arg_desc = match.groups()
                result['input_args'].append({
                    'arg_name': arg_name,
                    'arg_type': validate_arg_type(arg_type),
                    'arg_desc': arg_desc.strip()
                })

    if returns_match:
        return_section = docstring[returns_match.end():].strip()
        result['return'].append({
            'return_name': 'return' if len(result['return']) == 0 else 'return{0}'.format(len(result['return']) + 1),
            'return_type': 'Unknown',
            'return_desc': return_section
        })

    return result


def parse_numpy_style(docstring: str) -> dict:
    """
    Parse docstring in Numpy style.

    Args:
        docstring (str): The docstring to parse.

    Returns:
        dict: Parsed information.
    """
    result = {
        'static_instruction': '',
        'input_args': [],
        'return': []
    }

    docstring = remove_special_sections(docstring)

    params_pattern = re.compile(r'Parameters\s*[-]+', re.IGNORECASE)
    returns_pattern = re.compile(r'Returns\s*[-]+', re.IGNORECASE)

    params_match = params_pattern.search(docstring)
    returns_match = returns_pattern.search(docstring)

    if params_match:
        params_section = docstring[params_match.end():returns_match.start() if returns_match else None]
        for line in params_section.strip().splitlines():
            match = re.match(r'\s*(\w+)\s*:\s*([\w, ]*)\s*\n?(.*)', line)
            if match:
                arg_name, arg_type, arg_desc = match.groups()
                result['input_args'].append({
                    'arg_name': arg_name,
                    'arg_type': arg_type.strip() if arg_type else 'Unknown',
                    'arg_desc': arg_desc.strip()
                })

    if returns_match:
        return_section = docstring[returns_match.end():].strip()
        result['return'].append({
            'return_name': 'return' if len(result['return']) == 0 else 'return{0}'.format(len(result['return']) + 1),
            'return_type': 'Unknown',
            'return_desc': return_section
        })

    return result


def parse_epytext_style(docstring: str) -> dict:
    """
    Parse docstring in Epytext style.

    Args:
        docstring (str): The docstring to parse.

    Returns:
        dict: Parsed information.
    """
    result = {
        'static_instruction': '',
        'input_args': [],
        'return': []
    }

    docstring = remove_special_sections(docstring)

    param_pattern = re.compile(r'@param\s+(\w+)\s*:\s*(.*)', re.IGNORECASE)
    return_pattern = re.compile(r'@return:\s*(.*)', re.IGNORECASE)

    for match in param_pattern.finditer(docstring):
        arg_name, arg_desc = match.groups()
        result['input_args'].append({
            'arg_name': arg_name,
            'arg_type': 'Unknown',
            'arg_desc': arg_desc.strip()
        })

    return_match = return_pattern.search(docstring)
    if return_match:
        result['return'].append({
            'return_name': 'return' if len(result['return']) == 0 else 'return{0}'.format(len(result['return']) + 1),
            'return_type': 'Unknown',
            'return_desc': return_match.group(1).strip()})

    return result


def parse_restructuredtext_style(docstring: str) -> dict:
    """
    Parse docstring in RestructuredText style.

    Args:
        docstring (str): The docstring to parse.

    Returns:
        dict: Parsed information.
    """
    result = {
        'static_instruction': '',
        'input_args': [],
        'return': []
    }

    docstring = remove_special_sections(docstring)

    param_pattern = re.compile(r':param\s+(\w+):\s*(.*)', re.IGNORECASE)
    return_pattern = re.compile(r':returns:\s*(.*)', re.IGNORECASE)

    for match in param_pattern.finditer(docstring):
        arg_name, arg_desc = match.groups()
        result['input_args'].append({
            'arg_name': arg_name,
            'arg_type': 'Unknown',
            'arg_desc': arg_desc.strip()
        })

    return_match = return_pattern.search(docstring)
    if return_match:
        result['return'].append({
                'return_name': 'return' if len(result['return']) == 0 else 'return{0}'.format(len(result['return']) + 1),
            'return_type': 'Unknown',
            'return_desc': return_match.group(1).strip()})

    return result


def extract_function_info(func) -> Dict[str, Any]:
    """
    提取函數的結構化資訊，結合函數的型別提示與 docstring。

    Args:
        func: 要分析的函數物件。

    Returns:
        dict: 包含靜態描述、輸入參數及返回值的資訊。

    此函數會解析函數的型別提示（type hints），並結合函數的 docstring 提供的描述進行整合。
    例如，若型別提示與 docstring 的參數描述不一致，則優先使用型別提示的資訊。
    若 docstring 缺失，則基於型別提示補全函數資訊。
    """
    result = {
        'static_instruction': '',
        'input_args': [],
        'return': []
    }

    docstring = inspect.getdoc(func)
    if docstring:
        docstring_info = parse_docstring(docstring)
        result.update(docstring_info)

    type_hints = inspect.signature(func).parameters
    return_hint = inspect.signature(func).return_annotation

    for param_name, param in type_hints.items():
        arg_type = str(param.annotation) if param.annotation != inspect.Parameter.empty else 'Unknown'
        arg_desc = next((info['arg_desc'] for info in result['input_args'] if info['arg_name'] == param_name), '')

        result['input_args'].append({
            'arg_name': param_name,
            'arg_type': arg_type,
            'arg_desc': arg_desc
        })

    if return_hint != inspect.Signature.empty:
        result['return'].append({
            'return_name': '',
            'return_type': str(return_hint),
            'return_desc': result['return'][0]['return_desc'] if result['return'] else ''
        })

    return result