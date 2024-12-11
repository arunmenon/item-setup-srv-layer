from providers.claude_provider import ClaudeProvider
from providers.local_provider import LocalProvider
from providers.elements_provider import ElementsProvider
from providers.openai_provider import OpenAIProvider
from providers.runpod_provider import RunPodProvider
from providers.gemini_provider import GeminiProvider
import logging


class ProviderFactory:
    logger = logging.getLogger(__name__)

    # Set default logging configuration
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

   


    @staticmethod
    def create_provider(provider_name, **kwargs):
        if provider_name == "openai":
            ProviderFactory.logger.debug(f"Creating OpenAI provider ")
            clean_kwargs = ProviderFactory.filter_kwargs(OpenAIProvider, kwargs)
            return OpenAIProvider(**clean_kwargs)
        elif provider_name == "runpod":
            ProviderFactory.logger.info(f"Creating RunPod provider ")
            clean_kwargs = ProviderFactory.filter_kwargs(RunPodProvider, kwargs)
            return RunPodProvider(**clean_kwargs)
        elif provider_name == "gemini":
            ProviderFactory.logger.info(f"Creating Gemini provider")
            clean_kwargs = ProviderFactory.filter_kwargs(GeminiProvider, kwargs)
            # model = kwargs.get('model', 'gemini-1.5-flash')
            return GeminiProvider(**clean_kwargs)
        elif provider_name=="claude":
            ProviderFactory.logger.info(f"Creating Claude provider")
            clean_kwargs = ProviderFactory.filter_kwargs(ClaudeProvider, kwargs)
            return ClaudeProvider(**clean_kwargs)
        elif provider_name=="elements_openai":
            # ProviderFactory.logger.info(f"Creating elements_openai provider")
            clean_kwargs = ProviderFactory.filter_kwargs(ElementsProvider, kwargs)
            model = kwargs.get('model', 'Unknown')
            ProviderFactory.logger.info(f"Creating {model} provider")
            return ElementsProvider(**clean_kwargs)
        elif provider_name=="local":
            ProviderFactory.logger.info(f"Creating Local provider")
            provider_port = kwargs.get("provider_port")
            return LocalProvider(port=provider_port)
        else:
            ProviderFactory.logger.error(f"Unsupported provider: {provider_name}")
            raise ValueError(f"Unsupported provider: {provider_name}")


    @staticmethod
    def filter_kwargs(provider_class, kwargs):
        # Filter kwargs to only those that are accepted by provider_class's __init__ method
        import inspect
        signature = inspect.signature(provider_class.__init__)
        valid_kwargs = {k: v for k, v in kwargs.items() if k in signature.parameters}
        return valid_kwargs