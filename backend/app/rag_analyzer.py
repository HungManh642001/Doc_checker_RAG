"""
RAG Analyzer - kết nối Flask API với hệ thống RAG.
Dựng Qdrant index in-memory từ sở cứ người dùng tải lên,
sau đó thẩm định tài liệu đầu vào theo từng chunk.
"""

import os
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Chỉ import các module NHẸ ở cấp cao nhất. Các module nặng phụ thuộc llama_index
# (vector_db, audit_engine, audit_models) được import LAZY bên trong phương thức,
# để chế độ MOCK_MODE chạy được kể cả khi không có llama_index / không kết nối được.
from rag.knowledge_base.rules import load_rules_from_files
from rag.document_processing.chunker import chunk_html_table, extract_muc
from rag.config import (
    MOCK_MODE, AUDIT_CONCURRENCY, AUDIT_CHUNK_MAX_ROWS, AUDIT_MAX_CHUNKS,
)

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

        # --- Corpus tra cứu cho chatbot hỏi-đáp (dựng theo DÒNG thông số) ---
        # Kho YCKT lịch sử (upload kèm session) — NGUỒN A khi trả lời.
        self._history_index = None
        self._history_client = None
        self._history_retriever = None
        # Tài liệu đang xét — NGUỒN B khi trả lời (dựng trong analyze_document).
        self._current_index = None
        self._current_client = None
        self._current_retriever = None
        self._main_doc_name: str = ""

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def initialize_rag_system(
        self,
        reference_docs: List[str],
        rule_docs: Optional[List[str]] = None,
        history_docs: Optional[List[str]] = None,
    ) -> bool:
        """
        Chuyển các file sở cứ thành HTML, embed và dựng Qdrant index in-memory.

        Args:
            reference_docs: đường dẫn tới các file DOCX/HTML sở cứ (xây dựng tri thức).
                            Nếu rỗng → dùng sở cứ mặc định đi kèm hệ thống.
            rule_docs: đường dẫn tới các file quy định (.md/.txt/.docx) người dùng upload.
                       Nếu None/rỗng → dùng quy định mặc định (quy_dinh_chung.md).
            history_docs: đường dẫn tới các YCKT đã duyệt trước đây (DOCX/HTML), dùng
                          làm kho tra cứu cho chatbot hỏi-đáp. Tùy chọn — nếu rỗng thì
                          chatbot chỉ đối chiếu trên tài liệu đang xét.

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
                build_index_in_memory, build_yckt_index_in_memory,
                build_hybrid_retriever,
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

            # --- Kho YCKT lịch sử (NGUỒN A cho chatbot) — chẻ theo DÒNG thông số ---
            self._build_history_index(history_docs, build_yckt_index_in_memory,
                                      build_hybrid_retriever)

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

        self._main_doc_name = os.path.basename(main_doc_path)

        try:
            print("[RAG] Đang chuyển tài liệu sang HTML...")
            html = docx_to_html(main_doc_path)

            print("[RAG] Đang chẻ nhỏ tài liệu...")
            # Gom theo MỤC bảng nhưng không vượt quá AUDIT_CHUNK_MAX_ROWS dòng/chunk
            # → ít lần gọi LLM hơn + có ngữ cảnh cùng mục (chính xác hơn chunk 1-dòng).
            chunks = chunk_html_table(
                html, chunk_size=AUDIT_CHUNK_MAX_ROWS, header_rows_count=2
            )

            # ----- MOCK MODE: giả lập bằng heuristic, xử lý TOÀN BỘ chunk -----
            if self._mock:
                from rag.audit_logic.mock_auditor import audit_document
                print(f"[RAG] *** MOCK MODE *** giả lập thẩm định {len(chunks)} chunks...")
                all_errors = audit_document(chunks, self._rules)
                print(f"[RAG] Hoàn tất (mock): {len(all_errors)} lỗi giả lập.")
                return all_errors

            # ----- Chế độ thật: gọi LLM theo từng chunk -----
            from rag.audit_logic.audit_engine import run_audit

            # Dựng index tài liệu đang xét (NGUỒN B cho chatbot) — chẻ theo dòng.
            # Không chặn pipeline thẩm định nếu dựng thất bại.
            self._build_current_index(html)

            limit = min(AUDIT_MAX_CHUNKS, len(chunks))
            audit_chunks = chunks[:limit]
            print(f"[RAG] {len(chunks)} chunks, xử lý {limit} chunks "
                  f"song song ({AUDIT_CONCURRENCY} luồng).")

            # Thẩm định song song: vLLM batch nhiều request → nhanh hơn nhiều so với
            # gọi tuần tự. Phần truy hồi được khoá tuần tự (Qdrant không thread-safe),
            # phần sinh LLM (chậm) chạy đồng thời.
            retrieve_lock = threading.Lock()

            def _audit_one(idx: int, chunk: str):
                ket_qua = run_audit(
                    self._index, chunk, self._rules, top_k=top_k,
                    retriever=self._retriever, retrieve_lock=retrieve_lock,
                )
                return ket_qua

            ordered: List = [None] * len(audit_chunks)
            max_workers = max(1, min(AUDIT_CONCURRENCY, len(audit_chunks)))
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_idx = {
                    executor.submit(_audit_one, idx, chunk): idx
                    for idx, chunk in enumerate(audit_chunks)
                }
                for future in as_completed(future_to_idx):
                    idx = future_to_idx[future]
                    try:
                        ket_qua = future.result()
                        ordered[idx] = (audit_chunks[idx], ket_qua)
                        n = len(ket_qua.danh_sach_loi)
                        print(f"[RAG]   chunk {idx + 1}/{limit} -> "
                              + (f"{n} lỗi" if n else "Hợp lệ"))
                    except Exception as e:  # noqa: BLE001
                        print(f"[RAG] Lỗi chunk {idx + 1}: {e}")
                        ordered[idx] = (audit_chunks[idx], None)

            all_errors = self._assemble_errors(ordered)
            print(f"[RAG] Hoàn tất: {len(all_errors)} lỗi.")
            return all_errors

        except Exception as e:
            print(f"[RAG] Lỗi phân tích: {e}")
            import traceback
            traceback.print_exc()
            return []

    def answer_question(
        self,
        question: str,
        history: Optional[List[Dict]] = None,
        focus_param: Optional[str] = None,
        top_k: int = 6,
    ) -> Dict:
        """
        Trả lời câu hỏi chatbot bằng RAG trên kho YCKT lịch sử (NGUỒN A) và
        tài liệu đang xét (NGUỒN B).

        Args:
            question: câu hỏi của người thẩm định.
            history: lịch sử hội thoại [{"role": "user"|"assistant", "content": str}].
            focus_param: thông số đang quan tâm (vd khi bấm 'Hỏi về thông số này').

        Returns:
            {"answer": str, "citations": [...]}
        """
        if not self.is_initialized:
            raise RuntimeError("RAG chưa được khởi tạo. Gọi initialize_rag_system trước.")

        if self._mock:
            return {
                "answer": (
                    "Chatbot hỏi-đáp cần chế độ LLM thật (hãy tắt MOCK_MODE và "
                    "kết nối LiteLLM/Ollama)."
                ),
                "citations": [],
            }

        from rag.chat.qa_engine import answer_question as _answer
        return _answer(
            question,
            history_retriever=self._history_retriever,
            current_retriever=self._current_retriever,
            history=history,
            focus_param=focus_param,
            top_k=top_k,
        )

    def cleanup(self) -> None:
        """Đóng Qdrant client và giải phóng tài nguyên."""
        for client in (self._client, self._history_client, self._current_client):
            if client:
                try:
                    client.close()
                except Exception:
                    pass
        self._index = self._client = self._retriever = None
        self._history_index = self._history_client = self._history_retriever = None
        self._current_index = self._current_client = self._current_retriever = None
        self.is_initialized = False

    # ------------------------------------------------------------------
    # Corpus tra cứu cho chatbot (dựng theo dòng thông số)
    # ------------------------------------------------------------------

    def _build_history_index(self, history_docs, build_yckt_index_in_memory,
                             build_hybrid_retriever) -> None:
        """Dựng index kho YCKT lịch sử (NGUỒN A). Lỗi không chặn pipeline chính."""
        if not history_docs:
            print("[RAG] Không có YCKT lịch sử — chatbot chỉ đối chiếu tài liệu hiện tại.")
            return

        html_docs: List[Tuple[str, str]] = []
        for path in history_docs:
            if not os.path.exists(path):
                print(f"[RAG] Bỏ qua YCKT lịch sử (không tồn tại): {path}")
                continue
            try:
                html_docs.append((docx_to_html(path), os.path.basename(path)))
            except Exception as e:  # noqa: BLE001
                print(f"[RAG] Không đọc được YCKT lịch sử '{path}': {e}")

        if not html_docs:
            return

        try:
            print(f"[RAG] Đang embed kho YCKT lịch sử từ {len(html_docs)} file...")
            self._history_index, self._history_client, nodes = build_yckt_index_in_memory(
                html_docs, collection_name="yckt_history"
            )
            self._history_retriever = build_hybrid_retriever(
                self._history_index, nodes, top_k=8
            )
            print(f"[RAG] Kho YCKT lịch sử sẵn sàng ({len(nodes)} mục thiết bị).")
        except Exception as e:  # noqa: BLE001
            print(f"[RAG] Không dựng được kho YCKT lịch sử: {e}")
            self._history_index = self._history_client = self._history_retriever = None

    def _build_current_index(self, main_html: str) -> None:
        """Dựng index tài liệu đang xét (NGUỒN B). Lỗi không chặn pipeline chính."""
        try:
            from rag.knowledge_base.vector_db import (
                build_yckt_index_in_memory, build_hybrid_retriever,
            )
            doc_name = self._main_doc_name or "Tài liệu đang xét"
            self._current_index, self._current_client, nodes = build_yckt_index_in_memory(
                [(main_html, doc_name)], collection_name="current_doc"
            )
            self._current_retriever = build_hybrid_retriever(
                self._current_index, nodes, top_k=8
            )
            print(f"[RAG] Index tài liệu hiện tại sẵn sàng ({len(nodes)} mục thiết bị).")
        except Exception as e:  # noqa: BLE001
            print(f"[RAG] Không dựng được index tài liệu hiện tại: {e}")
            self._current_index = self._current_client = self._current_retriever = None

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _assemble_errors(self, ordered: List) -> List[Dict]:
        """
        Gom kết quả các chunk (đã sắp theo thứ tự chunk) thành danh sách lỗi.

        Tách riêng khỏi vòng song song để giữ thứ tự xác định (id/section ổn định,
        frontend/highlight không phụ thuộc thứ tự hoàn thành của luồng) và để test
        được mà không cần gọi LLM.

        Args:
            ordered: list các phần tử (chunk_html, ket_qua | None) theo đúng thứ tự
                     chunk. Phần tử None hoặc ket_qua None bị bỏ qua (chunk lỗi).
        """
        all_errors: List[Dict] = []
        for idx, item in enumerate(ordered):
            if not item:
                continue
            chunk, ket_qua = item
            if ket_qua is None:
                continue
            section = extract_muc(chunk)
            for err_idx, error in enumerate(ket_qua.danh_sach_loi):
                entry = self._transform_error(error, idx, err_idx, section)
                if entry:
                    all_errors.append(entry)
        return all_errors

    def _transform_error(
        self, error, chunk_idx: int, err_idx: int = 0, section: str = ""
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
                "section": section,
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
