from pydantic import BaseModel, Field
from typing import List, Optional

from llama_index.core.postprocessor.types import BaseNodePostprocessor
from llama_index.core.schema import NodeWithScore
from llama_index.core import Settings
from rag.config import (
    LLM_PROVIDER,
    LITELLM_BASE_URL, LITELLM_API_KEY, LITELLM_MODEL, LITELLM_DISABLE_THINKING,
    LITELLM_CONTEXT_WINDOW, LITELLM_MAX_TOKENS,
    OLLAMA_MODEL, OLLAMA_URL,
    REQUEST_TIMEOUT, CONTEXT_WINDOW, NUM_CTX,
)


def _build_llm():
    """
    Tạo LLM theo LLM_PROVIDER.

    - litellm: OpenAILike trỏ vào LiteLLM proxy (qwen3-27b trên vLLM).
               LiteLLM proxy là OpenAI-compatible nên dùng OpenAILike là chuẩn nhất.
    - ollama:  Ollama local (dev offline / fallback).

    Cả hai đều đặt is_function_calling_model=False (litellm) / không dùng tool,
    để LlamaIndex sinh structured output bằng prompt JSON — an toàn cho vLLM.
    """
    if LLM_PROVIDER == "litellm":
        from llama_index.llms.openai_like import OpenAILike

        additional_kwargs = {"seed": 42}
        if LITELLM_DISABLE_THINKING:
            # qwen3 trên vLLM: tắt thinking qua chat_template_kwargs (truyền extra_body)
            additional_kwargs["extra_body"] = {
                "chat_template_kwargs": {"enable_thinking": False}
            }

        return OpenAILike(
            model=LITELLM_MODEL,
            api_base=LITELLM_BASE_URL,
            api_key=LITELLM_API_KEY,
            is_chat_model=True,
            is_function_calling_model=False,  # dùng prompt-based JSON
            temperature=0.0,
            timeout=REQUEST_TIMEOUT,
            context_window=LITELLM_CONTEXT_WINDOW,  # khớp --max-model-len của vLLM
            max_tokens=LITELLM_MAX_TOKENS,          # << context_window để chừa chỗ cho prompt
            additional_kwargs=additional_kwargs,
        )

    # fallback: Ollama local
    from llama_index.llms.ollama import Ollama

    return Ollama(
        model=OLLAMA_MODEL,
        base_url=OLLAMA_URL,
        temperature=0.0,
        request_timeout=REQUEST_TIMEOUT,
        context_window=CONTEXT_WINDOW,
        thinking=False,
        keep_alive=True,
        additional_kwargs={"num_ctx": NUM_CTX, "seed": 42},
    )


Settings.llm = _build_llm()
print(f"[RAG] LLM provider = {LLM_PROVIDER} "
      f"({LITELLM_MODEL if LLM_PROVIDER == 'litellm' else OLLAMA_MODEL})")

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


class CanhBaoNoiDung(BaseModel):
    """Một cảnh báo (WARNING, không phải lỗi) khi đối chiếu nội dung với YCKT cũ."""
    original_text: str = Field(..., description="Thông số/giá trị NGUYÊN VĂN trong tài liệu đang xét được đối chiếu.")
    muc_do: str = Field(..., description="Mức độ: 'Cần lưu ý' hoặc 'Khác biệt lớn'.")
    reasoning: str = Field(..., description="So sánh giá trị trong tài liệu đang xét vs giá trị thiết bị tương ứng trong YCKT trước đây; vì sao cần lưu ý (lệch dải, khác đáng kể, khác đơn vị...).")
    reference_location: str = Field(..., description="Tên tài liệu YCKT trước đây + mục/thiết bị chứa giá trị đối chiếu.")
    reference_quote: str = Field(..., description="Trích NGUYÊN VĂN giá trị tương ứng từ YCKT trước đây. TUYỆT ĐỐI KHÔNG BỊA.")


class KetQuaNoiDung(BaseModel):
    danh_sach_canh_bao: List[CanhBaoNoiDung] = Field(
        default_factory=list,
        description="Danh sách cảnh báo đối chiếu nội dung. Rỗng nếu phù hợp hoặc không có cơ sở đối chiếu trong sở cứ.",
    )
