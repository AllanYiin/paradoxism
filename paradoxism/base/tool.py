import openai
from functools import wraps
from utils.regex_utils  import extract_json
import threading
from paradoxism.base.agent import _thread_local,LLMClient


class BaseTool:
    def __init__(self, llm_model="gpt-4o", system_prompt="你是一個擅長工具調用的超級幫手"):
        self.llm_model = llm_model
        self.system_prompt = system_prompt
        self.llm_client =LLMClient(model=self.llm_model, system_prompt='你是一個穩定可信賴的工具，直接輸出無須解釋', temperature=0.1)
        self.base_func=None

    def generate_tool_args(self, tool_name, docstring, input_kwargs):
        """
        基於工具的描述和現有的上下文，透過 LLM 生成工具調用所需的引數。
        Args:
            tool_name: 工具名稱
            docstring: 工具的 docstring，描述工具功能和參數
            input_kwargs: 用戶提供的引數（dict）
        Returns:
            生成的工具引數 dict
        """
        prompt = f"""
        你將調用一個工具，工具名稱是 "{tool_name}"，這個工具的功能以及所需引數如下：
        {docstring}
        請參考目前執行階段所收集之上下文信息：
        {input_kwargs}
        請基於工具的描述、引數的描述和上下文信息，以json格式生成最終的工具引數。
        """

        response = self.llm_client.client.chat.completions.create(
            model=self.llm_model,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}

        )
        tool_args =response.choices[0].message.content
        print('tool_args生成完畢!\n', tool_args, flush=True)

        return tool_args

    def __call__(self,input_kwargs,**kwargs):
        """
        收集上下文並生成最終的工具引數，然後調用原始函數。
        Args:
            tool_func: 被 @tool 裝飾的函數
            input_kwargs: 用戶輸入的引數（dict）

        Returns:
            工具函數的執行結果
        """
        tool_name =self.base_func.__name__
        docstring = self.base_func.__doc__ or ""
        # 生成引數
        tool_args = self.generate_tool_args(tool_name, docstring, input_kwargs)

        # 調用原始工具函數
        result = self.base_func.__call__(**eval(tool_args))
        print(f'工具{tool_name}調用完畢')
        return result


def tool():
    """
    @tool 裝飾器，用於將函數封裝為工具，並使用 LLM 來生成輸入引數。
    """

    def decorator(func):
        # 創建 BaseTool 實例
        base_tool = BaseTool()
        base_tool.base_func = func
        func.client = base_tool.llm_client
        func.static_instruction = func.__doc__ or ""
        _thread_local.static_instruction = func.__doc__ or ""
        _thread_local.llm_client = base_tool.llm_client


        @wraps(func)
        def wrapper(input_kwargs):
            """
            使用 BaseTool 來生成引數並調用函數，input_kwargs 為 dict 形式。
            """
            # 通過 BaseTool 來生成最終的引數並調用工具函數
            return base_tool(input_kwargs)

        return wrapper

    return decorator
