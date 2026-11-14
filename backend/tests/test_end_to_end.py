import os
import pytest
from app.db.database import SessionLocal, init_db
from app.db import repository
from app.services.document_service import DocumentService
from app.services.qa_service import QAService
from app.services.retriever import DocumentRetriever

def test_full_pipeline_end_to_end():
    init_db()
    db = SessionLocal()

    # Step 1: Ingest sample contract
    possible_paths = [
        os.path.abspath("data/sample_contract.txt"),
        os.path.abspath("../data/sample_contract.txt"),
        os.path.join(os.path.dirname(__file__), "../../data/sample_contract.txt")
    ]
    sample_path = next((p for p in possible_paths if os.path.exists(p)), None)
    assert sample_path is not None and os.path.exists(sample_path), "Sample contract file must exist."

    with open(sample_path, "rb") as f:
        file_bytes = f.read()

    doc_id, file_path, file_size = DocumentService.save_uploaded_file("sample_contract.txt", file_bytes)
    doc = repository.create_document(
        db=db,
        filename="sample_contract.txt",
        file_path=file_path,
        file_type="txt",
        file_size=file_size,
        doc_id=doc_id
    )
    assert doc.id == doc_id
    print(f"\n[1/5] Ingested document: {doc.id} ({doc.filename})")

    # Step 2: Execute document processing pipeline
    DocumentService.process_document_pipeline(db, doc.id)

    doc_refreshed = repository.get_document(db, doc.id)
    assert doc_refreshed.status == "completed", f"Expected completed status, got {doc_refreshed.status}: {doc_refreshed.error_message}"
    print(f"[2/5] Pipeline completed with page count = {doc_refreshed.page_count}")

    # Step 3: Verify NLP outputs
    results = repository.get_document_results(db, doc.id)
    assert results is not None
    assert results["summary"] is not None
    assert len(results["summary"]["short_summary"]) > 10
    print(f"[3/5] Summary generated:\n  Short: {results['summary']['short_summary'][:120]}...")
    print(f"  Key points count: {len(results['summary']['key_points'])}")

    # Category verification
    assert results["classification"] is not None
    print(f"  Category: {results['classification']['category']} (Confidence: {results['classification']['confidence']})")
    assert results["classification"]["category"] == "Legal / Contract"

    # Entities verification
    assert len(results["entities"]) > 0
    entity_texts = [e["text"] for e in results["entities"]]
    print(f"  Extracted entities count: {len(results['entities'])}")
    print(f"  Sample entities: {entity_texts[:6]}")

    # Step 4: Test Semantic Search
    search_res = DocumentRetriever.retrieve("arbitration rules and monetary damages", document_id=doc.id, top_k=2)
    assert len(search_res) > 0
    print(f"[4/5] Semantic retrieval found {len(search_res)} passages. Top score: {search_res[0]['score']}")

    # Step 5: Test RAG Question Answering with Citations
    qa_res = QAService.answer_question("What is the governing law of the agreement?", document_id=doc.id)
    print(f"[5/5] RAG QA:\n  Question: 'What is the governing law of the agreement?'\n  Answer: {qa_res['answer']}")
    print(f"  Evidence citations count: {len(qa_res['citations'])}")
    assert qa_res["has_evidence"] is True
    assert len(qa_res["citations"]) > 0

    # Test question about liquidated damages
    qa_res2 = QAService.answer_question("What is the amount of liquidated damages for wilful violation?", document_id=doc.id)
    print(f"  Answer 2: {qa_res2['answer']}")
    assert qa_res2["has_evidence"] is True

    print("\n✓ FULL END-TO-END DOCUMENT INTELLIGENCE PIPELINE VERIFIED SUCCESSFULLY!")
    db.close()

if __name__ == "__main__":
    test_full_pipeline_end_to_end()
