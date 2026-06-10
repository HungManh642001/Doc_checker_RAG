import re
from typing import List, Optional

from bs4 import BeautifulSoup

from llama_index.core import ChatPromptTemplate
from llama_index.core.llms import ChatMessage, MessageRole
from llama_index.core.retrievers import BaseRetriever
from llama_index.core.schema import QueryBundle, NodeWithScore
from llama_index.core.query_engine import RetrieverQueryEngine

from rag.audit_logic.audit_models import KetQuaThamDinh


# ---------------------------------------------------------------------------
# Query text extraction
# ---------------------------------------------------------------------------

def _html_to_query_text(html_chunk: str) -> str:
    """
    Trích xuất plain text từ HTML chunk để dùng làm query cho retriever.

    Lý do cần chuyển đổi:
    - Vector retriever embed PLAIN TEXT, không embed HTML tags
    - BM25 tokenizer cần text sạch
    - Bỏ cột boilerplate (Tiêu chí đánh giá, PP đánh giá) để tập trung vào
      TT + Tên yêu cầu + Giá trị yêu cầu — 3 cột quan trọng nhất cho retrieval

    Input ví dụ:
        <!-- Mục: 1.1 Van xả áp -->
        <table><tr><th>TT</th>...</tr><tr><td>1.1.3</td><td>Áp suất</td><td>0,3 – 0,95 Mpa</td>...</tr></table>

    Output ví dụ:
        Mục: 1.1 Van xả áp
        1.1.3 | Áp suất hoạt động | Bao dải 0,3 – 0,95 Mpa (3 – 9,5 bar)
    """
    parts: List[str] = []

    # Section context từ comment <!-- Mục: ... -->
    m = re.search(r'<!-- Mục:\s*(.+?)\s*-->', html_chunk)
    if m:
        parts.append(f"Mục: {m.group(1)}")

    soup = BeautifulSoup(html_chunk, 'html.parser')

    # Lấy dòng dữ liệu (không có <th>) — chỉ lấy 3 cột đầu
    for row in soup.find_all('tr'):
        if row.find('th'):
            continue  # bỏ header rows
        cells = row.find_all('td', recursive=False)
        cell_texts = [
            c.get_text(separator=' ', strip=True)
            for c in cells[:3]
            if c.get_text(strip=True)
        ]
        if cell_texts:
            parts.append(' | '.join(cell_texts))

    return '\n'.join(parts) if parts else soup.get_text(separator=' ', strip=True)


# ---------------------------------------------------------------------------
# QueryTransformRetriever
# ---------------------------------------------------------------------------

class QueryTransformRetriever(BaseRetriever):
    """
    Wrapper chuyển HTML query → plain text TRƯỚC KHI truyền vào inner retriever.

    Tách biệt hai mục đích:
    - Retrieval: dùng plain text (tốt cho embedding và BM25)
    - LLM context: dùng HTML gốc (giữ nguyên cấu trúc bảng cho LLM)

    RetrieverQueryEngine gọi retriever.retrieve(query) để lấy nodes,
    rồi dùng query gốc (HTML) để điền {query_str} trong prompt template.
    Wrapper này can thiệp ở bước retrieve mà không ảnh hưởng bước sinh LLM.
    """

    def __init__(self, inner: BaseRetriever) -> None:
        self._inner = inner
        super().__init__()

    def _retrieve(self, query_bundle: QueryBundle) -> List[NodeWithScore]:
        clean_text = _html_to_query_text(query_bundle.query_str)
        return self._inner.retrieve(clean_text)


# ---------------------------------------------------------------------------
# run_audit
# ---------------------------------------------------------------------------

def run_audit(
    index,
    noi_dung_tai_lieu_dau_vao: str,
    rules: str,
    top_k: int,
    retriever: Optional[BaseRetriever] = None,
) -> KetQuaThamDinh:
    """
    Thẩm định một chunk HTML và trả về kết quả có cấu trúc KetQuaThamDinh.

    Luồng xử lý:
    1. QueryTransformRetriever chuyển HTML chunk → plain text query
    2. inner retriever (hybrid BM25+vector hoặc vector-only) tìm nodes sở cứ
    3. RetrieverQueryEngine điền nodes vào {context_str}, chunk HTML vào {query_str}
    4. LLM sinh JSON → parse thành KetQuaThamDinh

    Args:
        index: VectorStoreIndex — dùng làm fallback khi retriever=None
        noi_dung_tai_lieu_dau_vao: HTML chunk cần thẩm định (giữ cấu trúc bảng)
        rules: quy định chung (inject vào system prompt)
        top_k: số node sở cứ lấy ra
        retriever: pre-built hybrid retriever (tốt nhất là xây một lần, tái dùng).
                   Nếu None, fallback sang vector-only từ index.
    """
    system_content = (
        "Bạn là một chuyên gia thẩm định tài liệu kỹ thuật Tiếng Việt nghiêm ngặt.\n"
        "Dưới đây là các quy định chung bắt buộc tuân thủ (GLOBAL RULES): \n"
        f"{rules}\n"
        "NHIỆM VỤ: Tìm ra tất cả các thông số sai lệch (sai đơn vị đo, vi phạm trình bày "
        "đơn vị đo, vi phạm giới hạn, hoặc lỗi thể thức). Với mỗi thông số phải tìm ra tất "
        "cả các lỗi gặp phải (các lỗi không trùng nhau).\n"
        "Nếu phát hiện lỗi phải viện dẫn đúng sở cứ.\n"
        "BẮT BUỘC: Câu trả lời là định dạng JSON hợp lệ, tuân thủ theo đúng cấu trúc được "
        "yêu cầu. Không được thêm bất kỳ văn bản nào bên ngoài chuỗi JSON.\n"
    )

    user_content = (
        "SỞ CỨ QUY ĐỊNH LÀM CĂN CỨ:\n"
        "--------------------\n"
        "{context_str}\n"
        "--------------------\n"
        "TÀI LIỆU CẦN THẨM ĐỊNH (HTML):\n"
        "--------------------\n"
        "{query_str}\n"
        "--------------------\n"
    )

    chat_qa_template = ChatPromptTemplate([
        ChatMessage(role=MessageRole.SYSTEM, content=system_content),
        ChatMessage(role=MessageRole.USER, content=user_content),
    ])

    # Chọn inner retriever
    base_retriever = retriever if retriever is not None else index.as_retriever(
        similarity_top_k=top_k
    )

    # Wrap: HTML query → plain text trước khi retrieve
    wrapped = QueryTransformRetriever(base_retriever)

    query_engine = RetrieverQueryEngine.from_args(
        retriever=wrapped,
        output_cls=KetQuaThamDinh,
        text_qa_template=chat_qa_template,
        node_postprocessors=[],   # bỏ DeduplicateHTMLPostprocessor: có thể drop context hợp lệ
    )

    print("Đang tiến hành đối chiếu và thẩm định bằng Qwen (Vui lòng đợi)...")
    response = query_engine.query(noi_dung_tai_lieu_dau_vao)
    return response
