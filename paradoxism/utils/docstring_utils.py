import re
from collections import OrderedDict
from typing import Any, Dict, List, Tuple
__all__ = ["parse_docstring","extract_function_info"]

def detect_style(docstring: str) -> str:
    """
    根據給定的結構和內容檢測docstring的風格。

    參數:
        docstring (str): 要分析的docstring。

    返回:
        str: 檢測到的風格（'plain'，'google'，'numpy'，'epytext'，'restructured'）。
    """
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


def parse_docstring(docstring: str, style=None) -> dict:
    """
    將給定的docstring解析為結構化的字典。

    參數:
        docstring (str): 要解析的docstring。
        style (str): docstring的風格（'plain'，'google'，'numpy'，'epytext'，'restructured'）。默認為'plain'。

    返回:
        dict: 包含'static_instruction'，'input_args'和'return'信息的字典。
    """
    result = {
        'static_instruction': '',
        'input_args': [],
        'return': []
    }
    if docstring is None or docstring=='':
        return result
    style = detect_style(docstring)

    if style == 'numpy':
        result = parse_numpy_style(docstring)
    elif style == 'epytext':
        result = parse_epytext_style(docstring)
    elif style == 'google':
        result = parse_google_style(docstring)
    elif style == 'restructured':
        result = parse_restructuredtext_style(docstring)
    else:
        result = parse_plain_style(docstring)

    return result



def remove_special_sections(docstring: str) -> str:
    """
    Remove sections such as Examples, Exceptions, and Raises from docstring.
    """
    special_section_patterns = [r'Examples?:', r'Exceptions?:', r'Raises?:']
    for pattern in special_section_patterns:
        docstring = re.split(pattern, docstring)[0].strip()
    return docstring


def parse_plain_style(docstring: str) -> dict:
    result = {
        'static_instruction': '',
        'input_args': [],
        'return': []
    }

    # Remove special sections
    docstring = remove_special_sections(docstring)

    params_pattern = re.compile(r'Parameters:|Args:', re.IGNORECASE)
    returns_pattern = re.compile(r'Returns:', re.IGNORECASE)

    params_match = params_pattern.search(docstring)
    returns_match = returns_pattern.search(docstring)

    static_parts = []
    upper_end=None
    lower_start = None
    if params_match:
        upper_end = params_match.start()
        lower_start= params_match.end()

    if returns_match:
        upper_end = returns_match.start() if upper_end is None else upper_end
        lower_start= returns_match.end()

    if not params_match and not returns_match:
        static_parts.append(docstring.strip())
    else:
        static_parts.append(docstring[:upper_end].strip())
        static_parts.append(docstring[lower_start+1:].strip())


    result['static_instruction'] = '\n\n'.join(static_parts)

    # 解析 input_args
    if params_match:
        params_section = docstring[params_match.end():returns_match.start() if returns_match else None]
        params_lines = params_section.strip().splitlines()

        for line in params_lines:
            match = re.match(r'\s*(\w+)\s*\((\w+)\):\s*(.*)', line)
            if match:
                arg_name, arg_type, arg_desc = match.groups()
                result['input_args'].append({
                    'arg_name': arg_name,
                    'arg_type': arg_type,
                    'arg_desc': arg_desc
                })

    # 解析 return 部分
    if returns_match:
        return_section = docstring[returns_match.end():].strip().splitlines()

        for i, line in enumerate(return_section):
            match = re.match(r'\s*(\w+):\s*(.*)', line)
            if match:
                return_type, return_desc = match.groups()
                result['return'].append({
                    'return_name': '',
                    'return_index': i,
                    'return_type': return_type,
                    'return_desc': return_desc
                })

    return result


def parse_google_style(docstring: str) -> dict:
    result = {
        'static_instruction': '',
        'input_args': [],
        'return': []
    }

    # Remove special sections
    docstring = remove_special_sections(docstring)

    params_pattern = re.compile(r'Args:', re.IGNORECASE)
    returns_pattern = re.compile(r'Returns:', re.IGNORECASE)

    params_match = params_pattern.search(docstring)
    returns_match = returns_pattern.search(docstring)

    static_parts = []
    if params_match:
        static_parts.append(docstring[:params_match.start()].strip())
    if returns_match:
        static_parts.append(docstring[returns_match.end():].strip())

    result['static_instruction'] = ('\n\n'.join(static_parts)).strip()

    # 解析 input_args
    if params_match:
        params_section = docstring[params_match.end():returns_match.start() if returns_match else None].strip().splitlines()

        for line in params_section:
            # 尝试匹配标准写法：参数名 (类型): 描述
            match = re.match(r'\s*(\w+)\s*\((\w+)\):\s*(.*)', line)
            if match:
                arg_name, arg_type, arg_desc = match.groups()
            else:
                # 尝试匹配类型在冒号后的写法：参数名: 类型 描述
                match = re.match(r'\s*(\w+)\s*:\s*(\w+)\s*(.*)', line)
                if match:
                    arg_name, arg_type, arg_desc = match.groups()
                else:
                    # 如果没有匹配到类型，假设类型未知
                    match = re.match(r'\s*(\w+)\s*:\s*(.*)', line)
                    if match:
                        arg_name, arg_desc = match.groups()
                        arg_type = 'Unknown'
                    else:
                        continue

            # 处理将 str 误写为 string 的情况
            if arg_type.lower() == 'string':
                arg_type = 'str'

            result['input_args'].append({
                'arg_name': arg_name,
                'arg_type': arg_type,
                'arg_desc': arg_desc
            })


    # 解析 return
    if returns_match:
        return_section = docstring[returns_match.end():].strip().splitlines()

        for i, line in enumerate(return_section):
            match = re.match(r'\s*(\w+):\s*(.*)', line)
            if match:
                return_type, return_desc = match.groups()
                result['return'].append({
                    'return_name': '',
                    'return_index': i,
                    'return_type': return_type,
                    'return_desc': return_desc
                })

    return result


def parse_numpy_style(docstring: str) -> dict:
    result = {
        'static_instruction': '',
        'input_args': [],
        'return': []
    }

    # 使用正則表達式匹配 Numpy 格式中的 Parameters 和 Returns
    params_pattern = re.compile(r'Parameters\s*[-]+', re.IGNORECASE)
    returns_pattern = re.compile(r'Returns\s*[-]+', re.IGNORECASE)

    params_match = params_pattern.search(docstring)
    returns_match = returns_pattern.search(docstring)

    # 靜態描述的部分
    static_parts = []
    if params_match:
        static_parts.append(docstring[:params_match.start()].strip())

    # 解析 input_args
    if params_match:
        params_section = docstring[params_match.end():returns_match.start() if returns_match else None]
        params_lines = params_section.strip().splitlines()

        param_name = None
        param_desc = []
        for line in params_lines:
            # 檢測新參數的開始
            match = re.match(r'\s*(\w+)\s*:\s*(\w+)', line)
            if match:
                if param_name:
                    result['input_args'].append({
                        'arg_name': param_name,
                        'arg_type': param_type,
                        'arg_desc': ' '.join(param_desc).strip()
                    })
                param_name, param_type = match.groups()
                param_desc = []
            else:
                param_desc.append(line.strip())

        if param_name:
            result['input_args'].append({
                'arg_name': param_name,
                'arg_type': param_type,
                'arg_desc': ' '.join(param_desc).strip()
            })

    # 解析 return
    if returns_match:
        returns_section = docstring[returns_match.end():].strip().splitlines()

        return_type = None
        return_desc = []
        for i, line in enumerate(returns_section):
            # 如果遇到情感列表，則停止處理 return，並將其視為靜態描述的一部分
            if "Positive emotions" in line or "Negative emotions" in line:
                static_parts.append("\n".join(returns_section[i:]).strip())
                break

            match = re.match(r'\s*(\w+)', line)
            if match and return_type is None:  # 只解析第一個有效返回值
                return_type = match.group(1)
            else:
                return_desc.append(line.strip())

        if return_type:
            result['return'].append({
                'return_name': '',
                'return_index': 0,
                'return_type': return_type,
                'return_desc': ' '.join(return_desc).strip()
            })

    # 最後處理靜態描述
    result['static_instruction'] = '\n\n'.join(static_parts).strip()

    return result


def parse_epytext_style(docstring: str) -> dict:
    result = {
        'static_instruction': '',
        'input_args': [],
        'return': []
    }

    # 匹配 @param 和 @return 以及 @type 和 @rtype 的正則表達式
    param_pattern = re.compile(r'@param\s+(\w+):\s*(.*)', re.IGNORECASE)
    type_pattern = re.compile(r'@type\s+(\w+):\s*(\w+)', re.IGNORECASE)
    return_pattern = re.compile(r'@return:\s*(.*)', re.IGNORECASE)
    rtype_pattern = re.compile(r'@rtype:\s*(\w+)', re.IGNORECASE)

    # 匹配參數、類型、返回值的匹配結果
    param_matches = param_pattern.findall(docstring)
    type_matches = type_pattern.findall(docstring)
    return_match = return_pattern.search(docstring)
    rtype_match = rtype_pattern.search(docstring)

    # 逐行處理 docstring，排除參數、返回值和特殊區段來構建 static_instruction
    doc_lines = docstring.splitlines()
    static_instruction_lines = []
    in_static_section = True

    for line in doc_lines:
        stripped_line = line.strip()
        # 如果當前行包含 @param、@type、@return 或 @rtype，則該行屬於參數或返回值部分，跳過這些部分
        if param_pattern.match(stripped_line) or return_pattern.match(stripped_line) or rtype_pattern.match(stripped_line) or type_pattern.match(stripped_line):
            continue
        elif stripped_line:
            static_instruction_lines.append(stripped_line)

    # 將靜態描述的部分用換行符號連接
    result['static_instruction'] = "\n".join(static_instruction_lines).strip()

    # 解析 input_args
    for param, desc in param_matches:
        param_type = next((t[1] for t in type_matches if t[0] == param), None)
        result['input_args'].append({
            'arg_name': param,
            'arg_type': param_type if param_type else '',
            'arg_desc': desc.strip()
        })

    # 解析 return
    if return_match and rtype_match:
        result['return'].append({
            'return_name': '',
            'return_index': 0,
            'return_type': rtype_match.group(1),
            'return_desc': return_match.group(1).strip()
        })

    return result

def parse_restructuredtext_style(docstring: str) -> dict:
    result = {
        'static_instruction': '',
        'input_args': [],
        'return': []
    }

    # 匹配 :param, :type, :returns, :rtype 的正則表達式
    param_pattern = re.compile(r':param\s+(\w+):\s*(.*)', re.IGNORECASE)
    type_pattern = re.compile(r':type\s+(\w+):\s*(\w+)', re.IGNORECASE)
    return_pattern = re.compile(r':returns:\s*(.*)', re.IGNORECASE)
    rtype_pattern = re.compile(r':rtype:\s*(\w+)', re.IGNORECASE)

    # 匹配參數和返回值
    param_matches = param_pattern.findall(docstring)
    type_matches = type_pattern.findall(docstring)
    return_match = return_pattern.search(docstring)
    rtype_match = rtype_pattern.search(docstring)

    # 逐行處理 docstring，排除參數、返回值和特殊區段來構建 static_instruction
    doc_lines = docstring.splitlines()
    static_instruction_lines = []
    in_static_section = True

    for line in doc_lines:
        stripped_line = line.strip()
        # 如果當前行包含 :param、:type、:returns 或 :rtype，則進入非靜態區段
        if param_pattern.match(stripped_line) or return_pattern.match(stripped_line) or rtype_pattern.match(stripped_line) or type_pattern.match(stripped_line):
            continue
        elif stripped_line:  # 只在 static 部分時累積
            static_instruction_lines.append(stripped_line)

    # 將靜態描述的部分用換行符號連接
    result['static_instruction'] = "\n".join(static_instruction_lines).strip()

    # 解析 input_args
    for param, desc in param_matches:
        param_type = next((t[1] for t in type_matches if t[0] == param), None)
        result['input_args'].append({
            'arg_name': param,
            'arg_type': param_type if param_type else '',
            'arg_desc': desc.strip()
        })

    # 解析 return
    if return_match and rtype_match:
        result['return'].append({
            'return_name': '',
            'return_index': 0,
            'return_type': rtype_match.group(1),
            'return_desc': return_match.group(1).strip()
        })

    return result


def extract_function_info(func) -> Dict[str, Any]:
    result = {
        'static_instruction': '',
        'input_args': [],
        'return': []
    }
    docstring_info={}
    # 獲取函數的型別提示
    type_hints = inspect.signature(func).parameters
    return_hint = inspect.signature(func).return_annotation
    docstring = inspect.getdoc(func)

    # 解析 docstring
    if docstring:
        docstring_info=parse_docstring(docstring)

        # 提取參數資訊
    for param_name, param in type_hints.items():
        # 優先判斷 type hinting
        if param.annotation != inspect.Parameter.empty:
            arg_type = str(param.annotation)
        # 其次判斷預設值的類型
        elif param.default != inspect.Parameter.empty:
            arg_type = type(param.default).__name__
        # 最後檢查 docstring 的描述
        else:
            arg_type = 'Unknown'  # 無法解析則設為 Unknown

        # 查找 docstring 的參數描述
        arg_desc = next((info['arg_desc'] for info in docstring_info['input_args'] if info['arg_name'] == param_name),
                        '')

    # 處理回傳值，考慮多個回傳值的情況
    if return_hint != inspect.Signature.empty:
        # 若回傳值是 Tuple，解析每個元素的類型
        if hasattr(return_hint, '__origin__') and return_hint.__origin__ == Tuple:
            for i, subtype in enumerate(return_hint.__args__):
                return_type = str(subtype) if subtype != inspect.Signature.empty else 'Unknown'
                return_desc = docstring_info['return'][i]['return_desc'] if i < len(
                    docstring_info['return']) else ''

                result['return'].append({
                    'return_name': f'return_{i}',
                    'return_index': i,
                    'return_type': return_type,
                    'return_desc': return_desc
                })
        else:
            # 單一回傳值情況
            return_type = str(return_hint)
            return_desc = docstring_info['return'][0]['return_desc'] if docstring_info['return'] else ''
            result['return'].append({
                'return_name': '',
                'return_index': 0,
                'return_type': return_type,
                'return_desc': return_desc
            })
    else:
        # 無法解析的回傳值情況
        result['return'].append({
            'return_name': '',
            'return_index': 0,
            'return_type': 'Unknown',
            'return_desc': ''
        })

    return result