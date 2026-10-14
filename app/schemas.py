from pydantic import BaseModel, ConfigDict, Field


class PriceRead(BaseModel):
    id: int
    ticker: str
    price: float = Field(gt=0)
    timestamp: int

    model_config = ConfigDict(from_attributes=True)
