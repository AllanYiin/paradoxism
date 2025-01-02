import inspect
from collections import OrderedDict
from typing import Callable, Dict, Any, Tuple
from typing import get_type_hints
import re
from paradoxism.utils.docstring_utils import parse_docstring

__all__ = ["get_input_dict"]

def _generate_inputs_dict(func: Callable, *args, **kwargs) -> OrderedDict:
    """Generate a dictionary of function input details."""
    inputs_dict = OrderedDict()
    signature = inspect.signature(func)

    for i, (param_name, param) in enumerate(signature.parameters.items()):
        param_type = param.annotation.__name__ if param.annotation and param.annotation != inspect.Parameter.empty else None

        if i < len(args):
            inputs_dict[param_name] = {
                'arg_name': param_name,
                'arg_value': args[i],
                'arg_type': param_type,
                'arg_desc': None
            }
        elif param_name in kwargs:
            inputs_dict[param_name] = {
                'arg_name': param_name,
                'arg_value': kwargs[param_name],
                'arg_type': param_type,
                'arg_desc': None
            }
        elif param.default is not inspect.Parameter.empty:
            inputs_dict[param_name] = {
                'arg_name': param_name,
                'arg_value': str(param.default),
                'arg_type': param_type,
                'arg_desc': None
            }
        else:
            inputs_dict[param_name] = {
                'arg_name': param_name,
                'arg_value': 'none',
                'arg_type': param_type,
                'arg_desc': None
            }

    return inputs_dict

def _format_docstring(docstring: str, inputs_dict: OrderedDict) -> str:
    """Format the docstring with values from the inputs dictionary."""
    if not docstring:
        return ""

    variables_to_replace = set(re.findall(r'{(.*?)}', docstring))
    if variables_to_replace.issubset(inputs_dict.keys()):
        formatted_docstring = docstring.format(
            **{key: inputs_dict[key]['arg_value'] for key in variables_to_replace}
        )
        return formatted_docstring

    return docstring

def _parse_and_format_docstring(func: Callable, inputs_dict: OrderedDict) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Parse and format the docstring for a given function."""
    docstring = _format_docstring(func.__doc__, inputs_dict)
    parsed_results = parse_docstring(docstring)
    type_hints = get_type_hints(func)

    if 'input_args' not in parsed_results or not parsed_results['input_args']:
        for arg_name, details in inputs_dict.items():
            parsed_results.setdefault('input_args', []).append({
                'arg_name': arg_name,
                'arg_type': details['arg_type'],
                'arg_desc': details['arg_desc'],
                'arg_value': details.get('arg_value')
            })
    else:
        for input_arg in parsed_results['input_args']:
            arg_name = input_arg['arg_name']
            if arg_name in inputs_dict:
                inputs_dict[arg_name]['arg_type'] = inputs_dict[arg_name]['arg_type'] or input_arg.get('arg_type')
                inputs_dict[arg_name]['arg_desc'] = input_arg.get('arg_desc')

            if arg_name in type_hints:
                inputs_dict[arg_name]['arg_type'] = type_hints[arg_name].__name__

    return parsed_results, type_hints

def _update_parsed_results(parsed_results: Dict[str, Any], inputs_dict: OrderedDict, type_hints: Dict[str, Any]):
    """Update the parsed results with type hints and additional information."""
    for input_arg in parsed_results.get('input_args', []):
        arg_name = input_arg['arg_name']
        if arg_name in inputs_dict:
            ref = inputs_dict[arg_name]
            input_arg['arg_type'] = ref['arg_type'] or input_arg.get('arg_type')

    for remaining_arg in set(inputs_dict.keys()) - {arg['arg_name'] for arg in parsed_results.get('input_args', [])}:
        parsed_results.setdefault('input_args', []).append({
            'arg_name': remaining_arg,
            'arg_type': type_hints.get(remaining_arg, inspect.Parameter.empty).__name__,
            'arg_desc': None
        })

def get_input_dict(func: Callable) -> Dict[str, Any]:
    """Retrieve a structured dictionary of input arguments for a given function.

    Args:
        func (Callable): The function to analyze.

    Returns:
        Dict[str, Any]: A dictionary containing details about the function's input arguments.
    """
    inputs_dict = _generate_inputs_dict(func)
    parsed_results, type_hints = _parse_and_format_docstring(func, inputs_dict)
    _update_parsed_results(parsed_results, inputs_dict, type_hints)
    return parsed_results
