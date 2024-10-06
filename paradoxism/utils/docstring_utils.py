import re
from collections import OrderedDict
__all__ = ["parse_docstring"]

def detect_style(docstring: str) -> str:
    """
    Detects the style of the given docstring based on its structure and content.

    Args:
        docstring (str): The docstring to analyze.

    Returns:
        str: The detected style ('plain', 'google', 'numpy', 'epytext', 'restructured').
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
    Parses a given docstring into a structured dictionary.

    Args:
        docstring (str): The docstring to parse.
        style (str): The style of the docstring ('plain', 'google', 'numpy', 'epytext', 'restructured'). Default is 'plain'.

    Returns:
        dict: A dictionary containing 'static_instruction', 'input_args', and 'return' information.
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

    result['static_instruction'] = '\n\n'.join(static_parts)

    # 解析 input_args
    if params_match:
        params_section = docstring[params_match.end():returns_match.start() if returns_match else None].strip().splitlines()

        for line in params_section:
            match = re.match(r'\s*(\w+)\s*\((\w+)\):\s*(.*)', line)
            if match:
                arg_name, arg_type, arg_desc = match.groups()
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


