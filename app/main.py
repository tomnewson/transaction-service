"""Main application entry point for the Transactions Service.
This module initializes the FastAPI application and sets up the database connection."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.db import ensure_schema, get_connection

@asynccontextmanager
async def lifespan(app: FastAPI):
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
