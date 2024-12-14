from huggingface_hub import InferenceClient,AsyncInferenceClient
import os
import json
import asyncio
import glob
import copy
from tenacity import retry, wait_random_exponential, stop_after_attempt
# from dotenv import load_dotenv
from paradoxism import context
from paradoxism.context import *
from paradoxism.utils.tokens_utils import *
from paradoxism.llm.base import *

os.environ["HUGGINGFACEHUB_API_TOKEN"]='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'

cxt = context._context()
__all__ = ["HuggingfaceClient"]

class HuggingfaceClient(LLMClient):
    def __init__(self, model="meta-llama/Meta-Llama-3-8B-Instruct", tools=None):
        api_key = os.environ["HUGGINGFACEHUB_API_TOKEN"]
        super().__init__(api_key, model, tools)
        self.client = InferenceClient(self.model,token=os.environ["HUGGINGFACEHUB_API_TOKEN"])
        self.aclient =AsyncInferenceClient(self.model,token=os.environ["HUGGINGFACEHUB_API_TOKEN"])
        # self.client._custom_headers['Accept-Language'] = 'zh-TW'
        # self.aclient._custom_headers['Accept-Language'] = 'zh-TW'
        self.max_tokens = -1

        # if model in self.model_info:
        #     self.max_tokens = self.model_info[model]["max_token"]
        #     print(f"Model: {self.model}, Max Tokens: {self.max_tokens}")
        # else:
        #     print('{0} is not valid model!'.format(model))
        self.params = {'temperature': 1}


    def chat_completion_request(self, message_with_context, parameters=None, stream=False, use_tool=True):
        if not parameters:
            parameters = self.params
        if 'max_tokens' in parameters and parameters['max_tokens'] != "NOT_GIVEN":
            parameters['max_tokens'] = int(parameters['max_tokens'])

        return self.client.chat_completion(
            messages=message_with_context,
            max_tokens=parameters.get('max_tokens'),
            temperature=parameters.get('temperature'),

        )


    async def async_chat_completion_request(self, message_with_context, parameters=None, stream=False, use_tool=True):
        if not parameters:
            parameters = self.params
        if 'max_tokens' in parameters and parameters['max_tokens'] != NOT_GIVEN:
            parameters['max_tokens'] = int(parameters['max_tokens'])

        return await self.aclient.chat.completions.create(
            model=self.model,
            messages=message_with_context,
            temperature=parameters.get('temperature'),
            top_p=parameters.get('top_p'),
            n=parameters.get('n', 1),
            max_tokens=parameters.get('max_tokens', NOT_GIVEN),
            presence_penalty=parameters.get('presence_penalty'),
            frequency_penalty=parameters.get('frequency_penalty'),
            stream=stream,
            tools=self.tools if use_tool and self.model != 'gpt-35-turbo' else NOT_GIVEN,
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
            message_with_context = self.parent.get_context(str(user_input), self.max_tokens)

        res = self.chat_completion_request(message_with_context, stream=True, use_tool=use_tool)
        partial_words = ''
        delta=''
        tool_calls = []
        for chunk in res:
            if chunk.choices and chunk.choices[0].delta:

                finish_reason = chunk.choices[0].finish_reason

                if chunk.choices[0].delta.content:
                    partial_words += chunk.choices[0].delta.content
                    yield chunk.choices[0].delta.content,partial_words

                if chunk.choices[0].delta.tool_calls:
                    for tool_call in chunk.choices[0].delta.tool_calls:
                        index = tool_call.index
                        if index == len(tool_calls):
                            tool_calls.append({})
                        if tool_call.id:
                            tool_calls[index]['id'] = tool_call.id
                            tool_calls[index]['type'] = 'function'
                        if tool_call.function:
                            if 'function' not in tool_calls[index]:
                                tool_calls[index]['function'] = {}
                            if 'name' not in tool_calls[index]['function'] and tool_call.function.name:
                                tool_calls[index]['function']['name'] = tool_call.function.name
                                # self.update_status('使用工具:{0}...'.format(tool_call.function.name))
                                tool_calls[index]['function']['arguments'] = ''
                            if tool_call.function.arguments:
                                tool_calls[index]['function']['arguments'] += (
                                    tool_call.function.arguments)

        if finish_reason=='length':
            message_with_context = self.parent.get_context('從上次中斷處繼續，若中斷點位於列表中則從該列表開頭處繼續', self.max_tokens)
            continue_res = self.post_streaming_chat(message_with_context, use_tool=True)
            message_with_context.pop(-1)
            while True:
                try:
                    delta, partial_words = next(second_res)
                    yield delta, partial_words
                except StopIteration:
                    break

        while len(tool_calls) > 0:
            current_history.append({
                'role': 'assistant',
                'content': "None",
                'tool_calls': tool_calls
            })

            for tool_call in tool_calls:
                tool_call_id = tool_call['id']
                tool_function_name = tool_call['function']['name']
                function_to_call = get_tool(tool_function_name)
                function_args = json.loads(tool_call['function']['arguments'])
                function_args['memory_storage'] = {}  # memory_storage
                function_results = function_to_call(**function_args)
                current_history.append({
                    "role": "tool",
                    "tool_call_id": tool_call_id,
                    "name": tool_function_name,
                    "content": function_results
                })
            tool_calls = []
            message_with_context = self.parent.get_context(user_input, self.max_tokens)
            message_with_context.pop(-1)
            second_res = self.post_streaming_chat(message_with_context, use_tool=True)
            while True:
                try:
                    delta,partial_words = next(second_res)
                    yield delta,partial_words
                except StopIteration:
                    break
            current_history.add_message('assistant',partial_words)
            return delta,partial_words

        return delta,partial_words

    def post_chat(self, user_input, use_tool=True):
        current_history = self.parent.get_history(self.parent.active_history_id)
        if isinstance(user_input, list) and all([isinstance(d, dict) for d in user_input]):
            message_with_context = user_input
        else:
            message_with_context = self.parent.get_context(str(user_input), self.max_tokens)

        res = self.chat_completion_request(message_with_context, stream=False, use_tool=use_tool)

        if res.choices and res.choices[0].message:
            finish_reason = res.choices[0].finish_reason
            if res.choices[0].message.content:
                return res.choices[0].message.content

            if res.choices[0].message.tool_calls:
                tool_calls = res.choices[0].message.tool_calls

            if finish_reason == 'length':
                message_with_context = self.parent.get_context( '從上次中斷處繼續，若中斷點位於列表中則從該列表開頭處繼續', self.max_tokens)
                continue_res = self.post_chat(message_with_context, use_tool=True)
                message_with_context.pop(-1)
                while True:
                    try:
                        delta, partial_words = next(second_res)
                        yield delta, partial_words
                    except StopIteration:
                        break

            partial_word=''
            while len(tool_calls) > 0:
                current_history.append({
                    'role': 'assistant',
                    'content': "None",
                    'tool_calls': tool_calls
                })

                for tool_call in tool_calls:
                    # If true the model will return the name of the tool / function to call and the argument(s)
                    tool_call_id = tool_call.id
                    tool_function_name = tool_call.function.name
                    # Step 3: Call the function and retrieve results. Append the results to the messages list.
                    function_to_call = get_tool(tool_function_name)
                    function_args = json.loads(tool_call.function.arguments)
                    function_args['memory_storage'] = {}  # memory_storage
                    function_results = function_to_call(**function_args)
                    current_history.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name":  tool_call.function.name,
                        "content": function_results
                    })
                tool_calls = []
                message_with_context = self.parent.get_context(user_input, self.max_tokens)
                message_with_context.pop(-1)
                second_res = self.chat_completion_request(message_with_context, stream=False, use_tool=False)
                partial_word+='\n\n'+ second_res.choices[0].message.content
            current_history.add_message('assistant', partial_words)
            return partial_word
