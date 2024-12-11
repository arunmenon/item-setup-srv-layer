# adapters/request_adapter.py
import logging

class LLMRequestAdapter:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def adapt(self, request_body: dict):
        """
        Adapt raw request_body into (item, task_type).

        Expected request_body keys:
        {
          "item_title": ...,
          "short_description": ...,
          "long_description": ...,
          "item_product_type": ...,
          "task_type": "generation" or "evaluation" (optional, defaults to 'generation'),
          "image_url": optional,
          "attributes_list": optional
        }

        Returns:
            (item: dict, task_type: str)
        """
        required = ["item_title","short_description","long_description","item_product_type"]
        missing = [r for r in required if r not in request_body]
        if missing:
            raise ValueError(f"Missing required fields: {missing}")

        item = {
            'item_title': request_body['item_title'],
            'short_description': request_body['short_description'],
            'long_description': request_body['long_description'],
            'product_type': request_body['item_product_type'],
            'image_url': request_body.get('image_url',''),
            'attributes_list': request_body.get('attributes_list',[])
        }
        task_type = request_body.get('task_type','generation')
        self.logger.debug(f"Adapted request into item={item}, task_type={task_type}")
        return item, task_type
