# builders/attribute_instruction_builder.py

from typing import Dict, Any

class AttributeInstructionBuilder:
    """
    Decoupled from prompt_manager. Creates instructions for each attribute spec.

    This logic was previously partially inside the prompt manager or
    scattered across the code. We centralize it here for clarity.
    """
    def create_attribute_prompt(self, spec_data: Dict[str, Any]) -> str:
        """
        Uses new fields from ae_inclusion_list (e.g. display_name, closed_list, acceptable_values)
        to build an advanced prompt snippet, e.g.:

            "An Color with valid options: red, blue or 'N/A'"
        
        Returns a string instruction or placeholder snippet that can be inserted
        into the final AE prompt.
        """
        display_name = spec_data.get("display_name", "Unnamed Attribute")
        closed_list = spec_data.get("closed_list", False)
        multi_select = spec_data.get("multi_select", False)
        raw_values = spec_data.get("acceptable_values", "")

        # Convert semicolon or comma separated strings
        if raw_values:
            # e.g. "red;blue" => ["red", "blue"]
            raw_values = raw_values.replace(",", ";")
            values_list = [v.strip() for v in raw_values.split(";") if v.strip()]
            if closed_list:
                valid_options = ", ".join(values_list) + " or 'N/A'"
                valid_str = f" with valid options: {valid_options}"
            else:
                valid_str = ""
        else:
            valid_str = ""

        article = "Any" if multi_select else ("An" if display_name[:1].lower() in "aeiouy" else "A")
        prompt = f"{article} {display_name}{valid_str}"
        return prompt
