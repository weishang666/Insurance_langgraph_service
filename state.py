from pydantic import BaseModel, Field
from typing import List, Optional, Dict

class State(BaseModel):
    messages: List[Dict] = Field(default_factory=list)
    product_data: Optional[Dict] = None
    current_step: str = "start"
    extracted_data: Optional[Dict] = None
    error: Optional[str] = None
    current_node: Optional[str] = None
    next_node: Optional[str] = None
    class Config:
        arbitrary_types_allowed = True