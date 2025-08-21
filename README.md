## Transaction Service

FastAPI service that ingests a CSV of transactions and returns per-user stats within an optional date range.

## Quick start

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn --reload app.main:app --app-dir src
```

## Docs

Visit `/docs` or `/redoc`.

For example, `http://127.0.0.1:8000/docs/`.

## Environment

`DUCKDB_PATH` (optional): path to DB file. Default: `data/transactions.duckdb`.

## API

### POST /upload

Ingest a CSV with header:
`transaction_id,user_id,product_id,timestamp,transaction_amount`

Query:

- `replace` (bool, default: `false`): clear all existing rows first

Responses:

- `200` `{rows, seconds, replaced}`: Success - rows added, time taken, whether or not all rows were replaced.
- `400`: invalid header or empty CSV
- `415`: invalid media type

Example:

```bash
curl -s -F "file=@sample.csv;type=text/csv" "http://127.0.0.1:8000/upload?replace=true"
```

### GET /summary/{user_id}

Query:

- `start` (ISO date, default: `1970-01-01`): inclusive start date for user summary
- `end` (ISO date, default: `9999-12-31`): inclusive end date for user summary

Responses:

- `200` `{user_id, start, end, count, min, max, mean, most_purchased_product_id}`: User ID, date range, stats summary
- `404`: no rows for user (in date range)
- `422`: start date after end date

Example:

```bash
curl -s "http://127.0.0.1:8000/summary/2"
curl -s "http://127.0.0.1:8000/summary/1?start=2024-01-01&end=2024-01-31"
```

## Testing

```bash
pytest -q
```

## Architecture & Flow

1. Upload a CSV (`/upload`).
2. File streamed to a secure temp file (chunked) so as to not load entire payload in memory.
3. Header validated against strict expected set (case and order insensitive).
4. DuckDB `INSERT ... SELECT FROM read_csv_auto` ingests and casts rows directly into the persisted table.
5. Optional `replace=true` clears table before ingest.
6. Client queries per-user aggregate stats via `/summary/{user_id}` with optional `start` / `end` inclusive date filters.
7. Summary SQL computes count, min, max, mean, and most purchased product (determined in order of highest count → most recent purchase timestamp → lowest product_id (deterministic tiebreak)).

All state stored locally in a single DuckDB file, which enables batch processing without an external DB dependency.

## Data Model

```
transactions(
	transaction_id       VARCHAR,          -- not currently constrained unique
	user_id              INTEGER,
	product_id           INTEGER,
	timestamp            TIMESTAMP,        -- provided in CSV (assumed UTC / ISO8601 with optional Z)
	transaction_amount   DECIMAL(12,2)
)
```

Assumptions:

- No de-duplication of `transaction_id` (appends unless `replace=true`).
- Timestamps treated as UTC.
- Transaction amount precision is 2 decimal places.

## Example Request / Response

Upload:

```bash
curl -s -F "file=@sample.csv;type=text/csv" "http://127.0.0.1:8000/upload?replace=true" | jq
```

Sample response:

```json
{
  "rows": 123456,
  "seconds": 4.2371,
  "replaced": true
}
```

Summary:

```bash
curl -s "http://127.0.0.1:8000/summary/42?start=2024-01-01&end=2024-02-01" | jq
```

Sample response:

```json
{
  "user_id": 42,
  "start": "2024-01-01T00:00:00",
  "end": "2024-02-01T23:59:59",
  "count": 3,
  "min": "9.99",
  "max": "20.01",
  "mean": "13.33",
  "most_purchased_product_id": 10
}
```

(Decimal values serialized as strings to preserve precision.)

## Design Choices

- **DuckDB**: Small, single-file OLAP engine supports vectorised CSV ingestion and high speed SQL aggregation. Chosen due to the challenge's requirements for simple, scalable analytics.
- **`read_csv_auto` + CAST**: DuckDB automatically infers types, I run `ensure_schema` on startup to ensure consistency.
- **Temp file buffering**: Chunking keeps memory bounded for large uploads instead of reading entire file into memory.
- **Deterministic tie-break**: Easily understandable, deterministic “most recently purchased” semantics. highest count → most recent purchase timestamp → lowest product_id
- **Stateless API layer**: All state in DuckDB file, avoiding need for shared storage or external dependencies.
- **Simple replace semantics**: `replace=true` offers easy full reload, particularly useful when testing.

## Testing Approach

- Pytest: header validation, media type handling, happy path ingestion, date filtering, tie-break correctness, and error conditions.
- Uses a per-test temporary DuckDB path via `DUCKDB_PATH`.
