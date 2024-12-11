# providers/claude_provider.py
import os
import logging
import requests
import json
from providers.base_provider import BaseProvider


class ClaudeProvider(BaseProvider):
    def __init__(self, model='claude-3-haiku', api_base=None, version=None, max_tokens=None):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.api_key = os.getenv("ELEMENTS_API_KEY_CLAUDE")
        self.model = model
        self.api_base = api_base
        self.api_version = version
        self.max_tokens = max_tokens

        if not self.api_key:
            raise ValueError("ELEMENTS_CLAUDE_API_KEY is missing from environment variables.")

        ca_bundle_path = os.getenv("WMT_CA_PATH")
        cert_file_name = "ca-bundle.crt"
        self.resolved_file_path = os.path.join(ca_bundle_path, cert_file_name)

        self.headers = {
            'X-Api-Key'   : self.api_key,
            'Content-Type': 'application/json'
        }

    def create_chat_completion(self, model_key: str, messages: list, temperature: float, max_tokens: int):

        # Combine the content of the messages into a single prompt string
        prompt = ""
        for message in messages:
            prompt += message['content']

        payload = {
            "model"        : self.model,
            "model-version": self.api_version,
            "task"         : "rawPredict",
            "model-params" : {
                "anthropic_version": "vertex-2023-10-16",
                "messages"         : [
                    {
                        "role"   : "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ],
                "max_tokens"       : max_tokens,
                "stream"           : False
            }
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
            content = response_data['content'][0]['text']
            return {"choices": [{"message": {"content": content}}]}
        except requests.exceptions.RequestException as e:
            self.logger.error("Error creating Claude raw predict: %s", str(e))
            raise