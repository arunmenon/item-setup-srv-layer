# parsers/parser_factory.py

from parsers.markdown_response_parser import MarkdownResponseParser
from parsers.json_response_parser import JsonResponseParser
from parsers.response_parser import ResponseParser

class ParserFactory:
    @staticmethod
    def get_parser(output_format: str, patterns_filename: str = "patterns_config.txt", mapping_filename: str = "helper_mapping.txt") -> ResponseParser:
        """
        Returns an instance of the appropriate ResponseParser based on the output format.

        Args:
            output_format (str): Desired output format ('markdown' or 'json').
            patterns_filename (str, optional): The patterns configuration file name. Defaults to "patterns_config.txt".
            mapping_filename (str, optional): The helper mappings configuration file name. Defaults to "helper_mapping.txt".

        Returns:
            ResponseParser: An instance of the corresponding parser.
        """
        output_format = output_format.lower()
        if output_format == "markdown":
            return MarkdownResponseParser(patterns_filename=patterns_filename, mapping_filename=mapping_filename)
        elif output_format == "json":
            return JsonResponseParser()  # No arguments needed
        else:
            raise ValueError(f"Unsupported output format: {output_format}")
