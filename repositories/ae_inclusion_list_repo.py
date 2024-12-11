# repositories/ae_inclusion_list_repo.py

import logging
from typing import Dict, List
from sqlalchemy.orm import Session
from models.models import AEInclusionList

class AEInclusionListRepo:
    def __init__(self, db_session: Session):
        """
        Repository for fetching and caching allowed attributes for attribute extraction tasks.

        Args:
            db_session (Session): SQLAlchemy database session
        """
        self.db_session = db_session
        self.logger = logging.getLogger(self.__class__.__name__)
        self.inclusion_cache: Dict[str, List[str]] = {}
        self.load_inclusion_lists()

    def load_inclusion_lists(self):
        """
        Load all active inclusion attributes from the database into an in-memory cache.
        """
        rows = self.db_session.query(AEInclusionList).filter_by(is_active=True).all()
        temp_cache = {}
        for row in rows:
            pt = row.product_type.strip().lower()
            attr = row.attribute_name.strip().lower()
            if pt not in temp_cache:
                temp_cache[pt] = []
            temp_cache[pt].append(attr)
        self.inclusion_cache = temp_cache
        self.logger.info(f"Loaded AE inclusion lists for product types: {list(self.inclusion_cache.keys())}")

    def get_included_attributes(self, product_type: str) -> List[str]:
        """
        Returns the list of allowed attributes for the given product_type.

        Args:
            product_type (str): The product type to fetch allowed attributes for.

        Returns:
            List[str]: The list of allowed attributes.
        """
        product_type = product_type.lower()
        return self.inclusion_cache.get(product_type, [])

    def reload(self):
        """
        Reload the inclusion lists (e.g., after updating the database).
        """
        self.load_inclusion_lists()
