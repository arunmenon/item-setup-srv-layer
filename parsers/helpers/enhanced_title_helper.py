# parsers/helpers/enhanced_title_helper.py

import logging
from typing import Optional, Match

def extract_enhanced_title(match: Optional[Match]) -> str:
    """
    Extracts the enhanced title from the regex match.

    Args:
        match (Optional[Match]): The regex match object.

    Returns:
        str: The extracted enhanced title or 'Not specified' if extraction fails.
    """
    if match:
        try:
            enhanced_title = match.group(1).strip()
            logging.debug(f"Extracted Enhanced Title: {enhanced_title}")
            return enhanced_title
        except IndexError:
            logging.warning("Enhanced Title extraction failed. Assigning 'Not specified'.")
    else:
        logging.warning("No match found for Enhanced Title. Assigning 'Not specified'.")
    return "Not specified"
