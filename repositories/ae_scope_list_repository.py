# repositories/ae_scope_list_repository.py
from typing import List, Dict, Any
from sqlalchemy.orm import Session
import json

class AEScopeListRepository:
    """
    Handles attribute extraction metadata.
    Provides methods to get certified attributes and attribute specifications.
    """
    def __init__(self, db_session: Session):
        self.db_session = db_session

    def get_certified_attributes(self, product_type: str) -> List[str]:
        """
        Returns a list of certified attribute names for the given product type.
        """
        sql = """
        SELECT attribute_name
        FROM ae_inclusion_list
        WHERE product_type = :ptype
          AND certified = 1
        """
        rows = self.db_session.execute(sql, {"ptype": product_type}).fetchall()
        return [r["attribute_name"].lower() for r in rows]

    def get_attribute_spec(self, product_type: str, attribute_name: str) -> Dict[str, Any]:
        """
        Returns the full specification for a given attribute, merging:
          - The 'spec' JSON column (if present)
          - Additional columns like closed_list, multi_select, acceptable_values, example_values, etc.
        
        The returned dictionary might look like:
        {
          "closed_list": True or False,
          "multi_select": True or False,
          "acceptable_values": "...",
          "example_values": "...",
          ... # plus any keys from the 'spec' JSON
        }
        """
        sql = """
        SELECT
            spec,
            closed_list,
            multi_select,
            acceptable_values,
            example_values
        FROM ae_inclusion_list
        WHERE product_type = :ptype
          AND attribute_name = :attr
          AND certified = 1
        """
        row = self.db_session.execute(sql, {"ptype": product_type, "attr": attribute_name}).fetchone()
        if not row:
            return {}

        result: Dict[str, Any] = {}

        # 1) Merge the 'spec' JSON (if present)
        if row["spec"]:
            try:
                spec_data = json.loads(row["spec"])
                # Merge keys from spec_data into result
                result.update(spec_data)
            except Exception:
                pass  # If parsing fails, just ignore the 'spec' content

        # 2) Add other columns (closed_list, multi_select, etc.)
        #    You may need to convert "Yes"/"No" => boolean if that's how it's stored in DB
        #    For instance, if row["closed_list"] is "No", we can map that to False, etc.
        #    Otherwise, if it is already boolean, just assign directly.

        # Example: convert "Yes" => True, "No" => False if needed.
        closed_list_str = row["closed_list"]
        if isinstance(closed_list_str, str):
            result["closed_list"] = (closed_list_str.lower() == "yes")
        else:
            # If it's already boolean in the DB, just do:
            result["closed_list"] = row["closed_list"]

        # Similarly for multi_select
        multi_select_str = row["multi_select"]
        if isinstance(multi_select_str, str):
            result["multi_select"] = (multi_select_str.lower() == "yes")
        else:
            result["multi_select"] = row["multi_select"]

        result["acceptable_values"] = row["acceptable_values"]
        result["example_values"] = row["example_values"]

        return result
