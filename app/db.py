"""Database connection and schema management for DuckDB."""
from pathlib import Path
import os
import duckdb

def get_db_path() -> str:
    """Get the path to the DuckDB database file."""
    db_path = Path(os.getenv("DB_PATH", "data/transactions.duckdb"))
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return str(db_path)

def get_connection() -> duckdb.DuckDBPyConnection:
    """Create and return a connection to the DuckDB database."""
    db_path = get_db_path()
    conn = duckdb.connect(db_path, read_only=False)
    # Increase thread count to match cores for better performance
    conn.execute(f"PRAGMA threads={os.cpu_count() or 2}")
    return conn

def ensure_schema(conn: duckdb.DuckDBPyConnection) -> None:
    """Ensure the database schema is created to match csv"""
    conn.execute("""
	CREATE TABLE IF NOT EXISTS transactions(
		transaction_id VARCHAR,
		user_id INTEGER,
		product_id INTEGER,
		"timestamp" TIMESTAMP,
		transaction_amount DECIMAL(12,2)
	);
	""")
