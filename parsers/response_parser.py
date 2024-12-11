# parsers/response_parser.py

from typing import Dict, Any
from abc import ABC, abstractmethod

class ResponseParser(ABC):
    @abstractmethod
    def parse(self, response: str) -> Dict[str, Any]:
        """
        Parses the response from the LLM and returns a dictionary.
        """
        pass
