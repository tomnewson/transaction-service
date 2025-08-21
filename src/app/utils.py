"""Utility functions for handling CSV files."""
import csv
import tempfile
from typing import Set
from fastapi import UploadFile

_EXPECTED_COLUMNS: Set[str] = {
	"transaction_id",
	"user_id",
	"product_id",
	"timestamp",
	"transaction_amount",
}


def allowed_csv_mimetype(mimetype: str | None) -> bool:
    """Check if the provided mimetype is allowed for CSV files."""
    if not mimetype:
        return False
    return mimetype in [
        "text/csv",
        "application/csv",
        "application/vnd.ms-excel",
    ]  # TODO: check for more valid mimetypes


async def write_upload_to_temp(file: UploadFile):
    """Write the uploaded file to a temporary location."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
        while True:
            chunk = await file.read(1024 * 1024)  # Read file in 1MB chunks
            if not chunk:
                break
            tmp.write(chunk)
    return tmp.name


def validate_csv_headers(csv_path: str) -> None:
    """Validate the headers of a CSV file."""
    with open(csv_path, "r", newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        try:
            header = next(reader)
        except StopIteration as exc:  # pragma: no cover - trivial
            raise ValueError("CSV file is empty") from exc
        normalised = {h.strip().strip('"').lower() for h in header}
        if normalised != _EXPECTED_COLUMNS:
            missing_cols = _EXPECTED_COLUMNS - normalised
            extra_cols = normalised - _EXPECTED_COLUMNS
            raise ValueError(
                f"Invalid header. Missing: {sorted(missing_cols)} Extra: {sorted(extra_cols)}"
            )
