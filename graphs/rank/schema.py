# graphs/rank/schema.py
from pydantic import BaseModel, Field
from typing import Literal

class ComparisonSchema(BaseModel):
    reasoning: str = Field(..., description="Detailed reasoning process comparing the two stocks.")
    better_stock: Literal['A', 'B'] = Field(..., description="The ticker symbol of the stock that is determined to be more promising based on the analysis.")
