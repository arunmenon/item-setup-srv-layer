# parsers/json_response_parser.py

import json
import logging
import re
from parsers.response_parser import ResponseParser

class JsonResponseParser(ResponseParser):
    def __init__(self):
        super().__init__()  # Assuming ResponseParser can be initialized without parameters

    def parse(self, response: str) -> dict:
        """
        Parses the JSON response from the LLM.

        Args:
            response (str): The raw response string from the LLM.

        Returns:
            dict: Parsed JSON data.
        """
        try:
            # Attempt to extract JSON content between triple backticks if present
            json_content = re.search(r'```json\s*\n?(.*?)\n?```', response, re.DOTALL)

            if json_content:
                json_str = json_content.group(1).strip()  # Strip leading/trailing whitespace/newlines
                # json_str = json.loads(f'"{json_str}"').strip()  # Wrap the string in quotes to ensure it's valid JSON
                logging.debug(f"Extracted JSON from code block: {json_str}")
            else:
                # Fallback: Use the entire response as JSON, ensuring it's stripped of unnecessary newlines
                json_str = response.strip()
                logging.debug("No code block found. Attempting to parse full response.")

            # Validate JSON starts properly if not caught by regex
            if not json_str.startswith(('{', '[')):
                json_str = json.loads(f'"{json_str}"').strip()  # Wrap the string in quotes to ensure it's valid JSON
                if not json_str.startswith(('{', '[')):
                    logging.warning("Response does not start with JSON object or array.")
                    raise ValueError("Response does not contain valid JSON.")

            # Attempt to parse JSON
            parsed_json = json.loads(json_str)
            return parsed_json

        except json.JSONDecodeError as e:
            logging.error(f"Failed to parse JSON response: {e}\nResponse: {response}")
            raise ValueError(f"Failed to parse JSON response: {e}")
