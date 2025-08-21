"""Database connection and schema management for DuckDB."""
from datetime import datetime
from pathlib import Path
import os
from time import perf_counter
from typing import Any, Dict, Tuple
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
    conn.execute(
        """
	CREATE TABLE IF NOT EXISTS transactions(
		transaction_id VARCHAR,
		user_id INTEGER,
		product_id INTEGER,
		"timestamp" TIMESTAMP,
		transaction_amount DECIMAL(12,2)
	);
	"""
    )


def _table_count(conn: duckdb.DuckDBPyConnection) -> int:
    """Get the count of rows in the transactions table."""
    result = conn.execute("SELECT COUNT(*) FROM transactions").fetchone()
    return result[0] if result else 0


def load_csv(
    conn: duckdb.DuckDBPyConnection, csv_path: str, replace: bool
) -> Tuple[int, float, bool]:
    """Load a CSV file into the transactions table."""
    start_time = perf_counter()
    if replace:
        conn.execute("DELETE FROM transactions;")  # clear the table if replace True

    initial_tx_count = _table_count(conn)

    conn.execute(
        """
    INSERT INTO transactions
    SELECT
        transaction_id::VARCHAR,
		user_id::INTEGER,
		product_id::INTEGER,
		"timestamp"::TIMESTAMP,
		transaction_amount::DECIMAL(12,2)
	FROM read_csv_auto(?, header=True, sample_size=-1);
	""",
        [csv_path],
    )

    new_tx_count = _table_count(conn)
    execution_time = perf_counter() - start_time
    rows_added = new_tx_count if replace else new_tx_count - initial_tx_count
    return (rows_added, execution_time, bool(replace))


def summarise_user(
    conn: duckdb.DuckDBPyConnection,
    user_id: int,
    start_dt: datetime,
    end_dt: datetime,
) -> Dict[str, Any]:
    """Return a summary of transaction statistics for a user."""
    result = conn.execute(
        """
    SELECT
        COUNT(*)::BIGINT as count,
        MIN(transaction_amount) AS min,
        MAX(transaction_amount) AS max,
        AVG(transaction_amount) AS mean
    FROM transactions
    WHERE user_id = ?
        AND "timestamp" BETWEEN ? AND ?
    """,
        [user_id, start_dt, end_dt],
    ).fetchone()
    return {
        "count": int(result[0]),
        "min": result[1],
        "max": result[2],
        "mean": result[3],
    }
