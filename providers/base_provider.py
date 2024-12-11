# providers/base_provider.py

class BaseProvider:
    def create_chat_completion(self, model: str, messages: list, temperature: float, max_tokens: int):
        raise NotImplementedError("This method should be overridden by subclasses.")
