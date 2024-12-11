import os
import logging
from openai import OpenAI

from providers.base_provider import BaseProvider

class LocalProvider(BaseProvider):
    def __init__(self,port):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.client = OpenAI(
            base_url=f"http://localhost:{port}/v1",
        )

    def create_chat_completion(self, model: str, messages: list, temperature: float, max_tokens: int):
        
        if not model: 
            model = self.extract_model_name()

        try:
            response_stream = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
            )
            response = "".join([chunk.choices[0].delta.content or "" for chunk in response_stream])
            return {"choices": [{"message": {"content": response}}]}
        except BaseException as e:
            self.logger.error("Error creating RunPod chat completion: %s", str(e))
            raise

    def extract_model_name(self):
        models_response = list(self.client.models.list())
        
        if not models_response:
            raise ValueError("No models found in RunPod response")

        model = models_response[0].id
        self.logger.info(f"Model extracted is: {model}")
        return model
