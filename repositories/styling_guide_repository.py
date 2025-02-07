# repositories/styling_guide_repository.py
from typing import Dict
from sqlalchemy.orm import Session
from models.models import StylingGuide

class StylingGuideRepository:
    def __init__(self, db_session: Session):
        self.db_session = db_session

    def fetch_active_styling_guides(self) -> Dict[str, Dict[str, str]]:
        """
        Returns a dict mapping product types to a dict of {task_name: styling guide content}.
        """
        styling_guides = self.db_session.query(StylingGuide).filter_by(is_active=True).all()
        result = {}
        for sg in styling_guides:
            product_type = sg.product_type.strip().lower()
            task_name = sg.task_name.strip().lower()
            content = sg.content.strip()
            if product_type not in result:
                result[product_type] = {}
            result[product_type][task_name] = content
        return result

    def get_styling_guide(self, product_type: str, task: str) -> str:
        guides = self.fetch_active_styling_guides()
        product_guides = guides.get(product_type.lower(), {})
        return product_guides.get(task.lower(), "")
