"""Unit tests for handling of different media types"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture(name="client")
def _client(tmp_path, monkeypatch):
    """Test client for FastAPI."""
    monkeypatch.setenv("DUCKDB_PATH", str(tmp_path / "mime.duckdb"))
    return TestClient(app)

def test_unsupported_media_type(client: TestClient):
    """Test unsupported media type."""
    files = {"file": ("x.txt", b"not a csv", "text/plain")}
    r = client.post("/upload", files=files)
    assert r.status_code == 415

def test_allowed_csv_mimetype(client: TestClient):
    """Test allowed CSV media type."""
    csv_data = """transaction_id,user_id,product_id,timestamp,transaction_amount
a1,1,10,2024-03-01T00:00:00Z,100.00
a2,1,11,2024-03-15T00:00:00Z,200.00
"""
    files = {"file": ("x.csv", csv_data, "text/csv")}
    r = client.post("/upload", files=files)
    assert r.status_code == 200
