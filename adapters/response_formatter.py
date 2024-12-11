# adapters/response_formatter.py
import logging

class DefaultJSONResponseFormatter:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def format(self, results):
        """
        Formats the results into a JSON-friendly structure.
        Currently just returns results as is, but could be extended.

        Args:
            results (dict): processed results from ItemEnricher.

        Returns:
            dict: formatted results
        """
        self.logger.debug("Formatting results for response.")
        return results
