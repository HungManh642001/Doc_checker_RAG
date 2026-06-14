"""
RAG configuration — loaded from backend/.env with safe defaults.

LLM architecture:
- Audit-result LLM: LiteLLM proxy (qwen3-27b on vLLM) — default.
  Can be switched back to local Ollama via the LLM_PROVIDER variable in .env.
- Embeddings: ALWAYS run on local Ollama (nomic-embed-text), never via LiteLLM.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# backend/.env (config.py lives at backend/rag/config.py → go up 2 levels to backend/)
load_dotenv(Path(__file__).parent.parent / ".env")


def _get(name: str, default: str) -> str:
    return os.getenv(name, default)


# ---------------------------------------------------------------------------
# Provider switch
# ---------------------------------------------------------------------------
# "litellm" → use LiteLLM proxy (vLLM qwen3-27b)
# "ollama"  → use local Ollama (offline dev / fallback)
LLM_PROVIDER = _get("LLM_PROVIDER", "litellm").strip().lower()

# ---------------------------------------------------------------------------
# MOCK MODE — simulate audit results when the LLM/embedding cannot be reached.
# Enable it to try out the UI & all features (highlight, file editing, Excel, presets)
# without needing the LiteLLM proxy or Ollama. When enabled the system does NOT
# import/initialize llama_index — it only uses heuristic checks based on quy_dinh_chung.md.
# ---------------------------------------------------------------------------
MOCK_MODE = _get("MOCK_MODE", "false").strip().lower() == "true"

# ---------------------------------------------------------------------------
# LiteLLM proxy (OpenAI-compatible, qwen3-27b on vLLM)
# ---------------------------------------------------------------------------
# Note: api_base MUST have the /v1 suffix (the LiteLLM proxy's OpenAI route).
LITELLM_BASE_URL = _get("LITELLM_BASE_URL", "http://localhost:4000/v1")
LITELLM_API_KEY = _get("LITELLM_API_KEY", "sk-no-key")
LITELLM_MODEL = _get("LITELLM_MODEL", "qwen3-27b")
# Disable qwen3 "thinking" mode on vLLM (true/false)
LITELLM_DISABLE_THINKING = _get("LITELLM_DISABLE_THINKING", "true").strip().lower() == "true"
# The model's real context window on vLLM (qwen3-27b native = 32768).
# IMPORTANT: must match vLLM's --max-model-len, otherwise LlamaIndex miscomputes the
# prompt budget → "Calculated available context size ... not non-negative" error.
LITELLM_CONTEXT_WINDOW = int(_get("LITELLM_CONTEXT_WINDOW", "32768"))
# Max output tokens. Must be MUCH smaller than the context window (per-chunk audit output is short).
LITELLM_MAX_TOKENS = int(_get("LITELLM_MAX_TOKENS", "2048"))

# ---------------------------------------------------------------------------
# Ollama local (embeddings + LLM fallback)
# ---------------------------------------------------------------------------
OLLAMA_URL = _get("OLLAMA_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = _get("OLLAMA_MODEL", "qwen3:4b")

# Embeddings always run on local Ollama
EMBEDDING_MODEL = _get("EMBEDDING_MODEL", "nomic-embed-text")

# Backward-compat: legacy code imports MODEL (Ollama LLM)
MODEL = OLLAMA_MODEL

# HuggingFace embedding (optional, currently unused — kept for import compatibility)
EMBEDDING_MODEL_PATH = _get(
    "EMBEDDING_MODEL_PATH",
    r"E:\hf_model\huggingface\hub\models--nomic-ai--nomic-embed-text-v1.5\snapshots\e5cf08aadaa33385f5990def41f7a23405aec398",
)
EMBEDDING_CACHE_FOLDER = _get("EMBEDDING_CACHE_FOLDER", r"E:\hf_cache")

# ---------------------------------------------------------------------------
# Shared generation parameters + Ollama
# ---------------------------------------------------------------------------
REQUEST_TIMEOUT = float(_get("REQUEST_TIMEOUT", "600.0"))
CONTEXT_WINDOW = int(_get("CONTEXT_WINDOW", "8192"))   # context window for Ollama
NUM_CTX = int(_get("NUM_CTX", "10240"))                # num_ctx for Ollama

# ---------------------------------------------------------------------------
# AUDIT pipeline parameters
# ---------------------------------------------------------------------------
# Number of parallel LLM-call threads during auditing. vLLM on GPU batches many
# concurrent requests well → higher throughput. The retrieval part (Qdrant) is
# serialized internally with a lock.
AUDIT_CONCURRENCY = int(_get("AUDIT_CONCURRENCY", "6"))
# Max data rows per chunk during auditing. Chunks are grouped by table SECTION but
# never exceed this cap (long sections are split into multiple chunks).
AUDIT_CHUNK_MAX_ROWS = int(_get("AUDIT_CHUNK_MAX_ROWS", "8"))
# Cap on the number of audit chunks (prevents very long documents from hanging).
# Raised from the old hard limit of 20 thanks to parallelization + section grouping.
AUDIT_MAX_CHUNKS = int(_get("AUDIT_MAX_CHUNKS", "60"))

# Number of retrieved nodes for the CHATBOT (per source). Higher than audit because a
# question may need several pieces of information spread far apart (inside the table +
# outside it, across many sections).
CHAT_TOP_K = int(_get("CHAT_TOP_K", "12"))

# CONTENT audit (warning): cross-check the parameters of the document under review
# against previous YCKT documents. Only runs when a historical YCKT store exists. The
# result is only a warning, not an error.
CONTENT_AUDIT_ENABLED = _get("CONTENT_AUDIT_ENABLED", "true").strip().lower() == "true"
