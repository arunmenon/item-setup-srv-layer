# parsers/helpers/extracted_attributes_helper.py

import logging
import re
from typing import List, Dict, Optional, Match

def extract_extracted_attributes(match: Optional[Match], attributes_list: List[str]) -> Dict[str, str]:
    """
    Extracts the attributes from the regex match.

    Args:
        match (Optional[Match]): The regex match object.
        attributes_list (List[str]): The list of attributes to extract.

    Returns:
        Dict[str, str]: A dictionary of extracted attributes with 'Not specified' as default.
    """
    attributes = {attr: "Not specified" for attr in attributes_list}
    
    if match:
        try:
            attributes_text = match.group(1).strip()
            logging.debug(f"Extracted Attributes Text: {attributes_text}")
            for line in attributes_text.split('\n'):
                attr_match = re.match(r"- \*\*(.+?)\*\*:\s*(.+)", line)
                if attr_match:
                    key, value = attr_match.groups()
                    key = key.strip()
                    value = value.strip()
                    if key in attributes:
                        attributes[key] = value
                        logging.debug(f"Parsed attribute '{key}': {value}")
            return attributes
        except IndexError:
            logging.warning("Extracted Attributes extraction failed. Assigning 'Not specified' for all attributes.")
    else:
        logging.warning("No match found for Extracted Attributes. Assigning 'Not specified' for all attributes.")
    
    return attributes
