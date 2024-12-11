# llm_request_models.py
from pydantic import BaseModel, Field
from typing import Dict, List, Union, Optional

class BaseLLMRequest(BaseModel):
    """
    Base request model for interacting with LLMs.

    Attributes:
        prompt (str): The input prompt to be sent to the LLM.
        parameters (Optional[Dict[str, Union[str, int, float]]]): Additional parameters for LLM configuration.
    """
    prompt: str
    parameters: Optional[Dict[str, Union[str, int, float]]] = None

class LLMRequest(BaseModel):
    """
    Request model for enriching an item using multiple LLMs.

    Attributes:
        metadata (Dict[str, Union[str, int, float, List[str]]]): A dictionary containing metadata about the item to be enriched.
        tasks (List[str]): A list of tasks to be performed on the metadata by the LLMs.
    """
    item_title: str
    short_description: str
    long_description: str
    item_product_type: str
    task_type: Optional[str] = 'generation'  # Default to 'generation'
    image_url : Optional[str] = None 
    attributes_list : Optional[List[str]] = None
    #max_tokens: Optional[int] = 150  
    #metadata: Optional[Dict[str, Union[str, int, float, List[str]]]] = None
    #tasks: Optional[List[str]] = None
    
