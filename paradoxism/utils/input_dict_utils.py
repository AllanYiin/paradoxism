import inspect
from collections import OrderedDict
from  typing import Callable
try:
    from typing import get_type_hints
except ImportError:
    from typing_extensions import get_type_hints
import re
from paradoxism.utils.docstring_utils import parse_docstring
__all__ = ["get_input_dict"]

def _generate_inputs_dict(func: Callable, *args, **kwargs) -> OrderedDict:
    inputs_dict = OrderedDict()
    signature = inspect.signature(func)
    for i, (param_name, param) in enumerate(signature.parameters.items()):
        if len(args) > i:
            inputs_dict[param_name] = {
                'arg_name': param_name,
                'arg_value': args[i],
                'arg_type': param.annotation.__name__ if param.annotation or param.annotation.__name__ !='_empty' else None,
                'arg_desc': None
            }
        elif param_name in kwargs:
            inputs_dict[param_name] = {
                'arg_name': param_name,
                'arg_value': kwargs[param_name],
                'arg_type': param.annotation.__name__ if param.annotation or param.annotation.__name__ !='_empty'  else None,
                'arg_desc': None
            }
        elif param.default is not inspect.Parameter.empty:
            inputs_dict[param_name] = {
                'arg_name': param_name,
                'arg_value': str(param.default),
                'arg_type': param.annotation.__name__ if param.annotation and param.annotation.__name__!='_empty' else None,
                'arg_desc': None
            }
        else:
            inputs_dict[param_name] = {
                'arg_name': param_name,
                'arg_value':'none',
                'arg_type': param.annotation.__name__ if param.annotation and param.annotation.__name__!='_empty' else None,
                'arg_desc': None
            }
    return inputs_dict

def _format_docstring(docstring: str, inputs_dict: OrderedDict) -> str:
    variables_need_to_replace = list(set(re.findall(r'{(.*?)}', docstring if docstring else '')))
    if variables_need_to_replace and all(var in inputs_dict for var in variables_need_to_replace):
        return docstring.format(**{k: inputs_dict[k]['arg_value'] for k in variables_need_to_replace})
    return docstring
def _parse_and_format_docstring(func: Callable, inputs_dict: OrderedDict) -> (dict, dict):
    docstring = _format_docstring(func.__doc__, inputs_dict)
    parsed_results = parse_docstring(docstring)
    type_hints_results = get_type_hints(func)
    if 'input_args' not in parsed_results or len(parsed_results['input_args'])==0:
        for k, v in inputs_dict.items():
            parsed_results['input_args'].append({
                'arg_name': k,
                'arg_type': v['arg_type'],
                'arg_desc': v['arg_desc'],
                'arg_value': v['arg_value'] if 'arg_value' in v else None
            })
    else:
        for idx in range(len(parsed_results['input_args'])):
            item=parsed_results['input_args'][idx]
            arg_name=item['arg_name']
            arg_type = None if item['arg_type'] in ['_empty','Unknown'] else item['arg_type']
            arg_desc = item['arg_desc']
            if arg_name in inputs_dict:
                inputs_dict[arg_name]['arg_type']=arg_type if not inputs_dict[arg_name]['arg_type'] else inputs_dict[arg_name]['arg_type']
                inputs_dict[arg_name]['arg_desc']=arg_desc
            if arg_name in type_hints_results and type_hints_results[arg_name].__name__ not in  ['','_empty','Unknown']:
                if type_hints_results[arg_name].__name__ not in ['','_empty','Unknown']:
                    inputs_dict[arg_name]['arg_type']=type_hints_results[arg_name].__name__



    return parsed_results, type_hints_results

def _update_parsed_results(parsed_results: dict, inputs_dict: OrderedDict, type_hints_results: dict):
    inputs_dict_keys = list(inputs_dict.keys())
    for idx, item in enumerate(parsed_results['input_args']):
        if item['arg_name'] in inputs_dict_keys:
            ref = inputs_dict[item['arg_name']]
            if ref['arg_type']:
                parsed_results['input_args'][idx]['arg_type'] = ref['arg_type']
            inputs_dict_keys.remove(item['arg_name'])
        if not item['arg_type'] and item['arg_name'] in type_hints_results:
            parsed_results['input_args'][idx]['arg_type'] = type_hints_results[item['arg_name']].__name__
    for k in inputs_dict_keys:
        if k in type_hints_results:
            parsed_results['input_args'].append({'arg_name': k, 'arg_type': type_hints_results[k].__name__})


def get_input_dict(func):
    """

    Args:
        func: 函數

    Returns: input_dict

    """
    inputs_dict = _generate_inputs_dict(func)

    # 格式化並解析 docstring
    parsed_results, type_hints_results = _parse_and_format_docstring(func, inputs_dict)
    _update_parsed_results(parsed_results, inputs_dict, type_hints_results)
    return parsed_results


