"""
RAG Analyzer - kết nối Flask API với hệ thống RAG.
Dựng Qdrant index in-memory từ sở cứ người dùng tải lên,
sau đó thẩm định tài liệu đầu vào theo từng chunk.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from rag.knowledge_base.vector_db import build_index_in_memory, build_hybrid_retriever
from rag.knowledge_base.rules import load_rules
from rag.document_processing.chunker import chunk_html_table
from rag.audit_logic.audit_engine import run_audit
from rag.audit_logic.audit_models import LoiThamDinh


# ---------------------------------------------------------------------------
# DOCX → HTML helpers
# ---------------------------------------------------------------------------

def _to_html_mammoth(docx_path: str) -> str:
    """Chuyển DOCX → HTML bằng mammoth (giữ nguyên cấu trúc bảng tốt hơn)."""
    import mammoth
    with open(docx_path, "rb") as f:
        return mammoth.convert_to_html(f).value


def _to_html_fallback(docx_path: str) -> str:
    """Fallback: chuyển DOCX → HTML bằng python-docx."""
    from docx import Document
    doc = Document(docx_path)
    parts = ["<html><body>"]
    ns = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"

    for el in doc.element.body:
        tag = el.tag.split("}")[-1] if "}" in el.tag else el.tag
        if tag == "p":
            text = "".join(t.text for t in el.findall(f".//{ns}t") if t.text)
            if text.strip():
                parts.append(f"<p>{text}</p>")
        elif tag == "tbl":
            parts.append("<table>")
            for row in el.findall(f".//{ns}tr"):
                parts.append("<tr>")
                for cell in row.findall(f".//{ns}tc"):
                    cell_text = "".join(
                        t.text for t in cell.findall(f".//{ns}t") if t.text
                    )
                    parts.append(f"<td>{cell_text}</td>")
                parts.append("</tr>")
            parts.append("</table>")

    parts.append("</body></html>")
    return "\n".join(parts)


def docx_to_html(path: str) -> str:
    """Chuyển DOCX/HTML → HTML string, ưu tiên mammoth."""
    if path.endswith(".html"):
        return Path(path).read_text(encoding="utf-8")
    try:
        return _to_html_mammoth(path)
    except ImportError:
        return _to_html_fallback(path)


# ---------------------------------------------------------------------------
# RAGAnalyzer
# ---------------------------------------------------------------------------

class RAGAnalyzer:
    """
    Một instance tương ứng với một session phân tích.
    Dựng index từ sở cứ upload, rồi chạy thẩm định.
    """

    def __init__(self) -> None:
        self._index = None
        self._client = None
        self._retriever = None   # pre-built hybrid retriever, tái dùng cho mọi chunk
        self._rules: str = ""
        self.is_initialized: bool = False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def initialize_rag_system(self, reference_docs: List[str]) -> bool:
        """
        Chuyển các file sở cứ thành HTML, embed và dựng Qdrant index in-memory.

        Args:
            reference_docs: đường dẫn tới các file DOCX hoặc HTML sở cứ

        Returns:
            True nếu thành công
        """
        try:
            self._rules = load_rules()
            print("[RAG] Đã nạp quy định chung.")

            html_docs: List[Tuple[str, str]] = []
            for ref_path in reference_docs:
                if not os.path.exists(ref_path):
                    print(f"[RAG] Bỏ qua (không tồn tại): {ref_path}")
                    continue
                doc_name = os.path.basename(ref_path)
                print(f"[RAG] Đang xử lý sở cứ: {doc_name}")
                html = docx_to_html(ref_path)
                html_docs.append((html, doc_name))

            if not html_docs:
                print("[RAG] Không có file sở cứ hợp lệ.")
                return False

            print(f"[RAG] Đang embed và dựng index từ {len(html_docs)} file sở cứ...")
            self._index, self._client, nodes = build_index_in_memory(html_docs)

            # Xây hybrid retriever một lần, tái dùng cho mọi chunk (BM25 đắt nếu tạo lại mỗi lần)
            self._retriever = build_hybrid_retriever(self._index, nodes, top_k=6)

            self.is_initialized = True
            print("[RAG] Dựng index hoàn tất.")
            return True

        except Exception as e:
            print(f"[RAG] Lỗi khởi tạo: {e}")
            import traceback
            traceback.print_exc()
            return False

    def analyze_document(self, main_doc_path: str, top_k: int = 6) -> List[Dict]:
        """
        Thẩm định tài liệu đầu vào, trả về danh sách lỗi.

        Args:
            main_doc_path: đường dẫn DOCX/HTML cần thẩm định
            top_k: số chunk sở cứ lấy ra cho mỗi lần tra cứu

        Returns:
            list of error dicts
        """
        if not self.is_initialized or self._index is None:
            raise RuntimeError("RAG chưa được khởi tạo. Gọi initialize_rag_system trước.")

        try:
            print("[RAG] Đang chuyển tài liệu sang HTML...")
            html = docx_to_html(main_doc_path)

            print("[RAG] Đang chẻ nhỏ tài liệu...")
            chunks = chunk_html_table(html, chunk_size=1, header_rows_count=2)
            limit = min(20, len(chunks))
            print(f"[RAG] {len(chunks)} chunks, xử lý {limit} chunks đầu.")

            all_errors: List[Dict] = []
            for idx, chunk in enumerate(chunks[:limit]):
                try:
                    print(f"[RAG] Thẩm định chunk {idx + 1}/{limit}...")
                    ket_qua = run_audit(
                        self._index, chunk, self._rules, top_k=top_k,
                        retriever=self._retriever,
                    )
                    for error in ket_qua.danh_sach_loi:
                        entry = self._transform_error(error, idx)
                        if entry:
                            all_errors.append(entry)
                    n = len(ket_qua.danh_sach_loi)
                    print(f"[RAG]   -> {n} lỗi" if n else "[RAG]   -> Hợp lệ")
                except Exception as e:
                    print(f"[RAG] Lỗi chunk {idx + 1}: {e}")

            print(f"[RAG] Hoàn tất: {len(all_errors)} lỗi.")
            return all_errors

        except Exception as e:
            print(f"[RAG] Lỗi phân tích: {e}")
            import traceback
            traceback.print_exc()
            return []

    def cleanup(self) -> None:
        """Đóng Qdrant client và giải phóng tài nguyên."""
        if self._client:
            try:
                self._client.close()
            except Exception:
                pass
        self._index = None
        self._client = None
        self._retriever = None
        self.is_initialized = False

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _transform_error(self, error: LoiThamDinh, chunk_idx: int) -> Optional[Dict]:
        try:
            details = [
                {
                    "error_type": d.error_type,
                    "reasoning": d.reasoning,
                    "severity": "error",
                }
                for d in error.danh_sach_cac_loi
            ]
            return {
                "id": f"error_c{chunk_idx}_{len(details)}",
                "original_text": error.original_text[:200],
                "elementId": f"chunk_{chunk_idx}",
                "elementType": "chunk",
                "danh_sach_cac_loi": details,
                "suggestion": error.suggestion,
                "reference_location": error.reference_location,
                "reference_quote": error.reference_quote,
                "severity": "error",
            }
        except Exception as e:
            print(f"[RAG] Lỗi transform: {e}")
            return None


# ---------------------------------------------------------------------------
# Factory — mỗi session tạo một instance độc lập
# ---------------------------------------------------------------------------

def make_analyzer() -> RAGAnalyzer:
    """Tạo một RAGAnalyzer mới cho một session phân tích."""
    return RAGAnalyzer()
