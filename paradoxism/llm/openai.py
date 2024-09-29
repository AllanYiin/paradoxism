import openai
from openai import OpenAI, AsyncOpenAI, AzureOpenAI, AsyncAzureOpenAI
from openai._types import NotGiven, NOT_GIVEN
import os
import json
import glob
import copy
from tenacity import retry, wait_random_exponential, stop_after_attempt
# from dotenv import load_dotenv
from paradoxism import context
from paradoxism.context import *
from paradoxism.common import *
from paradoxism.utils.tokens_utils import *
from paradoxism.llm.base import *
from concurrent.futures import ThreadPoolExecutor, as_completed

cxt = context._context()
__all__ = ["OpenAIClient", 'AzureClient']


class OpenAIClient(LLMClient):
    def __init__(self, model='gpt-4o', tools=None):
        api_key = os.environ["OPENAI_API_KEY"]
        super().__init__(api_key, model, tools)
        self.client = OpenAI(api_key=api_key)
        self.aclient = AsyncOpenAI(api_key=api_key)
        self.client._custom_headers['Accept-Language'] = 'zh-TW'
        self.aclient._custom_headers['Accept-Language'] = 'zh-TW'
        self.max_tokens = -1
        self.model_info = {
            # openai
            "gpt-3.5-turbo": {
                "endpoint": 'https://api.openai.com/v1/chat/completions',
                "max_token": 4096
            },
            "gpt-4-0125-preview": {
                "endpoint": 'https://api.openai.com/v1/chat/completions',
                "max_token": 128000
            },
            "gpt-4-1106-preview": {
                "endpoint": 'https://api.openai.com/v1/chat/completions',
                "max_token": 128000
            },
            "gpt-4-vision-preview": {
                "endpoint": 'https://api.openai.com/v1/chat/completions',
                "max_token": 128000
            },
            "gpt-4": {
                "endpoint": 'https://api.openai.com/v1/chat/completions',
                "max_token": 8192
            },

            "gpt-3.5-turbo-0613": {
                "endpoint": 'https://api.openai.com/v1/chat/completions',
                "max_token": 4096
            },
            "gpt-3.5-turbo-16k-0613": {
                "endpoint": 'https://api.openai.com/v1/chat/completions',
                "max_token": 16385
            },
            "gpt-3.5-turbo-1106": {
                "endpoint": 'https://api.openai.com/v1/chat/completions',
                "max_token": 16385
            },

            "gpt-4-0613": {
                "endpoint": 'https://api.openai.com/v1/chat/completions',
                "max_token": 8192
            },
            "gpt-4-0314": {
                "endpoint": 'https://api.openai.com/v1/chat/completions',
                "max_token": 8192
            },

            "gpt-4-32k": {
                "endpoint": 'https://api.openai.com/v1/chat/completions',
                "max_token": 32768
            },

            "gpt-4-32k-0314": {
                "endpoint": 'https://api.openai.com/v1/chat/completions',
                "max_token": 32768
            },
            "gpt-4-128k": {
                "endpoint": 'https://api.openai.com/v1/chat/completions',
                "max_token": 128000
            },
            "gpt-4o": {
                "endpoint": 'https://api.openai.com/v1/chat/completions',
                "max_token": 128000
            },
            "gpt-4o-mini": {
                "endpoint": 'https://api.openai.com/v1/chat/completions',
                "max_token": 128000
            },

        }
        if model in self.model_info:
            self.max_tokens = self.model_info[model]["max_token"]
            print(f"Model: {self.model}, Max Tokens: {self.max_tokens}")
        else:
            print('{0} is not valid model!'.format(model))
        self.params = {'top_p': 1, 'temperature': 1, 'top_k': 1, 'presence_penalty': 0,
                       'frequency_penalty': 0}

    @retry(wait=wait_random_exponential(multiplier=1, max=40), stop=stop_after_attempt(3))
    def chat_completion_request(self, message_with_context, parameters=None, stream=False, use_tool=True):
        if not parameters:
            parameters = self.params
        if 'max_tokens' in parameters and parameters['max_tokens'] != "NOT_GIVEN":
            parameters['max_tokens'] = int(parameters['max_tokens'])

        return self.client.chat.completions.create(
            model=self.model,
            messages=message_with_context,
            temperature=parameters.get('temperature'),
            top_p=parameters.get('top_p'),
            n=parameters.get('n', 1),
            max_tokens=parameters.get('max_tokens', NOT_GIVEN),
            presence_penalty=parameters.get('presence_penalty'),
            frequency_penalty=parameters.get('frequency_penalty'),
            stream=stream,
            response_format=NOT_GIVEN if not json_output else {"type": "json_object"},
            tools=self.tools if use_tool and self.model != 'gpt-35-turbo' else NOT_GIVEN,
            tool_choice=NOT_GIVEN if not use_tool or self.tools == NOT_GIVEN else "auto",
            parallel_tool_calls= True if use_tool and self.model != 'gpt-35-turbo' else NOT_GIVEN,
        )

    @retry(wait=wait_random_exponential(multiplier=1, max=40), stop=stop_after_attempt(3))
    async def async_chat_completion_request(self, message_with_context, parameters=None, stream=False, use_tool=True,json_output=False):
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
            response_format=NOT_GIVEN if not json_output else {"type": "json_object"},
            tools=self.tools if use_tool and self.model != 'gpt-35-turbo' else NOT_GIVEN,
            tool_choice=NOT_GIVEN if not use_tool or self.tools == NOT_GIVEN else "auto",
            parallel_tool_calls= True if use_tool and self.model != 'gpt-35-turbo' else NOT_GIVEN,
        )

    async def generate_summary(self, content):
        prompt = f"請將以下內容總結為筆記，所有重要知識點以及關鍵資訊應該盡可能保留:\n\n{content}"
        message_with_context = [
            {"role": "system", "content": "你是一個萬能的文字幫手"},
            {"role": "user", "content": prompt}
        ]
        params = copy.deepcopy(self.params)
        params['temperature'] = 0.5
        summary = await self.async_chat_completion_request(message_with_context, stream=False, use_tool=False)
        return summary

    def post_streaming_chat(self, user_input, use_tool=True,json_output=False):
        current_history = self.parent.get_history(self.parent.active_history_id)
        if isinstance(user_input, list) and all([isinstance(d, dict) for d in user_input]):
            message_with_context = user_input
        else:
            message_with_context = self.parent.get_context(None if user_input is None else str(user_input), self.max_tokens)

        res = self.chat_completion_request(message_with_context, stream=True, use_tool=use_tool,json_output=json_output)
        partial_words = ''
        delta = ''
        tool_calls = []
        for chunk in res:
            if chunk.choices and chunk.choices[0].delta:

                finish_reason = chunk.choices[0].finish_reason

                if chunk.choices[0].delta.content:
                    partial_words += chunk.choices[0].delta.content
                    yield chunk.choices[0].delta.content, partial_words

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

        if finish_reason == 'length':

            message_with_context = self.parent.get_context('從上次中斷處繼續，若中斷點位於列表中則從該列表開頭處繼續',elf.max_tokens)
            message_with_context.insert(-2,{"role":"assistant","content":partial_words})
            continue_res = self.post_streaming_chat(message_with_context, use_tool=True)
            self.parent.active_history.messages.pop(-1)
            while True:
                try:
                    delta, partial_words2 = next(continue_res)
                    yield delta, partial_words + partial_words2
                except StopIteration:
                    break
            partial_words += partial_words2
        threads = []

        while len(tool_calls) > 0:
            current_history.append({
                'role': 'assistant',
                'content': "None",
                'tool_calls': tool_calls
            })
            for tool_call in tool_calls:
                tool_call_id = tool_call['id']
                tool_function_name = tool_call['function']['name']
                # Step 3: Call the function and retrieve results. Append the results to the messages list.
                # function_to_call = get_tool(tool_function_name)
                function_args = tool_call['function']['arguments']
                th = self.parent.executor.submit(self.run_tool, tool_call_id, tool_function_name, function_args,
                                                 self.parent.short_memory)
                threads.append(th)
            for future in as_completed(threads):
                try:
                    tool_id, tool_name, tool_results = future.result()
                    current_history.append({
                        "role": "tool",
                        "tool_call_id": tool_id,
                        "name": tool_name,
                        "content": tool_results
                    })

                except Exception as e:
                    print(f"Error processing URL: {e}", flush=True)

            tool_calls = []

            second_res = self.post_streaming_chat(None, use_tool=True)
            while True:
                try:
                    delta, partial_words = next(second_res)
                    partial_words=self.monitor_and_replace_placeholder(partial_words)
                    yield delta, partial_words

                except StopIteration:
                    break
                except Exception as e:
                    PrintException()
                # except StopIteration:
                #     second_res.close()
                #     break
                # except GeneratorExit:
                #     second_res.close()
                # finally:
            current_history.add_message('assistant', partial_words)
            yield delta, partial_words

    def post_chat(self, user_input, use_tool=True,json_output=False):

        current_history = self.parent.get_history(self.parent.active_history_id)
        if isinstance(user_input, list) and all([isinstance(d, dict) for d in user_input]):
            message_with_context = user_input
        else:
            message_with_context = self.parent.get_context(None if user_input is None else str(user_input), self.max_tokens)

        res = self.chat_completion_request(message_with_context, stream=False, use_tool=use_tool,json_output=json_output)

        if res.choices and res.choices[0].message:
            finish_reason = res.choices[0].finish_reason
            if res.choices[0].message.content:
                return res.choices[0].message.content

            if res.choices[0].message.tool_calls:
                tool_calls = res.choices[0].message.tool_calls

            if finish_reason == 'length':
                message_with_context = self.parent.get_context(
                    '從上次中斷處繼續，若中斷點位於列表中則從該列表開頭處繼續', self.max_tokens)
                continue_res = self.post_chat(message_with_context, use_tool=True)
                message_with_context.pop(-1)
                while True:
                    try:
                        delta, partial_words = next(second_res)
                        yield delta, partial_words
                    except StopIteration:
                        break

            partial_word = ''
            while len(tool_calls) > 0:
                current_history.append({
                    'role': 'assistant',
                    'content': "None",
                    'tool_calls': tool_calls
                })
                threads = []

                for tool_call in tool_calls:
                    tool_call_id = tool_call.id
                    tool_function_name = tool_call.function.name
                    # Step 3: Call the function and retrieve results. Append the results to the messages list.
                    # function_to_call = get_tool(tool_function_name)
                    function_args = tool_call.function.arguments
                    # function_args['memory_storage'] = {}  # memory_storage
                    # function_results = function_to_call(**function_args)
                    th = self.parent.executor.submit(self.run_tool, tool_call_id, tool_function_name, function_args,
                                                     self.parent.short_memory)
                    threads.append(th)
                for future in as_completed(threads):
                    try:
                        tool_id, tool_name, tool_results = future.result()
                        current_history.append({
                            "role": "tool",
                            "tool_call_id": tool_id,
                            "name": tool_name,
                            "content": tool_results
                        })

                    except Exception as e:
                        print(f"Error processing URL: {e}", flush=True)
                tool_calls = []
                # message_with_context = self.parent.get_context(None, self.max_tokens)
                second_res = self.chat_completion_request(None, stream=False, use_tool=False)
                partial_word += '\n\n' + second_res.choices[0].message.content
            current_history.add_message('assistant', partial_words)
            return partial_word


class AzureClient(LLMClient):
    def __init__(self, model='gpt-4o-auto', tools=None):
        openai.api_type='azure'
        api_key = cxt.oai[model]['api_key']
        endpoint = cxt.oai[model]['azure_endpoint']
        super().__init__(api_key, model, tools)
        self.max_tokens =cxt.oai[model]['max_tokens']

        paras = copy.deepcopy(cxt.oai[model])
        paras.pop("max_tokens")
        self.client = AzureOpenAI(**paras)

        self.aclient = AsyncAzureOpenAI(**paras)
        self.params = {'top_p': 1, 'temperature': 1, 'top_k': 1, 'presence_penalty': 0,
                       'frequency_penalty': 0}

    @retry(wait=wait_random_exponential(multiplier=1, max=40), stop=stop_after_attempt(3))
    def chat_completion_request(self, message_with_context, parameters=None, stream=False,json_output=False):
        if not parameters:
            parameters = self.params
        if 'max_tokens' in parameters and parameters['max_tokens'] != "NOT_GIVEN":
            parameters['max_tokens'] = int(parameters['max_tokens'])

        return self.client.chat.completions.create(
            model=self.model,
            messages=message_with_context,
            temperature=parameters.get('temperature'),
            top_p=parameters.get('top_p'),
            n=parameters.get('n', 1),
            max_tokens=parameters.get('max_tokens', NOT_GIVEN),
            presence_penalty=parameters.get('presence_penalty'),
            frequency_penalty=parameters.get('frequency_penalty'),
            stream=stream,
            response_format=NOT_GIVEN if not json_output else {"type": "json_object"}
        )

    @retry(wait=wait_random_exponential(multiplier=1, max=40), stop=stop_after_attempt(3))
    async def async_chat_completion_request(self, message_with_context, parameters=None, stream=False,json_output=False):
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
            response_format=NOT_GIVEN if not json_output else {"type": "json_object"}
        )

    async def generate_summary(self, content):
        prompt = f"請將以下內容總結為筆記，所有重要知識點以及關鍵資訊應該盡可能保留:\n\n{content}"
        message_with_context = [
            {"role": "system", "content": "你是一個萬能的文字幫手"},
            {"role": "user", "content": prompt}
        ]
        params = copy.deepcopy(self.params)
        params['temperature'] = 0.5
        summary = await self.async_chat_completion_request(message_with_context, stream=False, use_tool=False)
        return summary

    def post_streaming_chat(self, user_input, use_tool=True,json_output=False):
        current_history = self.parent.get_history(self.parent.active_history_id)
        if isinstance(user_input, list) and all([isinstance(d, dict) for d in user_input]):
            message_with_context = user_input
        else:
            message_with_context = self.parent.get_context(None if user_input is None else str(user_input),
                                                           self.max_tokens)

        res = self.chat_completion_request(message_with_context, stream=True, use_tool=use_tool,json_output=json_output)
        partial_words = ''
        delta = ''
        tool_calls = []
        for chunk in res:
            if chunk.choices and chunk.choices[0].delta:

                finish_reason = chunk.choices[0].finish_reason

                if chunk.choices[0].delta.content:
                    partial_words += chunk.choices[0].delta.content
                    yield chunk.choices[0].delta.content, partial_words

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

        if finish_reason == 'length':

            message_with_context = self.parent.get_context('從上次中斷處繼續，若中斷點位於列表中則從該列表開頭處繼續',
                                                           elf.max_tokens)
            message_with_context.insert(-2, {"role": "assistant", "content": partial_words})
            continue_res = self.post_streaming_chat(message_with_context, use_tool=True)
            self.parent.active_history.messages.pop(-1)
            while True:
                try:
                    delta, partial_words2 = next(continue_res)
                    yield delta, partial_words + partial_words2
                except StopIteration:
                    break
            partial_words += partial_words2
        threads = []

        while len(tool_calls) > 0:
            current_history.append({
                'role': 'assistant',
                'content': "None",
                'tool_calls': tool_calls
            })
            for tool_call in tool_calls:
                tool_call_id = tool_call['id']
                tool_function_name = tool_call['function']['name']
                # Step 3: Call the function and retrieve results. Append the results to the messages list.
                # function_to_call = get_tool(tool_function_name)
                function_args = tool_call['function']['arguments']
                th = self.parent.executor.submit(self.run_tool, tool_call_id, tool_function_name, function_args,
                                                 self.parent.short_memory)
                threads.append(th)
            for future in as_completed(threads):
                try:
                    tool_id, tool_name, tool_results = future.result()
                    current_history.append({
                        "role": "tool",
                        "tool_call_id": tool_id,
                        "name": tool_name,
                        "content": str(tool_results)
                    })

                except Exception as e:
                    print(f"Error processing URL: {e}", flush=True)

            tool_calls = []

            second_res = self.post_streaming_chat(None, use_tool=True)
            while True:
                try:
                    delta, partial_words = next(second_res)
                    partial_words=self.monitor_and_replace_placeholder(partial_words)
                    yield delta, partial_words

                except StopIteration:
                    break
                except Exception as e:
                    PrintException()
                # except StopIteration:
                #     second_res.close()
                #     break
                # except GeneratorExit:
                #     second_res.close()
                # finally:
            current_history.add_message('assistant', partial_words)
            yield delta, partial_words

    def post_chat(self, user_input, use_tool=True,json_output=False):

        current_history = self.parent.get_history(self.parent.active_history_id)
        if isinstance(user_input, list) and all([isinstance(d, dict) for d in user_input]):
            message_with_context = user_input
        else:
            message_with_context = self.parent.get_context(None if user_input is None else str(user_input),
                                                           self.max_tokens)

        res = self.chat_completion_request(message_with_context, stream=False, use_tool=use_tool,json_output=json_output)

        if res.choices and res.choices[0].message:
            finish_reason = res.choices[0].finish_reason
            if res.choices[0].message.content:
                return res.choices[0].message.content

            if res.choices[0].message.tool_calls:
                tool_calls = res.choices[0].message.tool_calls

            if finish_reason == 'length':
                message_with_context = self.parent.get_context(
                    '從上次中斷處繼續，若中斷點位於列表中則從該列表開頭處繼續', self.max_tokens)
                continue_res = self.post_chat(message_with_context, use_tool=True)
                message_with_context.pop(-1)
                while True:
                    try:
                        delta, partial_words = next(second_res)
                        yield delta, partial_words
                    except StopIteration:
                        break

            partial_word = ''
            while len(tool_calls) > 0:
                current_history.append({
                    'role': 'assistant',
                    'content': "None",
                    'tool_calls': tool_calls
                })
                threads = []

                for tool_call in tool_calls:
                    tool_call_id = tool_call.id
                    tool_function_name = tool_call.function.name
                    # Step 3: Call the function and retrieve results. Append the results to the messages list.
                    # function_to_call = get_tool(tool_function_name)
                    function_args = tool_call.function.arguments
                    # function_args['memory_storage'] = {}  # memory_storage
                    # function_results = function_to_call(**function_args)
                    th = self.parent.executor.submit(self.run_tool, tool_call_id, tool_function_name, function_args,
                                                     self.parent.short_memory)
                    threads.append(th)
                for future in as_completed(threads):
                    try:
                        tool_id, tool_name, tool_results = future.result()
                        current_history.append({
                            "role": "tool",
                            "tool_call_id": tool_id,
                            "name": tool_name,
                            "content": str(tool_results)
                        })

                    except Exception as e:
                        print(f"Error processing URL: {e}", flush=True)
                tool_calls = []
                # message_with_context = self.parent.get_context(None, self.max_tokens)
                second_res = self.chat_completion_request(None, stream=False, use_tool=False)
                partial_word += '\n\n' + second_res.choices[0].message.content
            current_history.add_message('assistant', partial_words)
            return partial_word
