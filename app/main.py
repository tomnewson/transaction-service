"""Main application entry point for the Transactions Service.
This module initializes the FastAPI application and sets up the database connection."""
from contextlib import asynccontextmanager
from datetime import date, datetime, time
from typing import Optional
from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.responses import JSONResponse

from app.db import ensure_schema, get_connection, load_csv, summarise_user
from app.models import SummaryResponse, UploadResponse
from app.utils import allowed_csv_mimetype, validate_csv_headers, write_upload_to_temp

@asynccontextmanager
async def lifespan(_):
    """Application lifespan event to manage database connection and schema."""
    # Startup code
    con = get_connection()
    ensure_schema(con)
    con.close()
    yield
    # Shutdown code

app = FastAPI(title="Transactions Service", lifespan=lifespan)

@app.get("/health")
def health_check() -> JSONResponse:
    """Health check endpoint."""
    return JSONResponse(content={"status": "ok"})

@app.post("/upload", response_model=UploadResponse)
async def upload_csv(file: UploadFile = File(...), replace: bool = Query(False)) -> UploadResponse:
    """Upload a CSV file."""
    if not allowed_csv_mimetype(file.content_type):
        raise HTTPException(status_code=415, detail="Unsupported media type. Provide a CSV file.")

    tmp_path = await write_upload_to_temp(file)
    try:
        validate_csv_headers(tmp_path)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    conn = get_connection()
    ensure_schema(conn)
    rows, seconds, replaced = load_csv(conn, tmp_path, replace)
    return UploadResponse(rows=rows, seconds=seconds, replaced=replaced)

@app.get("/summary/{user_id}", response_model=SummaryResponse)
def get_summary(
	user_id: int,
	start: Optional[date] = Query(None, description="Inclusive start date (YYYY-MM-DD)"),
	end: Optional[date] = Query(None, description="Inclusive end date (YYYY-MM-DD)")
) -> SummaryResponse:
    """Get transaction summary for a user."""
    if start and end and start > end:
        raise HTTPException(status_code=422, detail="start must be on or before end")
    # convert dates to datetime
    start_dt = datetime.combine(start, time.min) if start else datetime(1970, 1, 1, 0, 0, 0)
    end_dt = datetime.combine(end, time.max) if end else datetime(9999, 12, 31, 23, 59, 59)

    conn = get_connection()
    ensure_schema(conn)
    result = summarise_user(conn, user_id, start_dt, end_dt)
    if result["count"] == 0:
        raise HTTPException(status_code=404, detail="No transactions for user in range")
    return SummaryResponse(
        user_id=user_id,
        start=start_dt,
        end=end_dt,
        count=result["count"],
        min=result["min"],
        max=result["max"],
        mean=result["mean"]
    )
