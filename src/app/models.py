"""Pydantic models for API responses."""
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict


class UploadResponse(BaseModel):
    """Response model for file uploads."""
    model_config = ConfigDict(from_attributes=True)
    rows: int
    seconds: float
    replaced: bool


class SummaryResponse(BaseModel):
    """Response model for transaction summaries."""
    model_config = ConfigDict(from_attributes=True)
    user_id: int
    start: datetime
    end: datetime
    count: int
    min: Decimal | None
    max: Decimal | None
    mean: Decimal | None
