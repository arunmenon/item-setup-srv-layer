# parsers/helpers/enhanced_short_description_helper.py

import logging
from typing import Optional, Match

def extract_enhanced_short_description(match: Optional[Match]) -> str:
    """
    Extracts the enhanced short description from the regex match.

    Args:
        match (Optional[Match]): The regex match object.

    Returns:
        str: The extracted enhanced short description or 'Not specified' if extraction fails.
    """
    if match:
        try:
            enhanced_short_description = match.group(1).strip()
            logging.debug(f"Extracted Enhanced Short Description: {enhanced_short_description}")
            return enhanced_short_description
        except IndexError:
            logging.warning("Enhanced Short Description extraction failed. Assigning 'Not specified'.")
    else:
        logging.warning("No match found for Enhanced Short Description. Assigning 'Not specified'.")
    return "Not specified"
