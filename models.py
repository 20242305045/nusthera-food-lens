from pydantic import BaseModel, Field


class FoodItem(BaseModel):
    name: str
    grams: float = Field(gt=0)
    confidence: float = Field(ge=0, le=1)


class FoodAnalysis(BaseModel):
    items: list[FoodItem]
    notes: str = ""