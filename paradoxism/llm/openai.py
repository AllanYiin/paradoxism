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
from paradoxism.llm.base import *
from concurrent.futures import ThreadPoolExecutor, as_completed


__all__ = ["OpenAIClient", 'AzureClient']


class OpenAIClient(LLMClient):
    def __init__(self, model='gpt-4o', system_prompt='你是一個萬能的人工智能助理', temperature=0.2, **kwargs):
        """
        初始化 OpenAIClient 類別。

        參數:
            model (str): 使用的模型名稱，預設為 'gpt-4o'。
            system_prompt (str): 系統提示詞，預設為 '你是一個萬能的人工智能助理'。
            temperature (float): 溫度參數，用於控制生成文本的隨機性，預設為 0.2。
            **kwargs: 其他額外參數。

        屬性:
            client (OpenAI): 同步 OpenAI 客戶端。
            aclient (AsyncOpenAI): 非同步 OpenAI 客戶端。
            max_tokens (int): 模型的最大 token 數。
            model_info (dict): 模型資訊字典。
            params (dict): 請求參數字典。
        """
        api_key = os.environ["OPENAI_API_KEY"]
        super().__init__(model,system_prompt,temperature, **kwargs)
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

        else:
            print('{0} is not valid model!'.format(model))
        self.params = {'top_p': 1, 'temperature': 1, 'top_k': 1, 'presence_penalty': 0,
                       'frequency_penalty': 0}

    @retry(wait=wait_random_exponential(multiplier=1, max=40), stop=stop_after_attempt(3))
    def chat_completion_request(self, message_with_context, stream=False, use_tool=False,is_json=None,**kwargs):
        """
        發送聊天完成請求。

        參數:
            message_with_context (list): 包含上下文的訊息列表。
            stream (bool): 是否使用流式傳輸，預設為 False。
            use_tool (bool): 是否使用工具，預設為 False。
            is_json (bool): 是否返回 JSON 格式，預設為 None。
            **kwargs: 其他額外參數。

        返回:
            dict: 聊天完成的回應。
        """
        parameters=kwargs
        if 'max_tokens' in kwargs and kwargs['max_tokens'] != "NOT_GIVEN":
            parameters['max_tokens'] = int(kwargs['max_tokens'])

        payload = {
            "model": self.model,
            "messages": message_with_context,
            "temperature": parameters.get('temperature'),
            "top_p": parameters.get('top_p'),
            "n": 1,
            "max_tokens": parameters.get('max_tokens', NOT_GIVEN),
            "presence_penalty": parameters.get('presence_penalty'),
            "frequency_penalty": parameters.get('frequency_penalty'),
            "stream": stream
        }
        if is_json:
            payload['response_format'] = {"type": "json_object"}

        return self.client.chat.completions.create(**payload)

    @retry(wait=wait_random_exponential(multiplier=1, max=40), stop=stop_after_attempt(3))
    async def async_chat_completion_request(self, message_with_context, stream=False, use_tool=False,**kwargs):
        """
        發送非同步聊天完成請求。

        參數:
            message_with_context (list): 包含上下文的訊息列表。
            stream (bool): 是否使用流式傳輸，預設為 False。
            use_tool (bool): 是否使用工具，預設為 False。
            **kwargs: 其他額外參數。

        返回:
            dict: 聊天完成的回應。
        """
        parameters=kwargs
        if 'max_tokens' in kwargs and kwargs['max_tokens'] != "NOT_GIVEN":
            parameters['max_tokens'] = int(kwargs['max_tokens'])

        payload = {
            "model": self.model,
            "messages": message_with_context,
            "temperature": parameters.get('temperature'),
            "top_p": parameters.get('top_p'),
            "n": 1,
            "max_tokens": parameters.get('max_tokens', NOT_GIVEN),
            "presence_penalty": parameters.get('presence_penalty'),
            "frequency_penalty": parameters.get('frequency_penalty'),
            "stream": stream
        }
        if is_json:
            payload['response_format'] = {"type": "json_object"}

        return await self.aclient.chat.completions.create(**payload)

    async def generate_summary(self, content):
        """
        生成內容摘要。

        參數:
            content (str): 要總結的內容。

        返回:
            dict: 生成的摘要。
        """
        prompt = f"請將以下內容總結為筆記，所有重要知識點以及關鍵資訊應該盡可能保留:\n\n{content}"
        message_with_context = [
            {"role": "system", "content": "你是一個萬能的文字幫手"},
            {"role": "user", "content": prompt}
        ]
        params = copy.deepcopy(self.params)
        params['temperature'] = 0.5
        summary = await self.async_chat_completion_request(message_with_context, stream=False, use_tool=False)
        return summary

    def generate(self, prompt: str,is_json=None,stream=False,system_prompt=None,temperature=0.2) -> str:
        """
        生成 LLM 的回應。

        參數:
            prompt (str): 用戶的提示詞。
            is_json (bool): 是否返回 JSON 格式，預設為 None。
            stream (bool): 是否使用流式傳輸，預設為 False。
            system_prompt (str): 系統提示詞，預設為 None。

        返回:
            str: 生成的回應。
        """
        if not system_prompt:
            system_prompt=self.system_prompt
        messages_with_context = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
        response = self.chat_completion_request(messages_with_context, is_json=is_json,stream=stream,temperature=temperature)
        if not stream:
            return response.choices[0].message.content.strip()
        # else:
        #     partial_words = ''
        #     delta = ''
        #     tool_calls = []
        #     for chunk in response:
        #         if chunk.choices and chunk.choices[0].delta:
        #             finish_reason = chunk.choices[0].finish_reason
        #             if chunk.choices[0].delta.content:
        #                 partial_words += chunk.choices[0].delta.content
        #                 yield partial_words
        #
        #     if finish_reason == 'length':
        #         message_with_context.append({"role": "assistant", "content": partial_words})
        #         message_with_context.append({"role": "user", "content":  '從上次中斷處繼續，若中斷點位於列表中則從該列表開頭處繼續'})
        #         continue_res = self.post_streaming_chat(message_with_context, use_tool=True)
        #         message_with_context.pop(-1)
        #         message_with_context.pop(-1)
        #
        #         while True:
        #             try:
        #                 delta, partial_words2 = next(continue_res)
        #                 yield partial_words + partial_words2
        #             except StopIteration:
        #                 break
        #         partial_words += partial_words2
        #     return  partial_words




            


class AzureClient(LLMClient):
    def __init__(self, model='gpt-4o-auto', system_prompt='你是一個萬能的人工智能助理', temperature=0.2,**kwargs ):
        super().__init__(model,system_prompt,temperature, **kwargs)
        paras = copy.deepcopy(oai[model])
        paras.pop("max_tokens")

        self.client = AzureOpenAI(**paras)
        self.aclient = AsyncAzureOpenAI(**paras)
        self.params = {'top_p': 1, 'temperature': 1, 'top_k': 1, 'presence_penalty': 0,
                       'frequency_penalty': 0}

    @retry(wait=wait_random_exponential(multiplier=1, max=40), stop=stop_after_attempt(3))
    def chat_completion_request(self, message_with_context, parameters=None, stream=False,json_output=False,temperature=0.2):
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
            stream=stream
        )

    @retry(wait=wait_random_exponential(multiplier=1, max=40), stop=stop_after_attempt(3))
    async def async_chat_completion_request(self, message_with_context, parameters=None, stream=False,temperature=0.2):
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
            stream=stream
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

    def generate(self, prompt: str, stream=False,temperature=0.2) -> str:
        """生成 LLM 的回應。"""
        messages_with_context = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": prompt}
        ]

        if not stream:
            response = self.chat_completion_request(messages_with_context, stream=stream,temperature=temperature)
            return response.choices[0].message.content.strip()
        # else:
        #     response = self.chat_completion_request(messages_with_context, stream=stream)
        #     partial_words = ''
        #     delta = ''
        #     tool_calls = []
        #     for chunk in response:
        #         if chunk.choices and chunk.choices[0].delta:
        #             finish_reason = chunk.choices[0].finish_reason
        #             if chunk.choices[0].delta.content:
        #                 partial_words += chunk.choices[0].delta.content
        #                 yield partial_words
        #
        #     if finish_reason == 'length':
        #         message_with_context.append({"role": "assistant", "content": partial_words})
        #         message_with_context.append(
        #             {"role": "user", "content": '從上次中斷處繼續，若中斷點位於列表中則從該列表開頭處繼續'})
        #         continue_res = self.post_streaming_chat(message_with_context, use_tool=True)
        #         message_with_context.pop(-1)
        #         message_with_context.pop(-1)
        #
        #         while True:
        #             try:
        #                 delta, partial_words2 = next(continue_res)
        #                 yield partial_words + partial_words2
        #             except StopIteration:
        #                 break
        #         partial_words += partial_words2
        #     return partial_words