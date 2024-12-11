# providers/gemini_provider.py
import os
# import google.generativeai as genai
import logging
from providers.base_provider import BaseProvider
import requests
import json


class GeminiProvider(BaseProvider):
    def __init__(self, model='gemini-1.5-flash', api_base=None, version=None, temperature=None, max_tokens=None):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.api_base = api_base or "https://wmtllmgateway.stage.walmart.com/wmtllmgateway/v1/google-genai"
        self.api_version = version or "001"

        if not self.api_key:
            self.logger.error("Gemini API key is not provided.")
            raise ValueError("Gemini API key is required.")

        ca_bundle_path = os.getenv("WMT_CA_PATH")
        cert_file_name = "ca-bundle.crt"
        self.resolved_file_path = os.path.join(ca_bundle_path, cert_file_name)

        self.headers = {
            'x-api-key'   : self.api_key,
            'Content-Type': 'application/json'
        }
        self.safety_settings_gemini = [
            {
                "category": 'HARM_CATEGORY_HATE_SPEECH',
                "threshold": 'BLOCK_NONE'
            },
            {
                "category": 'HARM_CATEGORY_UNSPECIFIED',
                "threshold": 'BLOCK_NONE'
            },
            {
                "category": 'HARM_CATEGORY_DANGEROUS_CONTENT',
                "threshold": 'BLOCK_NONE'
            },
            {
                "category": 'HARM_CATEGORY_SEXUALLY_EXPLICIT',
                "threshold": 'BLOCK_NONE'
            },
            {
                "category": 'HARM_CATEGORY_HARASSMENT',
                "threshold": 'BLOCK_NONE'
            }
        ]

    def configure_gen_settings(self, temperature, max_tokens):
        return {
            "maxOutputTokens": max_tokens,
            "temperature"    : temperature,
            "topP"           : 1
        }

    def create_chat_completion(self, model: str, messages: list, temperature: float, max_tokens: int):
        try:
            parts = [{"text": msg['content']} for msg in messages]
            payload = {
                "model"        : model,
                "task"         : "generateContent",
                "model-version": self.api_version,
                "model-params" : {
                    "contents"          : {
                        "role" : "user",
                        "parts": parts
                    },
                    "system_instruction": {
                        "parts": [
                            {
                                "text": ""
                            }
                        ]
                    },
                    "generation_config" : self.configure_gen_settings(temperature, max_tokens),
                    "safetySettings": self.safety_settings_gemini
                },
                "temperature"  : temperature,
                "max_tokens"   : max_tokens
            }

            response = requests.post(
                self.api_base,
                headers=self.headers,
                data=json.dumps(payload),
                verify=self.resolved_file_path
            )
            response.raise_for_status()
            response_data = response.json()
            content = response_data['candidates'][0]['content']['parts'][0]['text']  # Adjusted based on the expected response format
            return {"choices": [{"message": {"content": content}}]}
        except requests.exceptions.RequestException as e:
            self.logger.error("Error creating Gemini chat completion: %s", str(e))
            raise