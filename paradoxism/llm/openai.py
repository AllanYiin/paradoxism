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
    def chat_completion_request(self, message_with_context, stream=False, use_tool=False,**kwargs):
        parameters=kwargs
        if 'max_tokens' in kwargs and kwargs['max_tokens'] != "NOT_GIVEN":
            parameters['max_tokens'] = int(kwargs['max_tokens'])

        return self.client.chat.completions.create(
            model=self.model,
            messages=message_with_context,
            temperature=self.temperature,
            top_p=parameters.get('top_p'),
            n=1,
            max_tokens=parameters.get('max_tokens', NOT_GIVEN),
            presence_penalty=parameters.get('presence_penalty'),
            frequency_penalty=parameters.get('frequency_penalty'),
            stream=stream
        )

    @retry(wait=wait_random_exponential(multiplier=1, max=40), stop=stop_after_attempt(3))
    async def async_chat_completion_request(self, message_with_context, stream=False, use_tool=False,**kwargs):
        parameters=kwargs
        if 'max_tokens' in kwargs and kwargs['max_tokens'] != "NOT_GIVEN":
            parameters['max_tokens'] = int(kwargs['max_tokens'])


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


    def generate(self, prompt: str,stream=False) -> str:
        """生成 LLM 的回應。"""
        messages_with_context = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": prompt}
        ]
        response = self.chat_completion_request(messages_with_context, stream=stream)
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
            stream=stream
        )

    @retry(wait=wait_random_exponential(multiplier=1, max=40), stop=stop_after_attempt(3))
    async def async_chat_completion_request(self, message_with_context, parameters=None, stream=False):
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

    def generate(self, prompt: str, stream=False) -> str:
        """生成 LLM 的回應。"""
        messages_with_context = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": prompt}
        ]

        if not stream:
            response = self.chat_completion_request(messages_with_context, stream=stream)
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