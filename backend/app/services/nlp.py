from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from functools import lru_cache
from typing import Any

import numpy as np

try:
    import faiss  # type: ignore
except Exception:  # pragma: no cover
    faiss = None


@lru_cache(maxsize=1)
def get_spacy_nlp():
    try:
        import spacy

        return spacy.load("en_core_web_sm")
    except Exception:
        return None


@lru_cache(maxsize=1)
def get_sentence_model():
    try:
        from sentence_transformers import SentenceTransformer

        return SentenceTransformer("all-MiniLM-L6-v2")
    except Exception:
        return None


@lru_cache(maxsize=1)
def get_nli_model():
    try:
        from transformers import pipeline

        return pipeline("text-classification", model="cross-encoder/nli-deberta-v3-base")
    except Exception:
        return None


CATEGORIES: dict[str, list[str]] = {
    "Academic / Research": ["abstract", "methodology", "experiment", "citation"],
    "Legal / Contract": ["agreement", "party", "clause", "liability", "contract"],
    "Financial / Invoice": ["invoice", "amount", "tax", "gst", "balance", "payment"],
    "Technical / Engineering": ["architecture", "api", "deployment", "system", "module"],
    "HR / Resume": ["experience", "skills", "education", "curriculum", "resume"],
    "General Business": ["meeting", "business", "strategy", "customer", "project"],
}


def classify_document(text: str) -> str:
    lowered = text.lower()
    best_label = "General Business"
    best_score = -1
    for label, words in CATEGORIES.items():
        score = sum(lowered.count(w) for w in words)
        if score > best_score:
            best_score = score
            best_label = label
    return best_label


def _sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p.strip() for p in parts if p.strip()]


def summarize_text(text: str, category: str) -> str:
    sents = _sentences(text)
    if not sents:
        return "No readable text extracted from the document."
    lead = sents[: min(4, len(sents))]
    if category in {"Financial / Invoice", "Legal / Contract", "Technical / Engineering"}:
        bullets = "\n".join(f"- {s}" for s in lead)
        return f"Category: {category}\nKey points:\n{bullets}"
    return " ".join(lead)


def extract_entities(text: str) -> list[dict[str, Any]]:
    nlp = get_spacy_nlp()
    entities: list[dict[str, Any]] = []
    if nlp:
        doc = nlp(text)
        for ent in doc.ents:
            entities.append({"text": ent.text, "label": ent.label_})
    if not entities:
        for m in re.finditer(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2}\b", text):
            entities.append({"text": m.group(0), "label": "PROPN"})
    return entities[:200]


def chunk_text(text: str, chunk_size: int = 600) -> list[str]:
    cleaned = re.sub(r"\s+", " ", text).strip()
    if not cleaned:
        return []
    chunks = []
    start = 0
    while start < len(cleaned):
        end = min(start + chunk_size, len(cleaned))
        cut = cleaned.rfind(" ", start, end)
        if cut <= start:
            cut = end
        chunks.append(cleaned[start:cut].strip())
        start = cut
    return [c for c in chunks if c]


def embed_texts(texts: list[str]) -> np.ndarray:
    if not texts:
        return np.zeros((0, 384), dtype=np.float32)
    model = get_sentence_model()
    if model:
        vectors = model.encode(texts, normalize_embeddings=True)
        return np.array(vectors, dtype=np.float32)
    arr = np.zeros((len(texts), 384), dtype=np.float32)
    for i, t in enumerate(texts):
        for token in re.findall(r"\w+", t.lower()):
            arr[i, hash(token) % 384] += 1.0
    norms = np.linalg.norm(arr, axis=1, keepdims=True)
    norms[norms == 0] = 1
    return arr / norms


def vector_to_json(vec: np.ndarray) -> str:
    return json.dumps([float(x) for x in vec.tolist()])


def vector_from_json(raw: str) -> np.ndarray:
    data = json.loads(raw or "[]")
    return np.array(data, dtype=np.float32)


def _keyword_score(query: str, text: str) -> float:
    q_words = {w for w in re.findall(r"\w+", query.lower()) if len(w) > 2}
    if not q_words:
        return 0.0
    t_words = set(re.findall(r"\w+", text.lower()))
    return len(q_words & t_words) / len(q_words)


def hybrid_search(query: str, chunks: list[dict[str, Any]], top_k: int) -> list[dict[str, Any]]:
    if not chunks:
        return []
    q_vec = embed_texts([query])[0]
    c_vecs = np.array([c["vector"] for c in chunks], dtype=np.float32)

    if faiss is not None and len(c_vecs):
        index = faiss.IndexFlatIP(c_vecs.shape[1])
        index.add(c_vecs)
        scores, idxs = index.search(np.array([q_vec], dtype=np.float32), min(top_k * 3, len(chunks)))
        candidates = [(float(scores[0][i]), int(idxs[0][i])) for i in range(len(idxs[0])) if idxs[0][i] >= 0]
    else:
        sims = c_vecs @ q_vec
        order = np.argsort(-sims)[: min(top_k * 3, len(chunks))]
        candidates = [(float(sims[i]), int(i)) for i in order]

    scored: list[tuple[float, dict[str, Any]]] = []
    for sim, idx in candidates:
        chunk = chunks[idx]
        lexical = _keyword_score(query, chunk["content"])
        score = (0.75 * sim) + (0.25 * lexical)
        item = dict(chunk)
        item["score"] = round(score, 4)
        scored.append((score, item))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [item for _, item in scored[:top_k]]


def answer_question(question: str, evidence_chunks: list[dict[str, Any]]) -> dict[str, Any]:
    if not evidence_chunks:
        return {
            "answer": "I could not find supporting evidence in the uploaded documents.",
            "grounded": False,
            "sources": [],
        }
    top = evidence_chunks[0]
    answer = top["content"]
    if len(answer) > 350:
        answer = answer[:347] + "..."
    return {
        "answer": answer,
        "grounded": True,
        "sources": [
            {
                "document_id": c["document_id"],
                "document_name": c["document_name"],
                "page_number": c["page_number"],
                "score": c["score"],
            }
            for c in evidence_chunks
        ],
    }


MONEY_RE = re.compile(r"(?:₹|rs\.?|inr|\$|€)\s?([\d,]+(?:\.\d+)?)", re.I)
DATE_RE = re.compile(r"\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}-\d{2}-\d{2})\b")
NUMBER_RE = re.compile(r"\b\d+(?:\.\d+)?\b")
RESP_RE = re.compile(r"\b(responsible|owner|assigned to|lead by|managed by)\s+([A-Z][a-z]+(?:\s[A-Z][a-z]+)*)", re.I)


@dataclass
class StatementFeatures:
    money: float | None
    date: str | None
    numbers: list[float]
    responsible: str | None


def _first_number(text: str) -> float | None:
    m = MONEY_RE.search(text)
    if not m:
        return None
    try:
        return float(m.group(1).replace(",", ""))
    except ValueError:
        return None


def extract_statement_features(text: str) -> StatementFeatures:
    nums = []
    for m in NUMBER_RE.findall(text):
        try:
            nums.append(float(m))
        except ValueError:
            continue
    date_match = DATE_RE.search(text)
    resp_match = RESP_RE.search(text)
    return StatementFeatures(
        money=_first_number(text),
        date=date_match.group(0) if date_match else None,
        numbers=nums,
        responsible=resp_match.group(2) if resp_match else None,
    )


def local_nli_relation(premise: str, hypothesis: str) -> tuple[str, float, str]:
    model = get_nli_model()
    if model:
        output = model(f"{premise} [SEP] {hypothesis}")
        label = output[0]["label"].lower()
        if "contradiction" in label:
            return "Contradiction", float(output[0]["score"]), "NLI model detected contradiction."
        if "entail" in label:
            return "Entailment", float(output[0]["score"]), "NLI model indicates entailment."
        return "Neutral", float(output[0]["score"]), "NLI model indicates neutral relation."

    f1 = extract_statement_features(premise)
    f2 = extract_statement_features(hypothesis)

    if f1.money is not None and f2.money is not None and not math.isclose(f1.money, f2.money, rel_tol=0.01):
        return "Contradiction", 0.84, "Potential numerical inconsistency in monetary amounts."
    if f1.date and f2.date and f1.date != f2.date:
        return "Contradiction", 0.78, "Potential inconsistency in date values."
    if f1.responsible and f2.responsible and f1.responsible.lower() != f2.responsible.lower():
        return "Contradiction", 0.73, "Potential inconsistency in ownership/responsibility statement."
    if set(f1.numbers) and set(f2.numbers) and set(f1.numbers).intersection(set(f2.numbers)):
        return "Entailment", 0.62, "Statements share overlapping numeric facts."
    return "Neutral", 0.55, "No strong contradiction indicators found."
