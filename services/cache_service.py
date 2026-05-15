from typing import Dict, Any

# Simple in-memory cache
# Format: { "namespace": { "full_text": str, "pages_list": list[str], "metadata": dict } }
_document_cache: Dict[str, Dict[str, Any]] = {}

def get_document(namespace: str) -> Dict[str, Any]:
    return _document_cache.get(namespace)

def set_document(namespace: str, data: Dict[str, Any]):
    _document_cache[namespace] = data

def clear_cache():
    global _document_cache
    _document_cache = {}
