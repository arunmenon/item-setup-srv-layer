# exceptions/custom_exceptions.py

class StylingGuideNotFoundException(Exception):
    """
    Exception raised when a styling guide is not found for the given product type.
    """
    def __init__(self, product_type):
        self.product_type = product_type
        super().__init__(f"No styling guides found for product type: {product_type}")
