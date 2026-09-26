"""
Optional retrieval over your own course notes (PDFs) so SurveyGPT can quote your
syllabus and textbook instead of only the model's general knowledge.

Text-based PDFs only. Scanned/photographed pages need OCR first, which this
simple version does not do.
"""

import glob
import os

import numpy as np
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer

DOCS_DIR = os.environ.get("SURVEYGPT_DOCS_DIR", "docs")


class NotesIndex:
    """Loads every PDF in DOCS_DIR, splits it into chunks, and embeds them so the
    most relevant passages for a question can be found by cosine similarity."""

    def __init__(self, docs_dir: str = DOCS_DIR, chunk_size: int = 900, overlap: int = 150):
        self.docs_dir = docs_dir
        self.chunks = self._load_chunks(chunk_size, overlap)
        self.embedder = None
        self.chunk_emb = None
        if self.chunks:
            self.embedder = SentenceTransformer("all-MiniLM-L6-v2")  # small, free, CPU-friendly
            self.chunk_emb = self.embedder.encode(
                [c["text"] for c in self.chunks], normalize_embeddings=True
            )

    def _load_chunks(self, chunk_size: int, overlap: int) -> list:
        chunks = []
        os.makedirs(self.docs_dir, exist_ok=True)
        for path in glob.glob(os.path.join(self.docs_dir, "*.pdf")):
            reader = PdfReader(path)
            for page_no, page in enumerate(reader.pages, start=1):
                text = (page.extract_text() or "").strip()
                start = 0
                while start < len(text):
                    piece = text[start : start + chunk_size]
                    if len(piece.strip()) > 50:
                        chunks.append({"text": piece, "source": f"{os.path.basename(path)} p.{page_no}"})
                    start += chunk_size - overlap
        return chunks

    def retrieve(self, query: str, k: int = 4, min_score: float = 0.30):
        """Return (context_text, source_labels) for the k closest chunks to `query`."""
        if self.chunk_emb is None:
            return "", []
        q = self.embedder.encode([query], normalize_embeddings=True)[0]
        scores = self.chunk_emb @ q
        top = [i for i in np.argsort(-scores)[:k] if scores[i] >= min_score]
        context = "\n\n".join(f"[{self.chunks[i]['source']}]\n{self.chunks[i]['text']}" for i in top)
        sources = sorted({self.chunks[i]["source"] for i in top})
        return context, sources
