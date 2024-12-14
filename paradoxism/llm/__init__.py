from . import openai
from . import ollama
from . import claude
from . import base
from paradoxism.context import *
LLMClient=base.LLMClient
LLMClientManager=base.LLMClientManager
OpenAIClient=openai.OpenAIClient
AzureClient=openai.AzureClient
OllamaClient=ollama.OllamaClient
ClaudeClient=claude.ClaudeClient

provider_mapping = {"openai": 'OpenAIClient',
                    "chatgpt": 'OpenAIClient',
                    "azure": 'AzureClient',
                    "aoi": 'AzureClient',
                    "ollama": 'OllamaClient',
                    "anthropic": 'ClaudeClient',
                    "claude": 'ClaudeClient'}

def get_llm(provider_or_model_name, system_prompt, temperature=0.2, **kwargs):
    llm_client=None
    if provider_or_model_name is None:
        return None
    fn_modules = ['paradoxism.llm.claude','paradoxism.llm.openai', 'paradoxism.llm.azure', 'paradoxism.llm.ollama']
    if provider_or_model_name in provider_mapping:

        llm_client = get_class( provider_mapping[provider_or_model_name], fn_modules)
        return llm_client(system_prompt=system_prompt, temperature=0.2, **kwargs)
    else:
        for k,v in model_info.items():
            if provider_or_model_name.lower() in v:
                llm_client = get_class(provider_mapping[k] , fn_modules)
                return llm_client(model=provider_or_model_name,system_prompt=system_prompt, temperature=0.2, **kwargs)
        if llm_client is None:
            for k, v in oai.items():
                if provider_or_model_name.lower() ==k:
                    llm_client = get_class(provider_mapping["azure"], fn_modules)
                    return llm_client(model=provider_or_model_name, system_prompt=system_prompt, temperature=0.2, **kwargs)
    if llm_client is None:
        raise ValueError('Unknown llm provider')

