import re
from typing import List, Dict, Any

class TextPreprocessor:
    """
    Normalizes extracted text and creates page-aware overlapping chunks
    using sentence and paragraph boundaries.
    """

    @staticmethod
    def clean_text(text: str) -> str:
        if not text:
            return ""
        # Replace non-breaking spaces and carriage returns
        text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\xa0", " ")
        # Remove consecutive duplicate whitespace within lines
        text = re.sub(r"[ \t]+", " ", text)
        # Collapse excessive newlines (max 2 consecutive)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    @staticmethod
    def chunk_pages(
        pages: List[Dict[str, Any]],
        chunk_size: int = 700,
        chunk_overlap: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Splits page-aware text into chunks preserving page references.
        """
        all_chunks: List[Dict[str, Any]] = []
        chunk_index = 0

        for page in pages:
            page_num = page.get("page_number", 1)
            raw_text = page.get("text", "")
            cleaned = TextPreprocessor.clean_text(raw_text)

            if not cleaned:
                continue

            page_chunks = TextPreprocessor._chunk_single_text(
                cleaned,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                page_number=page_num,
                start_index=chunk_index
            )

            all_chunks.extend(page_chunks)
            chunk_index += len(page_chunks)

        # Fallback if text was split with 0 chunks
        if not all_chunks and pages:
            for page in pages:
                if page.get("text"):
                    all_chunks.append({
                        "chunk_index": 0,
                        "page_number": page.get("page_number", 1),
                        "text": page["text"][:chunk_size],
                        "token_count": len(page["text"][:chunk_size].split())
                    })
                    break

        return all_chunks

    @staticmethod
    def _chunk_single_text(
        text: str,
        chunk_size: int,
        chunk_overlap: int,
        page_number: int,
        start_index: int
    ) -> List[Dict[str, Any]]:
        if len(text) <= chunk_size:
            return [{
                "chunk_index": start_index,
                "page_number": page_number,
                "text": text,
                "token_count": len(text.split())
            }]

        chunks = []
        # Split into sentences or paragraphs
        sentences = re.split(r"(?<=[.?!])\s+", text)
        current_chunk_sentences = []
        current_len = 0
        idx = start_index

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            sent_len = len(sentence)
            if current_len + sent_len > chunk_size and current_chunk_sentences:
                chunk_text = " ".join(current_chunk_sentences)
                chunks.append({
                    "chunk_index": idx,
                    "page_number": page_number,
                    "text": chunk_text,
                    "token_count": len(chunk_text.split())
                })
                idx += 1

                # Retain overlap sentences
                overlap_sentences = []
                overlap_len = 0
                for s in reversed(current_chunk_sentences):
                    if overlap_len + len(s) <= chunk_overlap:
                        overlap_sentences.insert(0, s)
                        overlap_len += len(s)
                    else:
                        break

                current_chunk_sentences = overlap_sentences + [sentence]
                current_len = sum(len(s) for s in current_chunk_sentences) + len(current_chunk_sentences)
            else:
                current_chunk_sentences.append(sentence)
                current_len += sent_len + 1

        if current_chunk_sentences:
            chunk_text = " ".join(current_chunk_sentences)
            chunks.append({
                "chunk_index": idx,
                "page_number": page_number,
                "text": chunk_text,
                "token_count": len(chunk_text.split())
            })

        return chunks

