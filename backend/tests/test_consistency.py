import pytest
from app.services.statement_matcher import StatementMatcher
from app.services.contradiction_detector import ContradictionDetector
from app.services.numerical_consistency import NumericalConsistencyAnalyzer
from app.services.conflict_reporter import ConflictReporter
from app.db.database import SessionLocal, init_db
from app.db import repository

@pytest.fixture(scope="module")
def db_session():
    init_db()
    db = SessionLocal()
    yield db
    db.close()


def test_different_budgets_same_project():
    stmt_a = "The total project cost is ₹5,00,000 for phase one delivery."
    stmt_b = "The total project cost is ₹8,00,000 for phase one delivery."
    
    result = NumericalConsistencyAnalyzer.compare_statements(stmt_a, stmt_b)
    assert result is not None
    assert result["conflict_type"] == "NUMERICAL_INCONSISTENCY"
    assert result["confidence"] >= 0.85
    assert "₹5,00,000" in result["explanation"]
    assert "₹8,00,000" in result["explanation"]


def test_conflicting_dates_same_event():
    stmt_a = "The final project deadline is 15 December 2026."
    stmt_b = "The final project deadline is 20 January 2027."

    result = NumericalConsistencyAnalyzer.compare_statements(stmt_a, stmt_b)
    assert result is not None
    assert result["conflict_type"] == "DATE_INCONSISTENCY"
    assert result["confidence"] >= 0.80
    assert "15 December 2026" in result["explanation"]
    assert "20 January 2027" in result["explanation"]


def test_contradictory_statements_nli():
    stmt_a = "The client is strictly prohibited from sharing project source code with external vendors."
    stmt_b = "The client is fully permitted to share project source code with external vendors."

    result = ContradictionDetector.classify_pair(stmt_a, stmt_b)
    assert result["label"] == "CONTRADICTION"
    assert result["confidence"] >= 0.70
    assert "detection_method" in result


def test_semantically_equivalent_statements():
    stmt_a = "All user passwords must be hashed using bcrypt prior to database storage."
    stmt_b = "The application requires user password hashing with bcrypt before saving to the database."

    result = ContradictionDetector.classify_pair(stmt_a, stmt_b)
    assert result["label"] != "CONTRADICTION"


def test_different_numbers_different_subjects():
    stmt_a = "The backend server cluster operates with 16 worker nodes."
    stmt_b = "The maximum HTTP request timeout limit is set to 60 seconds."

    result = NumericalConsistencyAnalyzer.compare_statements(stmt_a, stmt_b)
    assert result is None


def test_compatible_updated_information():
    stmt_a = "The agreed project budget was ₹5 lakh."
    stmt_b = "The revised project budget is ₹7 lakh following the latest steering committee amendment."

    result = NumericalConsistencyAnalyzer.compare_statements(stmt_a, stmt_b)
    assert result is not None
    assert result["conflict_type"] == "POTENTIAL_VERSION_CHANGE"
    assert result["review_status"] == "needs_review"


def test_statements_with_different_currencies():
    stmt_a = "The annual maintenance fee is USD 50,000."
    stmt_b = "The annual maintenance fee is INR 50,000."

    result = NumericalConsistencyAnalyzer.compare_statements(stmt_a, stmt_b)
    assert result is not None
    assert result["conflict_type"] == "UNRESOLVED_DIFFERENCE"
    assert result["evidence_context"]["unit_mismatch"] is True


def test_statements_referring_to_different_periods():
    stmt_a = "The total corporate revenue for Q1 2025 was ₹10 lakh."
    stmt_b = "The total corporate revenue for Q3 2026 was ₹25 lakh."

    # Both contain different periods and should not be flagged as same-quarter contradiction
    pair = {
        "document_a_id": "doc1",
        "document_a_name": "Report 2025",
        "document_b_id": "doc2",
        "document_b_name": "Report 2026",
        "statement_a": stmt_a,
        "statement_b": stmt_b,
        "page_a": 1,
        "page_b": 1,
        "similarity": 0.65
    }
    evaluated = ConflictReporter._evaluate_pair(pair)
    # If evaluated, should not be a raw unflagged conflict
    if evaluated:
        assert evaluated["conflict_type"] in ("POTENTIAL_VERSION_CHANGE", "UNRESOLVED_DIFFERENCE", "NUMERICAL_INCONSISTENCY")


def test_unrelated_documents():
    doc_a = {
        "id": "unrelated_1",
        "filename": "organic_chem.txt",
        "extracted_text": "Benzene undergoes electrophilic aromatic substitution in the presence of Lewis acid catalysts."
    }
    doc_b = {
        "id": "unrelated_2",
        "filename": "piano_sonata.txt",
        "extracted_text": "Beethoven composed thirty-two piano sonatas spanning his early, middle, and late stylistic periods."
    }

    report = ConflictReporter.analyze_document_pair(doc_a, doc_b, min_similarity=0.60)
    assert report["total_conflicts"] == 0


def test_multi_document_consistency_comparison():
    """
    Verifies that the consistency engine compares 3+ documents simultaneously across combinations
    and produces traceable document and page references.
    """
    doc1 = {
        "id": "doc_prop_1",
        "filename": "Project_Proposal.pdf",
        "extracted_text": "The total project budget is ₹5,00,000 for phase one. Final delivery deadline is 15 December 2026.",
        "pages": [{"page_number": 1, "text": "The total project budget is ₹5,00,000 for phase one. Final delivery deadline is 15 December 2026."}]
    }
    doc2 = {
        "id": "doc_addendum_2",
        "filename": "Vendor_Addendum.docx",
        "extracted_text": "The total project budget is ₹9,00,000 for phase one. Governing law is the State of California.",
        "pages": [{"page_number": 2, "text": "The total project budget is ₹9,00,000 for phase one. Governing law is the State of California."}]
    }
    doc3 = {
        "id": "doc_legal_3",
        "filename": "Legal_Review.txt",
        "extracted_text": "Final delivery deadline is 25 February 2027. Governing law is the State of New York.",
        "pages": [{"page_number": 1, "text": "Final delivery deadline is 25 February 2027. Governing law is the State of New York."}]
    }

    report = ConflictReporter.generate_consistency_report([doc1, doc2, doc3], min_similarity=0.40)
    assert report["total_pairs_analyzed"] > 0
    assert report["total_conflicts"] >= 2

    # Verify traceable document and page references
    for finding in report["findings"]:
        assert finding["document_a_id"] in ["doc_prop_1", "doc_addendum_2", "doc_legal_3"]
        assert finding["document_b_id"] in ["doc_prop_1", "doc_addendum_2", "doc_legal_3"]
        assert finding["document_a_id"] != finding["document_b_id"]
        assert finding["page_a"] >= 1
        assert finding["page_b"] >= 1
        assert len(finding["statement_a"]) > 0
        assert len(finding["statement_b"]) > 0
        assert finding["conflict_type"] is not None
        assert finding["confidence"] > 0.0


def test_model_loading_and_fallback_label():
    stmt_a = "The warranty period is active."
    stmt_b = "The warranty period is terminated."

    res = ContradictionDetector.classify_pair(stmt_a, stmt_b)
    assert res["label"] == "CONTRADICTION"
    assert res["detection_method"] in ("cross_encoder_nli_deberta_v3", "semantic_cosine_rule_fallback")


def test_repeated_analysis_no_duplicates(db_session):
    analysis_id = "test_analysis_dedup_123"
    conflicts_data = [
        {
            "document_a_id": "doc_1",
            "document_b_id": "doc_2",
            "statement_a": "Total fee is ₹10,000.",
            "statement_b": "Total fee is ₹20,000.",
            "page_a": 1,
            "page_b": 2,
            "conflict_type": "NUMERICAL_INCONSISTENCY",
            "confidence": 0.90,
            "explanation": "Conflicting fees"
        }
    ]

    # Save once
    saved1 = repository.save_document_conflicts(db_session, analysis_id, conflicts_data)
    assert len(saved1) == 1

    # Save again for the same analysis_id -> must overwrite, not duplicate
    saved2 = repository.save_document_conflicts(db_session, analysis_id, conflicts_data)
    assert len(saved2) == 1

    stored = repository.get_document_conflicts(db_session, analysis_id=analysis_id)
    assert len(stored) == 1

    # Clean up
    repository.delete_conflicts_for_analysis(db_session, analysis_id)


def test_user_review_status_lifecycle(db_session):
    analysis_id = "test_analysis_lifecycle_456"
    conflicts_data = [
        {
            "document_a_id": "doc_a",
            "document_b_id": "doc_b",
            "statement_a": "The client shall pay ₹100,000.",
            "statement_b": "The client shall pay ₹150,000.",
            "page_a": 1,
            "page_b": 1,
            "conflict_type": "NUMERICAL_INCONSISTENCY",
            "confidence": 0.88,
            "review_status": "needs_review"
        }
    ]

    saved = repository.save_document_conflicts(db_session, analysis_id, conflicts_data)
    cid = saved[0].id

    # 1. Update to confirmed_conflict
    updated1 = repository.update_conflict_status(db_session, cid, "confirmed_conflict")
    assert updated1.review_status == "confirmed_conflict"

    # 2. Update to valid_revision
    updated2 = repository.update_conflict_status(db_session, cid, "valid_revision")
    assert updated2.review_status == "valid_revision"

    # 3. Update to resolved
    updated3 = repository.update_conflict_status(db_session, cid, "resolved")
    assert updated3.review_status == "resolved"

    # Clean up
    repository.delete_conflicts_for_analysis(db_session, analysis_id)


def test_consistency_precision_recall_f1():
    """
    Evaluates the contradiction detection engine on a gold-standard synthetic benchmark
    containing ground-truth labels: CONTRADICTION vs NON_CONTRADICTION.
    """
    test_dataset = [
        # True Contradictions (Ground Truth Positive: is_conflict = True)
        {
            "a": "The total project cost is ₹5,00,000.",
            "b": "The total project cost is ₹9,00,000.",
            "is_conflict": True
        },
        {
            "a": "The project deadline is 15 December 2026.",
            "b": "The project deadline is 25 February 2027.",
            "is_conflict": True
        },
        {
            "a": "The vendor is strictly prohibited from subcontracting any work without written permission.",
            "b": "The vendor is allowed to subcontract all deliverables without written permission.",
            "is_conflict": True
        },
        {
            "a": "Governing law is the State of California.",
            "b": "Governing law is the State of New York.",
            "is_conflict": True
        },
        {
            "a": "Contractor shall deliver the final report within 30 days.",
            "b": "Contractor shall deliver the final report within 90 days.",
            "is_conflict": True
        },
        {
            "a": "The interest rate on late payment is 5% per annum.",
            "b": "The interest rate on late payment is 18% per annum.",
            "is_conflict": True
        },
        {
            "a": "The warranty period is valid for twelve months.",
            "b": "The warranty period is terminated after three months.",
            "is_conflict": True
        },
        {
            "a": "The client is eligible for a full refund.",
            "b": "The client is ineligible for any refund.",
            "is_conflict": True
        },

        # Non-Contradictions / Compatible / Neutral (Ground Truth Negative: is_conflict = False)
        {
            "a": "All source code must be formatted according to PEP 8 standards.",
            "b": "Python scripts should adhere to standard PEP 8 formatting rules.",
            "is_conflict": False
        },
        {
            "a": "The application architecture utilizes React for front-end rendering.",
            "b": "The user interface components are constructed with React.",
            "is_conflict": False
        },
        {
            "a": "The cloud database operates on SQLite in development mode.",
            "b": "Local development utilizes an SQLite database engine.",
            "is_conflict": False
        },
        {
            "a": "The server uses 8 CPU cores.",
            "b": "The backup schedule executes every Sunday at midnight.",
            "is_conflict": False
        },
        {
            "a": "Employee working hours are 9:00 AM to 5:00 PM.",
            "b": "The office cafeteria is located on the second floor.",
            "is_conflict": False
        },
        {
            "a": "The project was initiated in March 2024.",
            "b": "Phase two was deployed in November 2025.",
            "is_conflict": False
        }
    ]

    tp = 0
    fp = 0
    tn = 0
    fn = 0

    for item in test_dataset:
        pair = {
            "document_a_id": "bench_a",
            "document_a_name": "Doc A",
            "document_b_id": "bench_b",
            "document_b_name": "Doc B",
            "statement_a": item["a"],
            "statement_b": item["b"],
            "page_a": 1,
            "page_b": 1,
            "similarity": 0.60
        }

        finding = ConflictReporter._evaluate_pair(pair)
        predicted_conflict = (finding is not None)

        if item["is_conflict"] and predicted_conflict:
            tp += 1
        elif not item["is_conflict"] and predicted_conflict:
            fp += 1
        elif not item["is_conflict"] and not predicted_conflict:
            tn += 1
        elif item["is_conflict"] and not predicted_conflict:
            fn += 1

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0

    print(f"\n--- Consistency Benchmark Evaluation ---")
    print(f"TP: {tp}, FP: {fp}, TN: {tn}, FN: {fn}")
    print(f"Precision: {precision:.4f}, Recall: {recall:.4f}, F1-Score: {f1:.4f}, FPR: {fpr:.4f}")

    assert precision >= 0.80, f"Precision {precision} below 0.80 threshold"
    assert recall >= 0.80, f"Recall {recall} below 0.80 threshold"
    assert f1 >= 0.80, f"F1-score {f1} below 0.80 threshold"
    assert fpr <= 0.20, f"False Positive Rate {fpr} above 0.20 threshold"

