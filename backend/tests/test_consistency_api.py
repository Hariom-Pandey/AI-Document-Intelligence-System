import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db.database import SessionLocal, init_db
from app.db import repository

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_db():
    init_db()


def test_api_consistency_full_workflow():
    db = SessionLocal()
    # 1. Create two test documents in the database with extracted_text
    doc_a = repository.create_document(
        db, 
        filename="Agreement_Alpha.txt", 
        file_path="uploads/test_alpha.txt", 
        file_type="txt", 
        file_size=120
    )
    doc_a.extracted_text = "The contract duration is 6 months starting January 2026. Phase one budget is ₹5,00,000."
    
    doc_b = repository.create_document(
        db, 
        filename="Agreement_Beta.txt", 
        file_path="uploads/test_beta.txt", 
        file_type="txt", 
        file_size=120
    )
    doc_b.extracted_text = "The contract duration is 18 months starting January 2026. Phase one budget is ₹9,00,000."
    db.commit()
    db.refresh(doc_a)
    db.refresh(doc_b)

    doc_a_id = doc_a.id
    doc_b_id = doc_b.id

    # Add chunks
    repository.save_chunks(db, doc_a_id, [
        {"chunk_index": 0, "text": doc_a.extracted_text, "page_number": 1}
    ])
    repository.save_chunks(db, doc_b_id, [
        {"chunk_index": 0, "text": doc_b.extracted_text, "page_number": 1}
    ])
    db.close()

    analysis_id = None
    try:
        # 2. Test direct pair comparison via POST /api/intelligence/consistency/compare
        compare_payload = {
            "document_a_id": doc_a_id,
            "document_b_id": doc_b_id,
            "min_similarity": 0.40
        }
        resp_compare = client.post("/api/intelligence/consistency/compare", json=compare_payload)
        assert resp_compare.status_code == 200
        compare_data = resp_compare.json()
        assert "total_conflicts" in compare_data
        assert compare_data["total_conflicts"] >= 1
        assert "findings" in compare_data

        # 3. Trigger consistency analysis via POST /api/intelligence/consistency/analyze
        resp_analyze = client.post(
            "/api/intelligence/consistency/analyze",
            json={"document_ids": [doc_a_id, doc_b_id], "min_similarity": 0.40}
        )
        assert resp_analyze.status_code == 200
        analysis_data = resp_analyze.json()
        analysis_id = analysis_data["analysis_id"]
        assert analysis_data["status"] == "completed"
        assert analysis_data["conflict_count"] >= 1

        # 4. Retrieve analysis job status via GET /api/intelligence/consistency/{analysis_id}
        resp_job = client.get(f"/api/intelligence/consistency/{analysis_id}")
        assert resp_job.status_code == 200
        job_data = resp_job.json()
        assert job_data["status"] == "completed"
        assert job_data["conflict_count"] >= 1

        # 5. List conflicts via GET /api/intelligence/conflicts
        resp_conflicts = client.get(f"/api/intelligence/conflicts?analysis_id={analysis_id}")
        assert resp_conflicts.status_code == 200
        conflicts_list = resp_conflicts.json()
        assert len(conflicts_list) >= 1
        conflict_item = conflicts_list[0]
        cid = conflict_item["id"]

        # 6. Get detailed conflict by ID via GET /api/intelligence/conflicts/{cid}
        resp_detail = client.get(f"/api/intelligence/conflicts/{cid}")
        assert resp_detail.status_code == 200
        detail = resp_detail.json()
        assert detail["id"] == cid
        assert "statement_a" in detail
        assert "statement_b" in detail
        assert "evidence_context" in detail

        # 7. Update review status via PATCH /api/intelligence/conflicts/{cid}
        resp_patch = client.patch(
            f"/api/intelligence/conflicts/{cid}",
            json={"review_status": "confirmed_conflict"}
        )
        assert resp_patch.status_code == 200
        patched = resp_patch.json()
        assert patched["review_status"] == "confirmed_conflict"

    finally:
        # Cleanup
        db_clean = SessionLocal()
        if analysis_id:
            repository.delete_conflicts_for_analysis(db_clean, analysis_id)
        repository.delete_document(db_clean, doc_a_id)
        repository.delete_document(db_clean, doc_b_id)
        db_clean.close()
