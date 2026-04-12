from pydantic import BaseModel, Field
from typing import List, Optional

from llama_index.core.postprocessor.types import BaseNodePostprocessor
from llama_index.core.schema import NodeWithScore
from llama_index.llms.ollama import Ollama
from llama_index.core import Settings
from config import MODEL, OLLAMA_URL, REQUEST_TIMEOUT, CONTEXT_WINDOW, NUM_CTX


Settings.llm = Ollama(
    model=MODEL, 
    base_url=OLLAMA_URL,
    temperature=0.0,
    request_timeout=REQUEST_TIMEOUT,
    context_window=CONTEXT_WINDOW,
    thinking=False,
    keep_alive=True,
    additional_kwargs={
        "num_ctx": NUM_CTX,
        "seed": 42
    }
)

class DeduplicateHTMLPostprocessor(BaseNodePostprocessor):
    def _postprocess_nodes(self, nodes: List[NodeWithScore], query_bundle: Optional[any] = None) -> List[NodeWithScore]:
        unique_nodes = []
        seen_identifiers = set()

        for node in nodes:
            van_ban = node.metadata.get('van_ban', "")
            muc = node.metadata.get('muc', "")

            identifier = f"{van_ban}_{muc}"

            if identifier not in seen_identifiers:
                seen_identifiers.add(identifier)
                unique_nodes.append(node)
            else:
                pass
    
        return unique_nodes
    
class ChiTietLoi(BaseModel):
    error_type: str = Field(..., description="Tên lỗi (VD: Sai đơn vị, Lỗi trình bày đơn vị đo, Lỗi trình bày thông số, Thông số vượt mức, Lỗi thể thức, Lỗi logic, ...)")
    reasoning: str = Field(..., description="Giải thích từng bước 1: 1. Nội dung trong tài liệu là gì vs Nội dung trong sở cứ là gì? 2. Nội dung trong tài liệu có tuân thủ theo sở cứ không? Tại sao tính là lỗi?.")

class LoiThamDinh(BaseModel):
    original_text: str = Field(..., description="Đoạn text hoặc thông số bị lỗi trong tài liệu tải lên.")
    danh_sach_cac_loi: List[ChiTietLoi] = Field(..., description="Liệt kê TOÀN BỘ các lỗi mà thông số này mặc phải.")
    suggestion: str = Field(..., description="Đề xuất sửa chữa ngắn gọn bằng Tiếng Việt.")
    reference_location: str = Field(..., description="Vị trí chính xác trong sở cứ. Ghi 'Không rõ' nếu không có.")
    reference_quote: str = Field(..., description="copy và paste nguyên văn đoạn text từ Context information chứng minh cho lỗi này. TUYỆT ĐỐI KHÔNG TỰ BỊA.")

class KetQuaThamDinh(BaseModel):
    danh_sach_loi: List[LoiThamDinh] = Field(description="Danh sách các lỗi. Nếu không có lỗi, trả về [].")
