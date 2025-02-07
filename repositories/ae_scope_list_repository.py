# repositories/ae_scope_list_repository.py
from typing import List, Dict, Any
from sqlalchemy.orm import Session

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
        SELECT attribute_name FROM ae_inclusion_list
        WHERE product_type = :ptype AND certified = 1
        """
        rows = self.db_session.execute(sql, {"ptype": product_type}).fetchall()
        return [r["attribute_name"].lower() for r in rows]

    def get_attribute_spec(self, product_type: str, attribute_name: str) -> Dict[str, Any]:
        """
        Returns the specification for a given attribute (if available), by reading the 'spec' column.
        """
        sql = """
        SELECT spec FROM ae_inclusion_list
        WHERE product_type = :ptype AND attribute_name = :attr AND certified = 1
        """
        row = self.db_session.execute(sql, {"ptype": product_type, "attr": attribute_name}).fetchone()
        if row and row["spec"]:
            import json
            try:
                return json.loads(row["spec"])
            except Exception:
                return {}
        return {}
