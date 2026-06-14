"""
Cấu hình RAG — đọc từ backend/.env, có giá trị mặc định an toàn.

Kiến trúc LLM:
- LLM sinh kết quả thẩm định: LiteLLM proxy (qwen3-27b trên vLLM) — mặc định.
  Có thể chuyển về Ollama local qua biến LLM_PROVIDER trong .env.
- Embeddings: LUÔN chạy trên Ollama local (nomic-embed-text), không qua LiteLLM.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# backend/.env (config.py ở backend/rag/config.py → lùi 2 cấp tới backend/)
load_dotenv(Path(__file__).parent.parent / ".env")


def _get(name: str, default: str) -> str:
    return os.getenv(name, default)


# ---------------------------------------------------------------------------
# Provider switch
# ---------------------------------------------------------------------------
# "litellm" → dùng LiteLLM proxy (vLLM qwen3-27b)
# "ollama"  → dùng Ollama local (dev offline / fallback)
LLM_PROVIDER = _get("LLM_PROVIDER", "litellm").strip().lower()

# ---------------------------------------------------------------------------
# MOCK MODE — giả lập kết quả thẩm định khi KHÔNG kết nối được LLM/embedding.
# Bật để dùng thử UI & toàn bộ tính năng (highlight, sửa file, Excel, preset)
# mà không cần LiteLLM proxy hay Ollama. Khi bật, hệ thống KHÔNG import/khởi tạo
# llama_index — chỉ dùng heuristic bắt lỗi theo quy_dinh_chung.md.
# ---------------------------------------------------------------------------
MOCK_MODE = _get("MOCK_MODE", "false").strip().lower() == "true"

# ---------------------------------------------------------------------------
# LiteLLM proxy (OpenAI-compatible, qwen3-27b trên vLLM)
# ---------------------------------------------------------------------------
# Lưu ý: api_base PHẢI có hậu tố /v1 (route OpenAI của LiteLLM proxy).
LITELLM_BASE_URL = _get("LITELLM_BASE_URL", "http://localhost:4000/v1")
LITELLM_API_KEY = _get("LITELLM_API_KEY", "sk-no-key")
LITELLM_MODEL = _get("LITELLM_MODEL", "qwen3-27b")
# Tắt chế độ "thinking" của qwen3 trên vLLM (true/false)
LITELLM_DISABLE_THINKING = _get("LITELLM_DISABLE_THINKING", "true").strip().lower() == "true"
# Context window thật của model trên vLLM (qwen3-27b native = 32768).
# QUAN TRỌNG: phải khớp --max-model-len của vLLM, nếu không LlamaIndex tính sai
# ngân sách prompt → lỗi "Calculated available context size ... not non-negative".
LITELLM_CONTEXT_WINDOW = int(_get("LITELLM_CONTEXT_WINDOW", "32768"))
# Max output tokens. Phải NHỎ hơn context window nhiều (output thẩm định mỗi chunk ngắn).
LITELLM_MAX_TOKENS = int(_get("LITELLM_MAX_TOKENS", "2048"))

# ---------------------------------------------------------------------------
# Ollama local (embeddings + LLM fallback)
# ---------------------------------------------------------------------------
OLLAMA_URL = _get("OLLAMA_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = _get("OLLAMA_MODEL", "qwen3:4b")

# Embeddings luôn trên Ollama local
EMBEDDING_MODEL = _get("EMBEDDING_MODEL", "nomic-embed-text")

# Backward-compat: code cũ import MODEL (LLM Ollama)
MODEL = OLLAMA_MODEL

# HuggingFace embedding (tuỳ chọn, hiện không dùng — giữ cho tương thích import)
EMBEDDING_MODEL_PATH = _get(
    "EMBEDDING_MODEL_PATH",
    r"E:\hf_model\huggingface\hub\models--nomic-ai--nomic-embed-text-v1.5\snapshots\e5cf08aadaa33385f5990def41f7a23405aec398",
)
EMBEDDING_CACHE_FOLDER = _get("EMBEDDING_CACHE_FOLDER", r"E:\hf_cache")

# ---------------------------------------------------------------------------
# Tham số sinh chung + Ollama
# ---------------------------------------------------------------------------
REQUEST_TIMEOUT = float(_get("REQUEST_TIMEOUT", "600.0"))
CONTEXT_WINDOW = int(_get("CONTEXT_WINDOW", "8192"))   # context window cho Ollama
NUM_CTX = int(_get("NUM_CTX", "10240"))                # num_ctx cho Ollama

# ---------------------------------------------------------------------------
# Tham số THẨM ĐỊNH (audit pipeline)
# ---------------------------------------------------------------------------
# Số luồng gọi LLM song song khi thẩm định. vLLM trên GPU batch tốt nhiều request
# đồng thời → tăng throughput. Phần truy hồi (Qdrant) được khóa tuần tự bên trong.
AUDIT_CONCURRENCY = int(_get("AUDIT_CONCURRENCY", "6"))
# Số dòng dữ liệu tối đa mỗi chunk khi thẩm định. Chunk gom theo MỤC bảng nhưng
# không vượt quá trần này (mục dài bị cắt thành nhiều chunk).
AUDIT_CHUNK_MAX_ROWS = int(_get("AUDIT_CHUNK_MAX_ROWS", "8"))
# Trần số chunk thẩm định (chống tài liệu quá dài làm treo). Tăng so với giới hạn
# cứng 20 cũ vì đã song song hóa + gom mục.
AUDIT_MAX_CHUNKS = int(_get("AUDIT_MAX_CHUNKS", "60"))

# Số node truy hồi cho CHATBOT (mỗi nguồn). Cao hơn audit vì câu hỏi có thể cần
# nhiều mẩu thông tin nằm xa nhau (trong bảng + ngoài bảng, nhiều mục).
CHAT_TOP_K = int(_get("CHAT_TOP_K", "12"))

# Thẩm định NỘI DUNG (warning): đối chiếu thông số tài liệu đang xét với YCKT trước
# đây. Chỉ chạy khi có kho YCKT lịch sử. Kết quả chỉ là cảnh báo, không phải lỗi.
CONTENT_AUDIT_ENABLED = _get("CONTENT_AUDIT_ENABLED", "true").strip().lower() == "true"
