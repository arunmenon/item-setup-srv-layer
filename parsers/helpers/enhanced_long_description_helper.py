# parsers/helpers/enhanced_long_description_helper.py

import logging
from typing import Optional, Match

def extract_enhanced_long_description(match: Optional[Match]) -> str:
    """
    Extracts the enhanced long description from the regex match.

    Args:
        match (Optional[Match]): The regex match object.

    Returns:
        str: The extracted enhanced long description or 'Not specified' if extraction fails.
    """
    if match:
        try:
            enhanced_long_description = match.group(1).strip()
            logging.debug(f"Extracted Enhanced Long Description: {enhanced_long_description}")
            return enhanced_long_description
        except IndexError:
            logging.warning("Enhanced Long Description extraction failed. Assigning 'Not specified'.")
    else:
        logging.warning("No match found for Enhanced Long Description. Assigning 'Not specified'.")
    return "Not specified"
