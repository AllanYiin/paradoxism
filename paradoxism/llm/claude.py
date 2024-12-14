import anthropic
from anthropic import Client,AsyncClient,NOT_GIVEN,NotGiven,Anthropic,AsyncAnthropic
from anthropic.types import TextBlock,ToolUseBlock
import os
import json
import asyncio
import builtins
import glob
import copy
from tenacity import retry, wait_random_exponential, stop_after_attempt
from paradoxism import context
from paradoxism.context import *
from paradoxism.llm.base import *

cxt = context._context()
__all__ = ["ClaudeClient"]

class ClaudeClient(LLMClient):
    def __init__(self, model='claude-3-5-sonnet-20240620', tools=None):
        api_key = os.environ["ANTHROPIC_API_KEY"]
        super().__init__(api_key, model, tools)
        self.client = Anthropic()
        self.aclient = AsyncAnthropic()
        self.tools=[self.openai_tools_to_claude_tools(t) for t in self.tools] if len(self.tools)>0 else []
        # self.client._custom_headers['Accept-Language'] = 'zh-TW'
        # self.aclient._custom_headers['Accept-Language'] = 'zh-TW'

        self.model_info = eval(open('./model_infos.json', encoding="utf-8").read())['anthropic']
        if model in self.model_info:
            self.max_tokens = self.model_info[model]["max_token"]
            print(f"Model: {self.model}, Max Tokens: {self.max_tokens}")
        else:
            self.max_tokens=4096
            print('{0} is not valid model!'.format(model))
        self.params = {'top_p': 1, 'temperature': 1, 'top_k': 1}

    def openai_tools_to_claude_tools(self,openai_tool):
        # 提取OpenAI格式的相關資料
        function_name = openai_tool["function"]["name"]
        description = openai_tool["function"]["description"]
        parameters = openai_tool["function"]["parameters"]

        # 轉換為Claude格式
        claude_tool = {
            "name": function_name,
            "description": description,
            "input_schema": {
                "type": parameters["type"],
                "properties": parameters["properties"],
                "required": parameters["required"]
            }
        }

        return claude_tool
    # @retry(wait=wait_random_exponential(multiplier=1, max=40), stop=stop_after_attempt(3))
    def chat_completion_request(self, message_with_context, parameters=None, stream=False, use_tool=True):
        if not parameters:
            parameters = self.params
        # if 'max_tokens' in parameters and parameters['max_tokens'] != "NOT_GIVEN":
        #     parameters['max_tokens'] = int(parameters['max_tokens'])
        system_message=self.parent.system_prompt#."你是一個萬能的文字幫手"
        if message_with_context and message_with_context[0]["role"]=="system":
            system_message=message_with_context.pop(0)["content"]

        return self.client.messages.create(
            model=self.model,
            system=system_message,
            messages=message_with_context,
            temperature=builtins.min(parameters.get('temperature',0.5),1),
            max_tokens=parameters.get('max_tokens', self.max_tokens),
            stream=stream,
            tools=self.tools if use_tool else []
        )

    # @retry(wait=wait_random_exponential(multiplier=1, max=40), stop=stop_after_attempt(3))
    async def async_chat_completion_request(self, message_with_context, parameters=None, stream=False, use_tool=True):
        system_message=self.parent.system_prompt
        if message_with_context and message_with_context[0]["role"]=="system":
            system_message=message_with_context.pop(0)["content"]

        return await self.aclient.messages.create(
            model=self.model,
            system=system_message,
            messages=message_with_context,
            temperature=builtins.min(parameters.get('temperature'), 1),
            top_p=parameters.get('top_p',NOT_GIVEN),
            tokp=parameters.get('n', 1),
            max_tokens=parameters.get('max_tokens', 8192 if self.model == "claude-3-5-sonnet-20240620" else 4096),
            stream=stream,
            tools=self.tools if use_tool else NOT_GIVEN,
            tool_choice=NOT_GIVEN if not use_tool or self.tools == NOT_GIVEN else "auto"
        )

    async def generate_summary(self, content):
        prompt = f"請將以下內容總結為筆記，所有重要知識點以及關鍵資訊應該盡可能保留:\n\n{content}"
        message_with_context = [
            {"role": "system", "content": "你是一個萬能的文字幫手"},
            {"role": "user", "content": prompt}
        ]
        params=copy.deepcopy(self.params)
        params['temperature']=0.5
        summary = await self.async_chat_completion_request(message_with_context,stream=False,use_tool=False)
        return summary

    def post_streaming_chat(self, user_input, use_tool=True):
        current_history = self.parent.get_history(self.parent.active_history_id)
        if isinstance(user_input, list) and all([isinstance(d, dict) for d in user_input]):
            message_with_context = user_input
        else:
            message_with_context = self.parent.get_context(None if user_input is None else str(user_input), self.max_tokens)

        res = self.chat_completion_request(message_with_context, stream=True, use_tool=use_tool)
        partial_words = ''
        partial_input_json=''
        finish_reason=None
        current_id=None
        delta=''
        tool_calls = {}
        for chunk in res:
            #print(chunk, flush=True)
            if chunk :

                if chunk.type=='message_delta' and hasattr(chunk,'delta')and hasattr(chunk.delta,'stop_reason'):
                    finish_reason = chunk.delta.stop_reason

                if chunk.type=='content_block_delta' :
                    if hasattr(chunk,'delta'):
                        if chunk.delta.type=='text_delta':
                            partial_words +=chunk.delta.text
                            yield chunk.delta.text,partial_words
                        elif chunk.delta.type=='input_json_delta':
                            partial_input_json+=chunk.delta.partial_json
                            tool_calls[current_id].input=partial_input_json

                elif chunk.type=='content_block_start'  :
                    if chunk.content_block.type=='tool_use':
                        current_id=chunk.content_block.id
                        tool_calls[current_id]=chunk.content_block
        while finish_reason == 'max_tokens':
            message_with_context = self.parent.get_context(
                '從上次中斷處繼續，若中斷點位於列表中則從該列表開頭處繼續', self.max_tokens)
            continue_res = self.post_streaming_chat(message_with_context, use_tool=True)
            partial_words+='\n\n'
            while True:
                try:
                    delta, continue_partial_words = next(continue_res)
                    partial_words+=delta
                    yield delta, partial_words
                except StopIteration:
                    break
            #finish_reason = continue_res.stop_reason

        while len(tool_calls) > 0:
            current_history.append({
                'role': 'assistant',
                'content': tool_calls
            })

            for tool_use in tool_calls.values():
                # If true the model will return the name of the tool / function to call and the argument(s)
                tool_name = tool_use.name
                tool_input = tool_use.input

                # Step 3: Call the function and retrieve results. Append the results to the messages list.
                function_to_call = get_tool(tool_name)
                function_args = json.loads(tool_input)
                function_args['memory_storage'] = {}  # memory_storage
                function_results = function_to_call(**function_args)

                current_history.append({
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": tool_use.id,
                            "content": str(function_results),
                        }
                    ]
                })
            del tool_calls[tool_use.id]
            message_with_context = self.parent.get_context(None, self.max_tokens)
            second_res = self.post_streaming_chat(message_with_context,  use_tool=use_tool)
            partial_words += '\n\n'
            second_partial_words=''
            while True:
                try:
                    delta, second_partial_words = next(second_res)
                    partial_words += delta
                    yield delta, partial_words
                except StopIteration:
                    break
            current_history.add_message('assistant', second_partial_words)
            #tool_calls = [block for block in second_res.content if block.type == "tool_use"]
            #finish_reason = second_res.stop_reason

        yield delta,partial_words

    def post_chat(self, user_input, use_tool=True):
        current_history = self.parent.get_history(self.parent.active_history_id)
        if isinstance(user_input, list) and all([isinstance(d, dict) for d in user_input]):
            message_with_context = user_input
        else:
            message_with_context = self.parent.get_context(None if user_input is None else str(user_input), self.max_tokens)

        res = self.chat_completion_request(message_with_context, stream=False, use_tool=use_tool)
        tool_calls=[]
        if res :
            finish_reason = res.stop_reason
            if res.content and finish_reason in ('end_turn','stop_sequence'):
                return res.content

            tool_calls=[block for block in res.content if block.type == "tool_use"]
            partial_words =res.content
            while finish_reason == 'max_tokens':
                message_with_context = self.parent.get_context(
                    '從上次中斷處繼續，若中斷點位於列表中則從該列表開頭處繼續', self.max_tokens)
                continue_res = self.post_chat(message_with_context, use_tool=True)


                finish_reason = continue_res.stop_reason
                if continue_res.content:
                    for c in continue_res.content:
                        is_match=False
                        for c_ in partial_words:
                            if c.__class__.__name__==c_.__class__.__name__:
                                is_match=True
                                if isinstance(c,TextBlock):
                                    c_.text+=c.text
                        if not is_match:
                            partial_words.append(c)

            while finish_reason== "tool_use":
                current_history.append({
                    'role': 'assistant',
                    'content': res.content
                })

                for tool_use in tool_calls:
                    # If true the model will return the name of the tool / function to call and the argument(s)
                    tool_name = tool_use.name
                    tool_input = tool_use.input

                    # Step 3: Call the function and retrieve results. Append the results to the messages list.
                    function_to_call = get_tool(tool_name)
                    function_args =tool_input
                    function_args['memory_storage'] = {}  # memory_storage
                    function_results = function_to_call(**function_args)

                    current_history.append({
                        "role":"user",
                        "content": [
                            {
                                "type": "tool_result",
                                "tool_use_id": tool_use.id,
                                "content": str(function_results),
                            }
                        ]
                    })

                message_with_context = self.parent.get_context(None, self.max_tokens)
                second_res = self.chat_completion_request(message_with_context, stream=False, use_tool=use_tool)
                current_history.add_message('assistant', second_res.content)
                partial_words.extend(second_res.content)
                tool_calls = [block for block in second_res.content if block.type == "tool_use"]
                finish_reason = second_res.stop_reason

            return partial_words