# schemas/enrichment.py
from typing import List, Optional
from pydantic import BaseModel, Field

class EnrichItemRequest(BaseModel):
    """
    Input model for enrichment.
    """
    title: str = Field(..., description="Title of the item.")
    short_desc: str = Field(..., description="Short description of the item.")
    long_desc: str = Field(..., description="Long description of the item.")
    product_type: str = Field(..., description="Category/type of the item.")

    # Optional fields
    blurb: Optional[str] = Field("", description="Optional marketing blurb or tagline.")
    image_url: Optional[str] = Field("", description="Optional URL to an image for the item.")
    attributes_list: List[str] = Field(default_factory=list, description="Optional list of known attributes.")
    task_type: str = Field("generation", description="Task type: 'generation' or 'evaluation'. Defaults to 'generation'.")


class EnrichItemResponse(BaseModel):
    """
    Represents the enriched output for the item.
    """
    title_enrichment: Optional[str] = Field(None, description="Enriched or generated title.")
    short_desc_enrichment: Optional[str] = Field(None, description="Enriched or generated short description.")
    long_desc_enrichment: Optional[str] = Field(None, description="Enriched or generated long description.")
    attributes_enrichment: List[AttributeEnrichment] = Field(
        default_factory=list,
        description="List of attribute-value pairs (e.g., color, size, etc.)"
    )

class AttributeEnrichment(BaseModel):
    """
    Represents a single extracted attribute with its value.
    For example: { "name": "color", "value": "red" }
    """
    name: str = Field(..., description="Name of the attribute.")
    value: Any = Field(..., description="Extracted or generated value for the attribute.")
