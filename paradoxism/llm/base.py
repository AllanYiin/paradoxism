import glob
import copy
import json
import re
from paradoxism import context
from paradoxism.context import *

cxt = context._context()
__all__ = ["LLMClient","LLMClientManager"]


class LLMClient:
    def __init__(self, model, system_prompt, temperature=0.2, **kwargs):

        self.model = model
        self.tools = []
        self.client = None
        self.system_prompt = system_prompt
        self.temperature=temperature
        self.aclient = None
        self.params =None

    def chat_completion_request(self, message_with_context, parameters=None, stream=False, use_tool=True):
        raise NotImplementedError("Subclasses should implement this method")

    async def async_chat_completion_request(self, message_with_context, parameters=None, stream=False, use_tool=True):
        raise NotImplementedError("Subclasses should implement this method")



class LLMClientManager:
    def __init__(self, config_file='config.json', default_model='gpt-4o', tools=None):
        self.default_model = default_model
        self.tools = tools
        self.config = None
        self.load_config(config_file)
        self.current_client = None

    def load_config(self, config_file):
        with open(config_file, 'r') as f:
            self.config = json.load(f)
            self.switch_model()

    def switch_model(self, provider, model=None, instance=None):
        if provider == 'openai':
            self.current_client = OpenAIClient(api_key=model or self.default_model, tools=self.tools)
        elif provider == 'azure' and instance:
            instance_config = self.config['azure'].get(instance)
            if instance_config:
                self.current_client = AzureClient(api_key=instance_config['api_key'],
                                                  endpoint=instance_config['endpoint'], model=model, tools=self.tools)
            else:
                raise ValueError(f"Instance {instance} not found in configuration.")
        elif provider == 'google_gemini':
            self.current_client = GoogleGeminiClient(api_key=self.config['google_gemini']['api_key'],
                                                     endpoint=self.config['google_gemini']['endpoint'], model=model,
                                                     tools=self.tools)
        elif provider == 'claude':
            self.current_client = ClaudeClient(api_key=self.config['claude']['api_key'],
                                               endpoint=self.config['claude']['endpoint'], model=model,
                                               tools=self.tools)
        else:
            raise ValueError("Invalid provider or missing instance information.")

    def chat_completion_request(self, message_with_context, parameters, stream=False, use_tool=True):
        if self.current_client is None:
            raise ValueError("No client selected. Please switch to a model first.")
        return self.current_client.chat_completion_request(message_with_context, parameters, stream, use_tool)

    async def async_chat_completion_request(self, message_with_context, parameters, stream=False, use_tool=True):
        if self.current_client is None:
            raise ValueError("No client selected. Please switch to a model first.")
        return await self.current_client.async_chat_completion_request(message_with_context, parameters, stream,
                                                                       use_tool)


