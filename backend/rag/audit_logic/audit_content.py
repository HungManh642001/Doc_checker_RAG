"""
Thẩm định NỘI DUNG (warning): đối chiếu thông số thiết bị trong tài liệu đang xét
với cùng thiết bị (hoặc tương tự) trong các YCKT đã duyệt TRƯỚC ĐÂY.

Khác với thẩm định hình thức (audit_engine — lỗi thể thức/đơn vị theo sở cứ pháp
lý), pass này CHỈ sinh CẢNH BÁO (warning) khi giá trị khác biệt/lệch dải so với
tiền lệ; không chặn, mang tính tham khảo cho người thẩm định.

Tái dùng QueryTransformRetriever (HTML query → plain text) + RetrieverQueryEngine
như audit_engine, nhưng truy hồi trên KHO YCKT LỊCH SỬ và xuất KetQuaNoiDung.
"""

from llama_index.core import ChatPromptTemplate
from llama_index.core.llms import ChatMessage, MessageRole
from llama_index.core.query_engine import RetrieverQueryEngine

from rag.audit_logic.audit_engine import QueryTransformRetriever
from rag.audit_logic.audit_models import KetQuaNoiDung


_SYSTEM = (
    "Bạn là chuyên gia thẩm định tài liệu kỹ thuật (YCKT) tiếng Việt. Nhiệm vụ: "
    "ĐỐI CHIẾU thông số của thiết bị/vật liệu trong TÀI LIỆU ĐANG XÉT với cùng "
    "thiết bị (hoặc tương tự) trong các YCKT ĐÃ DUYỆT TRƯỚC ĐÂY (phần SỞ CỨ).\n"
    "\n"
    "Với mỗi thông số trong tài liệu đang xét:\n"
    "- Nếu SỞ CỨ (YCKT trước đây) CÓ thiết bị/thông số tương ứng và giá trị KHÁC "
    "BIỆT/LỆCH DẢI/khác đơn vị một cách đáng kể → tạo MỘT CẢNH BÁO, nêu rõ giá trị "
    "hiện tại so với giá trị trước đây và mức độ ('Cần lưu ý' hoặc 'Khác biệt lớn').\n"
    "- Nếu giá trị PHÙ HỢP/nhất quán, HOẶC KHÔNG có cơ sở đối chiếu trong sở cứ → "
    "KHÔNG tạo cảnh báo cho thông số đó.\n"
    "\n"
    "Đây là CẢNH BÁO tham khảo, KHÔNG phải lỗi. TUYỆT ĐỐI không bịa giá trị hay tên "
    "tài liệu không có trong sở cứ; reference_quote phải trích nguyên văn từ sở cứ.\n"
    "BẮT BUỘC: trả về JSON hợp lệ đúng cấu trúc, không thêm văn bản ngoài JSON. Nếu "
    "không có cảnh báo nào, trả về danh sách rỗng.\n"
)

_USER = (
    "SỞ CỨ — CÁC YCKT TRƯỚC ĐÂY (để đối chiếu):\n"
    "--------------------\n"
    "{context_str}\n"
    "--------------------\n"
    "TÀI LIỆU ĐANG XÉT (HTML):\n"
    "--------------------\n"
    "{query_str}\n"
    "--------------------\n"
)


def run_content_audit(
    history_retriever,
    noi_dung_tai_lieu_dau_vao: str,
    top_k: int = 12,
    retrieve_lock=None,
) -> KetQuaNoiDung:
    """
    Đối chiếu một chunk (thiết bị) của tài liệu đang xét với kho YCKT lịch sử.

    Args:
        history_retriever: retriever trên kho YCKT trước đây (BẮT BUỘC khác None).
        noi_dung_tai_lieu_dau_vao: HTML chunk thiết bị cần đối chiếu.
        top_k: số node sở cứ lấy ra (không dùng trực tiếp — retriever đã cấu hình).
        retrieve_lock: khóa tuần tự hoá truy hồi khi chạy đa luồng.

    Returns:
        KetQuaNoiDung (danh_sach_canh_bao có thể rỗng).
    """
    template = ChatPromptTemplate([
        ChatMessage(role=MessageRole.SYSTEM, content=_SYSTEM),
        ChatMessage(role=MessageRole.USER, content=_USER),
    ])

    wrapped = QueryTransformRetriever(history_retriever, retrieve_lock=retrieve_lock)
    query_engine = RetrieverQueryEngine.from_args(
        retriever=wrapped,
        output_cls=KetQuaNoiDung,
        text_qa_template=template,
        node_postprocessors=[],
    )
    return query_engine.query(noi_dung_tai_lieu_dau_vao)
