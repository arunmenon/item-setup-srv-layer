# repositories/ae_scope_list_repository.py
from typing import List, Dict, Any
from sqlalchemy.orm import Session
import json

class AEScopeListRepository:
    """
    Single source of truth for AE attribute specs from 'ae_inclusion_list'.
    Now extended to include new columns:
      - display_name
      - taxonomy_key
    If your colleague needed more columns, add them here.
    """
    def __init__(self, db_session: Session):
        self.db_session = db_session

    def get_certified_attributes(self, product_type: str) -> List[str]:
        """
        Returns a list of certified attribute names for the given product type,
        reading 'ae_inclusion_list' with 'certified=1'.
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
        Merges the 'spec' JSON column with additional columns:
          closed_list, multi_select, acceptable_values, example_values, display_name, taxonomy_key
        """
        sql = """
        SELECT
            spec,
            closed_list,
            multi_select,
            acceptable_values,
            example_values,
            display_name,
            taxonomy_key
        FROM ae_inclusion_list
        WHERE product_type = :ptype
          AND attribute_name = :attr
          AND certified = 1
        """
        row = self.db_session.execute(sql, {"ptype": product_type, "attr": attribute_name}).fetchone()
        if not row:
            return {}

        result: Dict[str, Any] = {}
        if row["spec"]:
            try:
                result.update(json.loads(row["spec"]))
            except Exception:
                pass

        def to_bool(val):
            if isinstance(val, str):
                return val.lower() == "yes"
            return val

        result["closed_list"] = to_bool(row["closed_list"])
        result["multi_select"] = to_bool(row["multi_select"])
        result["acceptable_values"] = row["acceptable_values"]
        result["example_values"] = row["example_values"]
        result["display_name"] = row["display_name"] or attribute_name
        result["taxonomy_key"] = row["taxonomy_key"] or attribute_name.lower()

        return result
