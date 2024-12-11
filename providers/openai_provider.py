# providers/openai_provider.py
import os
import logging
import requests
import json
from providers.base_provider import BaseProvider


class OpenAIProvider(BaseProvider):
    def __init__(self, model='gpt-4o', api_base=None, version=None, temperature=None, max_tokens=None):
        self.logger = logging.getLogger(self.__class__.__name__)

        # Dynamically set the API key based on the model name
        if "mini" in model.lower():
            self.api_key = os.getenv("ELEMENTS_API_KEY_GPT_MINI")
        else:
            # self.api_key = os.getenv("ELEMENTS_API_KEY")
            self.api_key = os.getenv("ELEMENTS_API_KEY_GPT_MINI")

        # Check if API key is available
        if not self.api_key:
            raise ValueError("API key is missing from environment variables.")

        self.model = model
        self.api_base = api_base
        self.api_version = version
        self.temperature = temperature
        self.max_tokens = max_tokens

        # Setup CA bundle path for SSL verification
        ca_bundle_path = os.getenv("WMT_CA_PATH")
        cert_file_name = "ca-bundle.crt"
        self.resolved_file_path = os.path.join(ca_bundle_path, cert_file_name)

        self.headers = {
            'x-api-key'   : self.api_key,
            'Content-Type': 'application/json'
        }

    def create_chat_completion(self, model: str, messages: list, temperature: float, max_tokens: int):
        # Define the payload structure based on the model name
        if "mini" in model.lower():
            payload = {
                "model"            : model,
                "task"             : "chat/completions",
                "api-version"      : self.api_version,
                "model-params"     : {
                    "messages": messages
                },
                "temperature"      : temperature,
                "max_tokens"       : max_tokens,
                "top_p"            : 0.95,
                "frequency_penalty": 0,
                "presence_penalty" : 0,
                "stop"             : None
            }
        else:
            payload = {
                "model"            : model,
                "task"             : "chat/completions",
                "api-version"      : self.api_version,
                "model-params": {
                    "messages": messages
                },
                "temperature"      : temperature,
                "max_tokens"       : max_tokens,
                "top_p"            : 0.95,
                "frequency_penalty": 0,
                "presence_penalty" : 0,
                "stop"             : None
            }

        try:
            response = requests.post(
                self.api_base,
                headers=self.headers,
                data=json.dumps(payload),
                verify=self.resolved_file_path
            )
            response.raise_for_status()
            response_data = response.json()
            content = response_data['choices'][0]['message']['content']
            return {"choices": [{"message": {"content": content}}]}
        except requests.exceptions.RequestException as e:
            self.logger.error("Error creating OpenAI chat completion (%s): %s",str(model), str(e))
            raise
