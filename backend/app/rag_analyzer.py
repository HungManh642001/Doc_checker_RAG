"""
RAG Analyzer - kết nối Flask API với hệ thống RAG.
Dựng Qdrant index in-memory từ sở cứ người dùng tải lên,
sau đó thẩm định tài liệu đầu vào theo từng chunk.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Chỉ import các module NHẸ ở cấp cao nhất. Các module nặng phụ thuộc llama_index
# (vector_db, audit_engine, audit_models) được import LAZY bên trong phương thức,
# để chế độ MOCK_MODE chạy được kể cả khi không có llama_index / không kết nối được.
from rag.knowledge_base.rules import load_rules_from_files
from rag.document_processing.chunker import chunk_html_table
from rag.config import MOCK_MODE

# Sở cứ mặc định đi kèm hệ thống (NĐ 86/2012) — dùng khi người dùng không upload sở cứ.
_DEFAULT_REFERENCE_DIR = (
    Path(__file__).parent.parent / "rag" / "data" / "reference_documents"
)


def _default_reference_docs() -> List[str]:
    """Trả về danh sách sở cứ mặc định đi kèm hệ thống (nếu có)."""
    if not _DEFAULT_REFERENCE_DIR.exists():
        return []
    return [
        str(p)
        for p in _DEFAULT_REFERENCE_DIR.iterdir()
        if p.suffix.lower() in (".docx", ".doc", ".html")
    ]


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
        self._mock: bool = MOCK_MODE
        self.is_initialized: bool = False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def initialize_rag_system(
        self,
        reference_docs: List[str],
        rule_docs: Optional[List[str]] = None,
    ) -> bool:
        """
        Chuyển các file sở cứ thành HTML, embed và dựng Qdrant index in-memory.

        Args:
            reference_docs: đường dẫn tới các file DOCX/HTML sở cứ (xây dựng tri thức).
                            Nếu rỗng → dùng sở cứ mặc định đi kèm hệ thống.
            rule_docs: đường dẫn tới các file quy định (.md/.txt/.docx) người dùng upload.
                       Nếu None/rỗng → dùng quy định mặc định (quy_dinh_chung.md).

        Returns:
            True nếu thành công
        """
        try:
            # Quy định: ưu tiên file upload, fallback mặc định
            self._rules = load_rules_from_files(rule_docs)

            # ----- MOCK MODE: bỏ qua embedding & dựng index -----
            if self._mock:
                print("[RAG] *** MOCK MODE *** — giả lập thẩm định, KHÔNG gọi "
                      "LLM/embedding. Bỏ qua dựng index.")
                self.is_initialized = True
                return True

            # Lazy import các module nặng (chỉ khi chạy thật)
            from rag.knowledge_base.vector_db import (
                build_index_in_memory, build_hybrid_retriever,
            )

            # Sở cứ: fallback sang sở cứ mặc định nếu người dùng không upload
            if not reference_docs:
                reference_docs = _default_reference_docs()
                if reference_docs:
                    print(f"[RAG] Không có sở cứ upload — dùng {len(reference_docs)} "
                          f"sở cứ mặc định.")

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
        if not self.is_initialized:
            raise RuntimeError("RAG chưa được khởi tạo. Gọi initialize_rag_system trước.")
        if not self._mock and self._index is None:
            raise RuntimeError("Index chưa sẵn sàng.")

        try:
            print("[RAG] Đang chuyển tài liệu sang HTML...")
            html = docx_to_html(main_doc_path)

            print("[RAG] Đang chẻ nhỏ tài liệu...")
            chunks = chunk_html_table(html, chunk_size=1, header_rows_count=2)

            # ----- MOCK MODE: giả lập bằng heuristic, xử lý TOÀN BỘ chunk -----
            if self._mock:
                from rag.audit_logic.mock_auditor import audit_document
                print(f"[RAG] *** MOCK MODE *** giả lập thẩm định {len(chunks)} chunks...")
                all_errors = audit_document(chunks, self._rules)
                print(f"[RAG] Hoàn tất (mock): {len(all_errors)} lỗi giả lập.")
                return all_errors

            # ----- Chế độ thật: gọi LLM theo từng chunk -----
            from rag.audit_logic.audit_engine import run_audit

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
                    for err_idx, error in enumerate(ket_qua.danh_sach_loi):
                        entry = self._transform_error(error, idx, err_idx)
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

    def _transform_error(
        self, error, chunk_idx: int, err_idx: int = 0
    ) -> Optional[Dict]:
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
                "id": f"error_c{chunk_idx}_{err_idx}",
                # Giữ NGUYÊN VĂN original_text để apply_text_corrections khớp chính xác
                # khi thay thế trong DOCX (cắt ngắn sẽ làm hỏng phép thay thế).
                "original_text": error.original_text,
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
