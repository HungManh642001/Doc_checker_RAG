"""
Engine hỏi-đáp (chatbot) cho DocumentPreview.

Mục tiêu: trả lời câu hỏi của người thẩm định về việc một thông số kỹ thuật ĐÃ
từng xuất hiện trong các YCKT trước đây hay chưa, với giá trị bao nhiêu, có tham
khảo được để thẩm định tài liệu mới không.

Grounding trên 2 nguồn (RAG):
- NGUỒN A — kho YCKT lịch sử (history retriever).
- NGUỒN B — tài liệu đang xét (current retriever).

Trích dẫn (citations) được lấy TRỰC TIẾP từ metadata của các node truy hồi được,
KHÔNG để LLM tự sinh — tránh bịa nguồn.

Thiết kế tách lớp:
- Các helper định dạng (format_context, build_messages, build_citations) là THUẦN,
  thao tác trên đối tượng node-like → test được không cần Ollama/LLM.
- Chỉ answer_question() mới gọi tới Settings.llm (LLM thật).
"""

from typing import Dict, List, Optional

from llama_index.core.llms import ChatMessage, MessageRole


SYSTEM_PROMPT = (
    "Bạn là trợ lý thẩm định tài liệu Yêu Cầu Kỹ Thuật (YCKT) bằng tiếng Việt, hỗ "
    "trợ người thẩm định TRA CỨU và ĐỐI CHIẾU với các YCKT đã duyệt trước đây.\n"
    "\n"
    "KHÁI NIỆM QUAN TRỌNG:\n"
    "- Mỗi 'mục' trong bảng YCKT (vd '1.1 Van xả áp', '1.2 Cờ lê SMA') là MỘT "
    "THIẾT BỊ/VẬT LIỆU.\n"
    "- Các dòng con (1.1.1, 1.1.2, ...) là các THÔNG SỐ kỹ thuật của thiết bị đó "
    "(tên thông số + giá trị yêu cầu).\n"
    "- NGUỒN A = các YCKT TRƯỚC ĐÂY (kho tham chiếu để đối chiếu).\n"
    "- NGUỒN B = TÀI LIỆU ĐANG XÉT (tài liệu mới cần thẩm định).\n"
    "\n"
    "BẠN CÓ THỂ trả lời nhiều loại câu hỏi, ví dụ:\n"
    "- Thiết bị/vật liệu này trong các YCKT trước đây có những thông số gì, giá trị "
    "bao nhiêu?\n"
    "- Giá trị thông số của thiết bị trong tài liệu đang xét có PHÙ HỢP/NHẤT QUÁN "
    "với cùng thiết bị (hoặc thiết bị tương tự) ở các YCKT trước đây không? Chênh "
    "lệch ra sao?\n"
    "- Liệt kê / so sánh các thiết bị, thông số, dải giá trị đã từng dùng.\n"
    "- Các câu hỏi tra cứu, đối chiếu khác về YCKT trước đây.\n"
    "\n"
    "QUY TẮC BẮT BUỘC:\n"
    "1. CHỈ dựa vào dữ liệu trong NGUỒN A và NGUỒN B. TUYỆT ĐỐI không bịa thiết bị, "
    "thông số, giá trị hay tên tài liệu không có trong nguồn.\n"
    "2. Khi ĐỐI CHIẾU: nêu rõ giá trị trong NGUỒN B (tài liệu đang xét) so với giá "
    "trị tương ứng trong NGUỒN A (YCKT trước đây), rồi đưa nhận định phù hợp / khác "
    "biệt / cần lưu ý.\n"
    "3. Nếu NGUỒN A không có thiết bị/thông số liên quan, nói rõ: 'Chưa tìm thấy "
    "trong các YCKT trước đây.'\n"
    "4. Luôn viện dẫn TÊN TÀI LIỆU và MỤC (thiết bị) khi dẫn số liệu.\n"
    "5. Nếu NHIỀU tài liệu YCKT trước đây cùng chứa thiết bị/thông tin được hỏi, "
    "phải trình bày RIÊNG theo từng tài liệu (vd liệt kê theo từng tài liệu) và ghi "
    "rõ thông tin nào thuộc tài liệu nào — KHÔNG gộp chung làm một.\n"
    "6. Trả lời ngắn gọn, có cấu trúc, bằng tiếng Việt.\n"
)


# ---------------------------------------------------------------------------
# Node accessors — hỗ trợ cả NodeWithScore (llama_index) lẫn object giả khi test
# ---------------------------------------------------------------------------

def _get_node(nw):
    """Trả về TextNode bên trong NodeWithScore (hoặc chính nó nếu đã là node)."""
    return getattr(nw, "node", nw)


def _node_text(nw) -> str:
    node = _get_node(nw)
    if hasattr(node, "get_content"):
        try:
            return node.get_content() or ""
        except Exception:  # noqa: BLE001
            pass
    return getattr(node, "text", "") or ""


def _node_metadata(nw) -> Dict:
    return getattr(_get_node(nw), "metadata", {}) or {}


def _node_score(nw) -> Optional[float]:
    score = getattr(nw, "score", None)
    try:
        return float(score) if score is not None else None
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------------------
# Helpers thuần (test được)
# ---------------------------------------------------------------------------

def format_context(nodes: List, label: str) -> str:
    """Ghép nội dung các node truy hồi được thành một khối context có nhãn nguồn."""
    if not nodes:
        return f"[{label}]\n(Không có dữ liệu liên quan.)"
    parts = [f"[{label}]"]
    for i, nw in enumerate(nodes, 1):
        parts.append(f"{i}. {_node_text(nw)}")
    return "\n".join(parts)


def build_citations(nodes_a: List, nodes_b: List) -> List[Dict]:
    """
    Dựng danh sách trích dẫn từ metadata node (đã khử trùng theo doc+mục+thông số).

    Mỗi citation: {source, doc_name, section, param_name, param_value, score}.
    """
    citations: List[Dict] = []
    seen = set()
    for source, nodes in (
        ("YCKT trước đây", nodes_a or []),
        ("Tài liệu đang xét", nodes_b or []),
    ):
        for nw in nodes:
            md = _node_metadata(nw)
            key = (
                source,
                md.get("doc_name", ""),
                md.get("section", ""),
                md.get("param_name", ""),
            )
            if key in seen:
                continue
            seen.add(key)
            citations.append({
                "source": source,
                "doc_name": md.get("doc_name", ""),
                "section": md.get("section", ""),
                "param_name": md.get("param_name", ""),
                "param_value": md.get("param_value", ""),
                "score": _node_score(nw),
            })
    return citations


def build_messages(
    question: str,
    ctx_a: str,
    ctx_b: str,
    history: Optional[List[Dict]] = None,
    focus_param: Optional[str] = None,
) -> List[ChatMessage]:
    """
    Dựng danh sách ChatMessage: system + lịch sử hội thoại + câu hỏi kèm context.

    history: list of {"role": "user"|"assistant", "content": str}.
    focus_param: thông số người dùng đang quan tâm (vd bấm 'Hỏi về thông số này').
    """
    messages: List[ChatMessage] = [
        ChatMessage(role=MessageRole.SYSTEM, content=SYSTEM_PROMPT)
    ]

    for turn in history or []:
        role = (turn.get("role") or "").lower()
        content = turn.get("content") or ""
        if not content:
            continue
        messages.append(ChatMessage(
            role=MessageRole.USER if role == "user" else MessageRole.ASSISTANT,
            content=content,
        ))

    focus = (
        f"\nĐối tượng đang quan tâm (thiết bị/vật liệu hoặc thông số): {focus_param}"
        if focus_param else ""
    )
    user_content = (
        f"{ctx_a}\n\n"
        f"{ctx_b}\n\n"
        f"--------------------\n"
        f"CÂU HỎI: {question}{focus}"
    )
    messages.append(ChatMessage(role=MessageRole.USER, content=user_content))
    return messages


def _safe_retrieve(retriever, query: str) -> List:
    """Truy hồi an toàn — trả [] nếu retriever None hoặc lỗi (không chặn chat)."""
    if retriever is None:
        return []
    try:
        return retriever.retrieve(query)
    except Exception as e:  # noqa: BLE001
        print(f"[Chat] Lỗi retrieve: {e}")
        return []


# ---------------------------------------------------------------------------
# Hàm chính — gọi LLM thật
# ---------------------------------------------------------------------------

def answer_question(
    question: str,
    history_retriever=None,
    current_retriever=None,
    history: Optional[List[Dict]] = None,
    focus_param: Optional[str] = None,
    top_k: int = 6,
) -> Dict:
    """
    Trả lời một câu hỏi của người thẩm định bằng RAG trên 2 nguồn.

    Returns:
        {"answer": <chuỗi trả lời>, "citations": [<trích dẫn>...]}
    """
    query = f"{question} {focus_param}".strip() if focus_param else question

    nodes_a = _safe_retrieve(history_retriever, query)
    nodes_b = _safe_retrieve(current_retriever, query)

    ctx_a = format_context(nodes_a, "NGUỒN A — YCKT trước đây")
    ctx_b = format_context(nodes_b, "NGUỒN B — Tài liệu đang xét")
    messages = build_messages(question, ctx_a, ctx_b, history, focus_param)

    # Import lazy: side-effect cấu hình Settings.llm (theo LLM_PROVIDER).
    from llama_index.core import Settings
    import rag.audit_logic.audit_models  # noqa: F401  (đảm bảo Settings.llm sẵn sàng)

    response = Settings.llm.chat(messages)
    answer_text = (getattr(response.message, "content", "") or "").strip()

    return {
        "answer": answer_text,
        "citations": build_citations(nodes_a, nodes_b),
    }
