"""Pinecone-backed document chunk store using integrated embeddings."""

from __future__ import annotations

import hashlib
import os
import re
import time
from typing import Any


TEXT_FIELD = "chunk_text"
DEFAULT_INDEX_NAME = "pdf-intelligence"
DEFAULT_EMBED_MODEL = "llama-text-embed-v2"
DEFAULT_CLOUD = "aws"
DEFAULT_REGION = "us-east-1"
UPSERT_BATCH_SIZE = 96


def chunk_text(text: str, chunk_size: int = 400, overlap: int = 80) -> list[str]:
    """Split text into overlapping word chunks."""
    words = text.split()
    if not words:
        return []

    chunks, i = [], 0
    step = max(chunk_size - overlap, 1)
    while i < len(words):
        chunks.append(" ".join(words[i : i + chunk_size]))
        i += step
    return chunks


def namespace_for_document(pdf_name: str | None, pdf_text: str) -> str:
    """Build a stable Pinecone namespace for this uploaded document."""
    digest = hashlib.sha256(f"{pdf_name or ''}\n{pdf_text}".encode("utf-8", "ignore")).hexdigest()[:24]
    safe_name = re.sub(r"[^a-z0-9-]+", "-", (pdf_name or "document").lower()).strip("-")[:32]
    return f"{safe_name or 'document'}-{digest}"


def pinecone_configured() -> bool:
    return bool(os.getenv("PINECONE_API_KEY"))


def get_index_name() -> str:
    return os.getenv("PINECONE_INDEX_NAME", DEFAULT_INDEX_NAME)


def _pinecone_client():
    try:
        from pinecone import Pinecone
    except ImportError as exc:
        raise RuntimeError("pinecone package is not installed. Run: pip install pinecone") from exc

    api_key = os.getenv("PINECONE_API_KEY")
    if not api_key:
        raise RuntimeError("PINECONE_API_KEY missing from .env")
    return Pinecone(api_key=api_key)


def _ensure_index(pc: Any, index_name: str):
    if hasattr(pc, "has_index") and pc.has_index(index_name):
        return

    existing = {idx["name"] if isinstance(idx, dict) else getattr(idx, "name", None) for idx in pc.list_indexes()}
    if index_name in existing:
        return

    cloud = os.getenv("PINECONE_CLOUD", DEFAULT_CLOUD)
    region = os.getenv("PINECONE_REGION", DEFAULT_REGION)
    model = os.getenv("PINECONE_EMBED_MODEL", DEFAULT_EMBED_MODEL)

    pc.create_index_for_model(
        name=index_name,
        cloud=cloud,
        region=region,
        embed={
            "model": model,
            "field_map": {"text": TEXT_FIELD},
        },
    )

    deadline = time.time() + 90
    while time.time() < deadline:
        desc = pc.describe_index(index_name)
        status = desc.get("status", {}) if isinstance(desc, dict) else getattr(desc, "status", {})
        ready = status.get("ready") if isinstance(status, dict) else getattr(status, "ready", False)
        if ready:
            return
        time.sleep(2)


def _batched(items: list[dict], size: int):
    for i in range(0, len(items), size):
        yield items[i : i + size]


def index_document(pdf_text: str, pdf_name: str | None = None) -> dict:
    """Chunk and upsert source text to Pinecone; Pinecone creates embeddings."""
    chunks = chunk_text(pdf_text)
    if not chunks:
        raise ValueError("No text chunks available to index.")

    pc = _pinecone_client()
    index_name = get_index_name()
    _ensure_index(pc, index_name)
    index = pc.Index(index_name)
    namespace = namespace_for_document(pdf_name, pdf_text)

    records = [
        {
            "_id": f"{namespace}-{i}",
            TEXT_FIELD: chunk,
            "chunk": i + 1,
            "source": pdf_name or "uploaded-pdf",
        }
        for i, chunk in enumerate(chunks)
    ]

    for batch in _batched(records, UPSERT_BATCH_SIZE):
        index.upsert_records(namespace=namespace, records=batch)

    return {"index_name": index_name, "namespace": namespace, "chunks": len(chunks)}


def _hits_from_response(response: Any) -> list[Any]:
    if isinstance(response, dict):
        result = response.get("result", response)
        return result.get("hits", [])
    result = getattr(response, "result", None)
    if isinstance(result, dict):
        return result.get("hits", [])
    return getattr(result, "hits", []) or getattr(response, "hits", [])


def _field(hit: Any, name: str, default: Any = None) -> Any:
    if isinstance(hit, dict):
        fields = hit.get("fields") or {}
        return fields.get(name, hit.get(name, default))
    fields = getattr(hit, "fields", {}) or {}
    if isinstance(fields, dict):
        return fields.get(name, default)
    return getattr(fields, name, default)


class PineconeChunkIndex:
    """Search document chunks using Pinecone integrated text embeddings."""

    def __init__(self, pdf_text: str, pdf_name: str | None = None, namespace: str | None = None):
        self.pdf_text = pdf_text
        self.pdf_name = pdf_name
        self.namespace = namespace or namespace_for_document(pdf_name, pdf_text)
        self.pc = _pinecone_client()
        self.index_name = get_index_name()
        _ensure_index(self.pc, self.index_name)
        self.index = self.pc.Index(self.index_name)

    def search(self, query: str, top_k: int = 3) -> list[str]:
        top_k = max(1, min(int(top_k or 3), 10))
        response = self.index.search(
            namespace=self.namespace,
            top_k=top_k,
            inputs={"text": query},
            fields=[TEXT_FIELD, "chunk", "source"],
        )
        results = []
        for hit in _hits_from_response(response):
            text = _field(hit, TEXT_FIELD)
            chunk = _field(hit, "chunk")
            if text:
                label = f"Chunk {chunk}" if chunk else "Chunk"
                results.append(f"[{label}] {text}")
        return results
