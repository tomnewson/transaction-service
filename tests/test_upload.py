"""Unit tests for the transaction upload and summary endpoints."""
import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture(name="client")
def _client(tmp_path, monkeypatch):
    """Test client for FastAPI."""
    monkeypatch.setenv("DUCKDB_PATH", str(tmp_path / "test.duckdb"))
    return TestClient(app)

def _csv_bytes(string: str) -> bytes:
    """Convert a string to bytes."""
    return bytes(string, encoding="utf-8")

def test_rejects_bad_header(client: TestClient):
    """Test CSV rejects upload with invalid header."""
    bad_csv = """transaction_id,user_id,product_id,timestamp,amount
t1,1,10,2024-01-01T10:00:00Z,9.99
"""
    files = {"file": ("bad.csv", _csv_bytes(bad_csv), "text/csv")}
    response = client.post("/upload", files=files)
    assert response.status_code == 400
    assert "Invalid header" in response.text

def test_upload_and_summary_happy_path(client: TestClient):
    """Test CSV upload and summary retrieval."""
    csv_data = """transaction_id,user_id,product_id,timestamp,transaction_amount
t1,42,10,2024-01-01T10:00:00Z,9.99
t2,42,11,2024-01-02T12:30:00Z,20.01
t3,7,12,2024-02-01T09:00:00Z,5.00
t4,42,10,2024-02-01T09:00:01Z,9.99
"""
    files = {"file": ("ok.csv", _csv_bytes(csv_data), "text/csv")}
    r1 = client.post("/upload?replace=true", files=files)
    assert r1.status_code == 200, r1.text
    body = r1.json()
    assert body["replaced"] is True
    assert body["rows"] == 4

    r2 = client.get("/summary/42")
    assert r2.status_code == 200, r2.text
    s = r2.json()
    assert s["user_id"] == 42
    assert s["count"] == 3
    assert float(s["min"]) == pytest.approx(9.99, rel=1e-6)
    assert float(s["max"]) == pytest.approx(20.01, rel=1e-6)
    assert float(s["mean"]) == pytest.approx((9.99 + 20.01 + 9.99) / 3.0, rel=1e-6)
    assert s["most_purchased_product_id"] == 10

def test_summary_date_filters_and_not_found(client: TestClient):
    """Test summary endpoint with date filters, both when found and not found."""
    csv_data = """transaction_id,user_id,product_id,timestamp,transaction_amount
a1,1,10,2024-03-01T00:00:00Z,100.00
a2,1,11,2024-03-15T00:00:00Z,200.00
"""
    files = {"file": ("ok.csv", _csv_bytes(csv_data), "text/csv")}
    client.post("/upload?replace=true", files=files)

    r = client.get("/summary/1?start=2024-04-01&end=2024-04-30")
    assert r.status_code == 404

    r2 = client.get("/summary/1?start=2024-03-10&end=2024-03-31")
    assert r2.status_code == 200
    s = r2.json()
    assert s["count"] == 1
    assert float(s["min"]) == pytest.approx(200.00, rel=1e-6)
    assert float(s["max"]) == pytest.approx(200.00, rel=1e-6)
    assert float(s["mean"]) == pytest.approx(200.00, rel=1e-6)
    assert s["most_purchased_product_id"] == 11

def test_start_after_end_rejected(client: TestClient):
    """Test summary endpoint rejects when start date after end date."""
    r = client.get("/summary/5?start=2024-05-10&end=2024-05-01")
    assert r.status_code == 422

def test_summary_no_transactions(client: TestClient):
    """Test summary endpoint returns 404 when no transactions exist."""
    r = client.get("/summary/999")
    assert r.status_code == 404
    assert r.json()["detail"] == "No transactions for user in range"
