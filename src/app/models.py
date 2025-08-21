"""Pydantic models for API responses."""
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict

class UploadResponse(BaseModel):
    """Response model for file uploads."""
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
			"example": {"rows": 1000000, "seconds": 12.34, "replaced": True}
		},
    )
    rows: int
    seconds: float
    replaced: bool

class SummaryResponse(BaseModel):
    """Response model for transaction summaries."""
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
			"example": {
				"user_id": 42,
				"start": "2024-01-01T00:00:00",
				"end": "2024-01-31T23:59:59",
				"count": 2,
				"min": "9.99",
				"max": "20.01",
				"mean": "15.00",
			}
		},
    )
    user_id: int
    start: datetime
    end: datetime
    count: int
    min: Decimal | None
    max: Decimal | None
    mean: Decimal | None
