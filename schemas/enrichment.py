# schemas/enrichment.py
from typing import List, Optional, Any
from pydantic import BaseModel, Field, validator

class ProductIdentifier(BaseModel):
    """
    Represents an identifier for the product (e.g. GTIN).
    """
    id_type: str = Field(..., description="Type of ID, e.g. 'GTIN'")
    id: str = Field(..., description="Actual identifier string")

class Attributes(BaseModel):
    """
    Defines included or excluded attributes for enrichment.
    """
    inclusions: List[str] = []
    exclusions: List[str] = []

class PayloadItem(BaseModel):
    """
    Represents a single item in the multi-item request.
    Includes product_identifier, specs, etc.
    """
    product_identifier: ProductIdentifier
    spec_product_type: str
    product_name: str
    product_short_description: str
    product_additional_description: str
    main_image_url: Optional[str] = None
    attributes: Optional[Attributes] = None
    additional_data: Optional[dict] = {}

    @validator("spec_product_type", "product_name", "product_short_description", "product_additional_description")
    def not_empty(cls, v):
        if not v:
            raise ValueError("This field cannot be empty")
        return v

class MultiEnrichRequest(BaseModel):
    """
    The top-level multi-item request schema.
    Example:
    {
      "spec_version": "1.0",
      "tenant_id": 123,
      "locale": "en_us",
      "mart_id": 0,
      "payload": [... list of PayloadItem ...]
    }
    """
    spec_version: str
    tenant_id: int
    locale: str
    mart_id: int
    payload: List[PayloadItem]

    @validator("spec_version", "locale")
    def validate_string_fields(cls, v):
        if not v:
            raise ValueError("This field cannot be empty")
        return v

class AttributeEnrichment(BaseModel):
    """
    Represents a single extracted attribute-value pair.
    """
    name: str
    value: Any

class MultiEnrichResponse(BaseModel):
    """
    Example multi-item response structure for all enriched items.
    Adapt as needed for your final success/error layout.
    """
    status: str
    data: Any  # Could store 'success' / 'errors' arrays, etc.
