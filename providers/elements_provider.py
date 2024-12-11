import json
import os
import logging
import requests
from providers.base_provider import BaseProvider


class ElementsProvider(BaseProvider):
    CONFIG = {
        'llama3-8b-orca-1024-w8a8': {
            'url'        : 'https://llama3-8b-orca-1024-w8a8-stage.element.glb.us.walmart.net/llama3-8b-orca-1024-w8a8/v1/completions',
            'api_key_env': "ELEMENTS_API_KEY_LLAMA3_8B",
        },
        'meta-llama/Llama-3.2-1B' : {
            'url'        : 'https://llama-3-dot-2-1b-stage.element.glb.us.walmart.net/llama-3-dot-2-1b/v1/completions',
            'api_key_env': "ELEMENTS_API_KEY_META_LLAMA3_1B",
        },
        'meta-llama/Llama-3.2-3B' : {
            'url'        : 'https://llama-3-dot-2-3b-stage.element.glb.us.walmart.net/llama-3-dot-2-3b/v1/completions',
            'api_key_env': "ELEMENTS_API_KEY_META_LLAMA3_3B",
        },
        'meta-llama/Llama-3.1-405B-Instruct-FP8': {
            'url'        : 'https://llama-3-dot-1-405b-fp8-stage.element.glb.us.walmart.net/llama-3-dot-1-405b-fp8/v1/completions',
            'api_key_env': "ELEMENTS_API_KEY_META_LLAMA3_405B",
        },
        'neuralmagic/SmolLM-1.7B-Instruct-quantized.w8a16': {
            'url'        : 'https://smollm-1-7b-instruct-q-stage.element.glb.us.walmart.net/smollm-1-7b-instruct-q/v1/completions',
            'api_key_env': "ELEMENTS_API_KEY_META_SMOLLM_1d7B",
        }
    }

    def __init__(self, model=None, api_base=None, version=None, temperature=None, max_tokens=None):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.model = model
        self.api_base = api_base
        self.api_version = version

        ca_bundle_path = os.getenv("WMT_CA_PATH")
        cert_file_name = "ca-bundle.crt"
        self.resolved_file_path = os.path.join(ca_bundle_path, cert_file_name)
        self.temperature = temperature
        self.max_tokens = max_tokens

    def create_chat_completion(self, model_key: str, messages: list, temperature: float, max_tokens: int):
        if model_key not in self.CONFIG:
            raise ValueError(f"Model key '{model_key}' is not supported.")

        config = self.CONFIG[model_key]
        api_key = os.getenv(config['api_key_env'])

        if not api_key:
            self.logger.error("API key for model '%s' is not provided.", model_key)
            raise ValueError(f"API key for model '{model_key}' is required.")

        headers = {
            'Authorization': f"Bearer {api_key}",
            'Content-Type' : 'application/json'
        }

        # Combine the content of the messages into a single prompt string
        prompt = ""
        for message in messages:
            prompt += message['content']

        payload = {
            "model"      : "/mnt/models",
            "prompt"     : prompt,
            "temperature": temperature,
            "max_tokens" : max_tokens
        }
        self.logger.debug(f"Payload {model_key} : {json.dumps(payload)}")
        try:
            response = requests.post(
                config['url'],
                headers=headers,
                data=json.dumps(payload),
                verify=self.resolved_file_path
            )
            response.raise_for_status()
            response_data = response.json()
            content = response_data.get('choices', [{}])[
                0].get('text', '')  # Adjusted based on expected response format
            return {"choices": [{"message": {"content": content}}]}
        except requests.exceptions.RequestException as e:
            self.logger.error("Error creating chat completion for model '%s': %s", model_key, str(e))
            raise
