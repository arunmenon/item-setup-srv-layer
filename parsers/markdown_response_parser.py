# parsers/markdown_response_parser.py

import re
import os
import logging
from typing import Dict, Any, List, Optional, Match
from importlib import import_module

from .response_parser import ResponseParser

class MarkdownResponseParser(ResponseParser):
    def __init__(self, patterns_filename: str = "patterns_config.txt", mapping_filename: str = "helper_mapping.txt"):
        """
        Initializes the MarkdownResponseParser by loading regex patterns and helper mappings from configuration files.

        Args:
            patterns_filename (str): The filename of the patterns configuration file.
            mapping_filename (str): The filename of the helper mappings configuration file.
        """
        # Determine the absolute paths to the config files within the parsers directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        patterns_path = os.path.join(current_dir, patterns_filename)
        mapping_path = os.path.join(current_dir, mapping_filename)

        self.patterns = self.load_patterns(patterns_path)
        self.compiled_patterns = self.compile_patterns(self.patterns)
        self.helper_mapping = self.load_helper_mapping(mapping_path)

    def load_patterns(self, patterns_path: str) -> Dict[str, str]:
        """
        Loads regex patterns from a TXT configuration file.

        Args:
            patterns_path (str): The file path to the patterns configuration TXT file.

        Returns:
            Dict[str, str]: A dictionary mapping task names to their regex patterns.
        """
        if not os.path.exists(patterns_path):
            logging.error(f"Patterns configuration file not found at '{patterns_path}'.")
            raise FileNotFoundError(f"Patterns configuration file not found at '{patterns_path}'.")

        patterns = {}
        with open(patterns_path, 'r') as file:
            for line_number, line in enumerate(file, 1):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue  # Skip empty lines or comments
                if ':' not in line:
                    logging.warning(f"Invalid pattern format at line {line_number}: '{line}'")
                    continue
                key, pattern = line.split(':', 1)
                patterns[key.strip()] = pattern.strip()
        logging.info(f"Loaded regex patterns from '{patterns_path}'.")
        return patterns

    def compile_patterns(self, patterns: Dict[str, str]) -> Dict[str, re.Pattern]:
        """
        Compiles regex patterns for faster matching.

        Args:
            patterns (Dict[str, str]): A dictionary of regex patterns as strings.

        Returns:
            Dict[str, re.Pattern]: A dictionary of compiled regex patterns.
        """
        compiled = {}
        for key, pattern in patterns.items():
            try:
                compiled[key] = re.compile(pattern, re.IGNORECASE | re.DOTALL)
                logging.debug(f"Compiled pattern for '{key}': {pattern}")
            except re.error as e:
                logging.error(f"Invalid regex pattern for '{key}': {e}")
                raise e
        return compiled

    def load_helper_mapping(self, mapping_path: str) -> Dict[str, Any]:
        """
        Loads helper mappings from a TXT configuration file.

        Args:
            mapping_path (str): The file path to the helper mappings configuration TXT file.

        Returns:
            Dict[str, Any]: A dictionary mapping pattern keys to helper functions.
        """
        if not os.path.exists(mapping_path):
            logging.error(f"Helper mapping configuration file not found at '{mapping_path}'.")
            raise FileNotFoundError(f"Helper mapping configuration file not found at '{mapping_path}'.")

        helper_mapping = {}
        with open(mapping_path, 'r') as file:
            for line_number, line in enumerate(file, 1):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue  # Skip empty lines or comments
                if ':' not in line:
                    logging.warning(f"Invalid helper mapping format at line {line_number}: '{line}'")
                    continue
                key, helper_path = line.split(':', 1)
                key = key.strip()
                helper_path = helper_path.strip()
                try:
                    module_path, function_name = helper_path.rsplit('.', 1)
                    module = import_module(module_path)
                    helper_function = getattr(module, function_name)
                    helper_mapping[key] = helper_function
                    logging.debug(f"Mapped '{key}' to helper function '{helper_path}'.")
                except (ImportError, AttributeError) as e:
                    logging.error(f"Error loading helper function '{helper_path}' for key '{key}': {e}")
                    raise ImportError(f"Error loading helper function '{helper_path}' for key '{key}': {e}")
        logging.info(f"Loaded helper mappings from '{mapping_path}'.")
        return helper_mapping

    def parse(self, response: str, attributes_list: List[str] = None) -> Dict[str, Any]:
        """
        Parses a Markdown-formatted response and extracts the enhanced content using helper functions.

        Args:
            response (str): The Markdown response from the LLM.
            attributes_list (List[str], optional): List of attributes to extract. Defaults to None.

        Returns:
            Dict[str, Any]: A dictionary containing the extracted/enhanced fields.
        """
        data = {}

        for key, pattern in self.compiled_patterns.items():
            match = pattern.search(response)
            if match:
                helper_function = self.helper_mapping.get(key)
                if helper_function:
                    logging.info(f"Pattern matched for key '{key}'. Invoking helper function '{helper_function.__name__}'.")
                    if key in ["extracted_attributes", "extracted_vision_attributes"]:
                        extracted_data = helper_function(match, attributes_list)
                    else:
                        extracted_data = helper_function(match)
                    data[self.camel_case(key)] = extracted_data
                else:
                    logging.warning(f"No helper function mapped for key '{key}'. Assigning 'Not specified'.")
                    data[self.camel_case(key)] = "Not specified"
            else:
                logging.warning(f"Pattern for key '{key}' not found in the response. Assigning 'Not specified'.")
                if key in ["extracted_attributes", "extracted_vision_attributes"]:
                    data[self.camel_case(key)] = {attr: "Not specified" for attr in attributes_list} if attributes_list else {}
                else:
                    data[self.camel_case(key)] = "Not specified"

        logging.debug(f"Final parsed data: {data}")
        return data

    def camel_case(self, snake_str: str) -> str:
        """
        Converts snake_case string to camelCase string.

        Args:
            snake_str (str): The snake_case string.

        Returns:
            str: The camelCase string.
        """
        components = snake_str.split('_')
        return components[0] + ''.join(x.title() for x in components[1:])
