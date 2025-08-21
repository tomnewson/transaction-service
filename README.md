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
- `200` `{user_id, start, end, count, min, max, mean}`: User ID, date range, summary
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

## Notes
- Uses DuckDB's `read_csv_auto` for fast CSV ingestion into database.
- Decimal maths for amounts, serialised as JSON strings by FastAPI.
