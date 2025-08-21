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
