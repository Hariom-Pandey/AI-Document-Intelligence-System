import pytest
from app.services.preprocessor import TextPreprocessor
from app.services.classifier import DocumentClassifier
from app.services.ner import EntityExtractor
from app.services.summarizer import DocumentSummarizer

def test_text_cleaner():
    raw = "This is  a   test\r\nwith  spaces\n\n\n\nand newlines."
    cleaned = TextPreprocessor.clean_text(raw)
    assert "  " not in cleaned
    assert "\r" not in cleaned
    assert "\n\n\n" not in cleaned

def test_chunking():
    pages = [
        {"page_number": 1, "text": "Page one text content. It explains machine learning concepts and models in detail."},
        {"page_number": 2, "text": "Page two text content. It deals with natural language processing and tokenization."}
    ]
    chunks = TextPreprocessor.chunk_pages(pages, chunk_size=100, chunk_overlap=20)
    assert len(chunks) >= 2
    assert chunks[0]["page_number"] == 1
    assert "text" in chunks[0]

def test_classifier():
    legal_text = "This non-disclosure agreement (NDA) governs confidential information between parties under law and arbitration."
    result = DocumentClassifier.classify(legal_text)
    assert result["category"] == "Legal / Contract"
    assert result["confidence"] > 0.0

    tech_text = "The microservice architecture exposes REST APIs with Docker containerization and FastAPI endpoints."
    result_tech = DocumentClassifier.classify(tech_text)
    assert result_tech["category"] == "Technical / Engineering"

def test_ner_extractor():
    text = "Apple Inc. announced a new product on October 14, 2026 for $999 in California."
    entities = EntityExtractor.extract_entities(text)
    labels = [e["label"] for e in entities]
    # Check that date or money or org was picked up
    assert any(l in ["DATE", "MONEY", "ORG", "GPE"] for l in labels)

def test_summarizer():
    text = (
        "Artificial intelligence is transforming document workflows across modern enterprises. "
        "Deep learning models enable natural language understanding and automated processing. "
        "Retrieval augmented generation connects pretrained models to domain specific knowledge bases. "
        "Organizations can reduce manual review time significantly with intelligent extraction."
    )
    res = DocumentSummarizer.summarize(text)
    assert len(res["short_summary"]) > 20
    assert len(res["detailed_summary"]) >= len(res["short_summary"])
    assert len(res["key_points"]) > 0

def test_docx_extractor():
    from pathlib import Path
    from app.services.extractor import DocumentExtractor
    doc_path = Path("data/uploads/8c87f2d9-4a90-4593-9f56-50069ea6af1b_Trust_Reliability_AI_Agents_Agile_Review_IEEE_Template.docx")
    if doc_path.exists():
        res = DocumentExtractor.extract(str(doc_path))
        assert res["page_count"] > 0
        assert len(res["full_text"]) > 500
        assert "Trust" in res["full_text"]


