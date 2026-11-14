import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db.database import init_db

def test_api_endpoints():
    init_db()
    with TestClient(app) as client:
        # 1. Health check
        res = client.get("/api/health")
        assert res.status_code == 200, f"Health check failed: {res.text}"
        print("✓ Health check passed:", res.json())

        # 2. Root
        res = client.get("/")
        assert res.status_code == 200
        print("✓ Root endpoint passed:", res.json()["name"])

        # 3. List documents
        res = client.get("/api/documents")
        assert res.status_code == 200
        print("✓ List documents passed (count:", len(res.json()), ")")

        # 4. Search validation
        res = client.post("/api/search", json={"query": ""})
        assert res.status_code == 400
        print("✓ Search validation passed (empty query rejected with 400)")

        # 5. Invalid upload validation
        res = client.post(
            "/api/documents/upload",
            files={"file": ("test.exe", b"invalid binary", "application/octet-stream")}
        )
        assert res.status_code == 400
        print("✓ Upload validation passed (invalid extension rejected with 400)")

    print("\nALL API TESTS PASSED!")

if __name__ == "__main__":
    test_api_endpoints()
