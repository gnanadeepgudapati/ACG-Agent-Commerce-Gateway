from pydantic import BaseModel, Field


class Address(BaseModel):
    line1: str = Field(min_length=1)
    line2: str | None = None
    city: str = Field(min_length=1)
    state: str | None = None
    postal_code: str = Field(min_length=1)
    country: str = Field(default="US", min_length=2, max_length=2)
