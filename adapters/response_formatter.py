# adapters/response_formatter.py
import logging

class DefaultJSONResponseFormatter:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def format(self, results):
        """
        Formats the results into a JSON-friendly structure.
        Currently returns the results as-is.
        """
        self.logger.debug("Formatting results for response.")
        return results
