from llama_index.core import ChatPromptTemplate, PromptTemplate
from llama_index.core.llms import ChatMessage, MessageRole

from audit_logic.audit_models import KetQuaThamDinh, DeduplicateHTMLPostprocessor

def run_audit(index, noi_dung_tai_lieu_dau_vao: str, rules: str, top_k: int):
    qa_prompt_tmpl_str = (
        "Bạn là một chuyên gia thẩm định tài liệu kỹ thuật tiếng Việt nghiêm ngặt.\n"
        "Dưới đây là các quy định sở cứ (Context information): \n"
        "--------------------\n"
        "{context_str}\n"
        "--------------------\n"
        "Dựa chỉ vào các quy trình, hãy thẩm định tài liệu đầu vào sau đây.\n"
        "Tài liệu đầu vào (HTML):\n"
        "{query_str}\n\n"
        "Nhiệm vụ: Tìm ra TẤT CẢ các thông số sai lệch, sai đơn vị đo, vi phạm trình bày đơn vị đo, vi phạm giới hạn, hoặc lỗi thể thức (ví dụ dùng sai ký hiệu toán học). Với mỗi thông số phải tìm ra tất cả các lỗi mà nó gặp phải."
        "Nếu phát hiện lỗi, phải viện dẫn đúng sở cứ.\n"
        "BẮT BUỘC: Câu trả lời của bạn phải là định dạng JSON hợp lệ, tuân thủ đúng cấu trúc được yêu cầu. Không được thêm bất kỳ văn bản nào bên ngoài chuỗi JSON.\n"
    )

    system_content = (
        "Bạn là một chuyên gia thẩm định tài liệu kỹ thuật Tiếng Việt nghiêm ngặt.\n"
        "Dưới đây là các quy định chung bắt buộc tuân thủ (GLOBAL RULES): \n"
        f"{rules}\n"
        "NHIỆM VỤ: Tìm ra tất cả các thông số sai lệch (sai đơn vị đo, vi phạm trình bày đơn vị đo, vi phạm giới hạn, hoặc lỗi thể thức). Với mỗi thông số phải tìm ra tất cả các lỗi gặp phải (các lỗi không trùng nhau).\n"
        "Nếu phải hiện lỗi phải viện dẫn đúng sở cứ. \n"
        "BẮT BUỘC: Cẩu trả lời là định dạng JSON hợp lệ, tuân thủ theo đúng cấu trúc được yêu cầu. Không được thêm bất kỳ văn bản nào bên ngoài chuỗi JSON.\n"
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

    chat_text_qa_msgs = [
        ChatMessage(role=MessageRole.SYSTEM, content=system_content),
        ChatMessage(role=MessageRole.USER, content=user_content)
    ]
    chat_qa_template = ChatPromptTemplate(message_templates=chat_text_qa_msgs)

    qa_prompt_tmpl = PromptTemplate(qa_prompt_tmpl_str)

    query_engine = index.as_query_engine(
        output_cls=KetQuaThamDinh,
        text_qa_template=chat_qa_template,
        similarity_top_k=top_k,
        node_postprocessors=[DeduplicateHTMLPostprocessor()]
    )

    print("Đang tiến hành đối chiếu và thẩm định bằng Qwen (Vui lòng đợi)...")
    response = query_engine.query(noi_dung_tai_lieu_dau_vao)

    return response