import os
import logging
from openai import OpenAI

from providers.base_provider import BaseProvider

class RunPodProvider(BaseProvider):
    def __init__(self,endpoint_id=None):
        self.logger = logging.getLogger(self.__class__.__name__)
        runpod_api_key = os.getenv("RUNPOD_API_KEY")
        runpod_endpoint_id = endpoint_id or os.getenv("RUNPOD_ENDPOINT_ID")

        if not runpod_api_key or not runpod_endpoint_id:
            raise ValueError("RUNPOD_API_KEY or RUNPOD_ENDPOINT_ID is missing from environment variables.")

        self.client = OpenAI(
            api_key=runpod_api_key,
            base_url=f"https://api.runpod.ai/v2/{runpod_endpoint_id}/openai/v1",
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
