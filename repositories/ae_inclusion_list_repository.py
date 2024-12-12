from typing import List
from sqlalchemy.orm import Session

class AEInclusionListRepository:
    
    def __init__(self, db_session: Session):
        self.db_session = db_session

    def get_certified_attributes(self, product_type: str, precision_level: str = None) -> List[str]:
        """
        Returns a list of certified attributes for the given product_type.
        Optionally filter by attribute_precision_level if provided.
        """
        if precision_level:
            sql = """
            SELECT attribute_name FROM ae_inclusion_list
            WHERE product_type = :ptype AND certified = 1 AND attribute_precision_level = :plevel
            """
            rows = self.db_session.execute(sql, {"ptype": product_type, "plevel": precision_level}).fetchall()
        else:
            sql = """
            SELECT attribute_name FROM ae_inclusion_list
            WHERE product_type = :ptype AND certified = 1
            """
            rows = self.db_session.execute(sql, {"ptype": product_type}).fetchall()

        return [r['attribute_name'] for r in rows]
