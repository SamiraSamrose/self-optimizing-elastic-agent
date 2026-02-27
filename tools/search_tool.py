import os
import json
import hashlib
import numpy as np
import faiss
import httpx
from pathlib import Path
from sentence_transformers import SentenceTransformer
from config.settings import (
    DOCS_VECTOR_INDEX,
    EMBEDDING_MODEL,
    DOCS_SOURCE_URL,
)

_FAISS_INDEX_PATH = f"{DOCS_VECTOR_INDEX}.faiss"
_METADATA_PATH = f"{DOCS_VECTOR_INDEX}.meta.json"
_EMBEDDING_DIM = 384  # all-MiniLM-L6-v2 output dimension


def _load_embedding_model() -> SentenceTransformer:
    return SentenceTransformer(EMBEDDING_MODEL)


def _embed(texts: list[str], model: SentenceTransformer) -> np.ndarray:
    embeddings = model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
    return embeddings.astype("float32")


def build_docs_index(doc_chunks: list[dict]) -> None:
    """
    Indexes a list of documentation chunks into a FAISS flat inner-product
    index for fast vector similarity search.

    Each chunk in doc_chunks must have:
        - 'text': str  — the raw documentation text
        - 'url': str   — the source URL
        - 'title': str — page or section title
    """
    model = _load_embedding_model()
    texts = [chunk["text"] for chunk in doc_chunks]
    embeddings = _embed(texts, model)

    index = faiss.IndexFlatIP(_EMBEDDING_DIM)
    index.add(embeddings)
    faiss.write_index(index, _FAISS_INDEX_PATH)

    metadata = [
        {"text": chunk["text"], "url": chunk["url"], "title": chunk["title"]}
        for chunk in doc_chunks
    ]
    with open(_METADATA_PATH, "w") as f:
        json.dump(metadata, f)


def _load_index_and_metadata():
    if not Path(_FAISS_INDEX_PATH).exists():
        raise FileNotFoundError(
            f"FAISS index not found at {_FAISS_INDEX_PATH}. "
            "Run the docs indexing pipeline first."
        )
    index = faiss.read_index(_FAISS_INDEX_PATH)
    with open(_METADATA_PATH, "r") as f:
        metadata = json.load(f)
    return index, metadata


def search_elastic_docs(query: str, top_k: int = 5) -> list[dict]:
    """
    Performs a vector similarity search against the indexed Elastic documentation.
    Returns the top-k most relevant chunks with their source URLs and text.

    Called by the agent when it encounters errors like CircuitBreakerException or
    needs guidance on wildcard query optimization, n-grams, breaker settings, etc.
    """
    index, metadata = _load_index_and_metadata()
    model = _load_embedding_model()

    query_vec = _embed([query], model)
    scores, indices = index.search(query_vec, top_k)

    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx == -1:
            continue
        chunk = metadata[idx]
        results.append({
            "score": float(score),
            "title": chunk["title"],
            "url": chunk["url"],
            "text": chunk["text"],
        })
    return results


def crawl_and_index_elastic_docs(
    sitemap_urls: list[str],
    chunk_size: int = 500,
    chunk_overlap: int = 50,
) -> int:
    """
    Crawls the Elastic documentation pages, splits them into overlapping
    chunks, and builds the FAISS vector index.

    Args:
        sitemap_urls: List of documentation page URLs to crawl.
        chunk_size: Number of characters per chunk.
        chunk_overlap: Overlap between consecutive chunks.

    Returns:
        Total number of chunks indexed.
    """
    chunks = []
    client = httpx.Client(timeout=30.0, follow_redirects=True)

    for url in sitemap_urls:
        try:
            response = client.get(url)
            response.raise_for_status()
            raw_text = _strip_html(response.text)
            page_chunks = _split_text(raw_text, chunk_size, chunk_overlap)
            for chunk_text in page_chunks:
                chunks.append({
                    "text": chunk_text,
                    "url": url,
                    "title": _extract_title(response.text),
                })
        except httpx.HTTPError:
            continue

    client.close()

    if chunks:
        build_docs_index(chunks)

    return len(chunks)


def _strip_html(html: str) -> str:
    """Removes HTML tags to get plain text from documentation pages"""
    import re
    text = re.sub(r"<style[^>]*>.*?</style>", "", html, flags=re.DOTALL)
    text = re.sub(r"<script[^>]*>.*?</script>", "", text, flags=re.DOTALL)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _extract_title(html: str) -> str:
    import re
    match = re.search(r"<title>(.*?)</title>", html, re.IGNORECASE)
    return match.group(1).strip() if match else "Elastic Documentation"


def _split_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    """Splits text into overlapping chunks for embedding"""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return [c for c in chunks if len(c.strip()) > 50]
