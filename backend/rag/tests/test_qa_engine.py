"""
Test cho engine hỏi-đáp chatbot (bước 2).

Chạy từ thư mục backend/:
    python -m rag.tests.test_qa_engine

Test nhắm phần logic THUẦN của qa_engine (format_context, build_citations,
build_messages, _safe_retrieve) — KHÔNG gọi LLM/Ollama. Dùng node giả mô phỏng
NodeWithScore (có .node.metadata / .node.get_content() / .score).
"""

from rag.chat import qa_engine


# ---------------------------------------------------------------------------
# Node giả: mô phỏng NodeWithScore của llama_index
# ---------------------------------------------------------------------------
class _FakeNode:
    def __init__(self, content, metadata):
        self._content = content
        self.metadata = metadata

    def get_content(self):
        return self._content


class _FakeNodeWithScore:
    def __init__(self, content, metadata, score):
        self.node = _FakeNode(content, metadata)
        self.score = score


def _make_node(doc, section, param, value, score=0.9):
    return _FakeNodeWithScore(
        content=f"[Tài liệu: {doc} | Mục: {section}]\n{param} | {value}",
        metadata={
            "doc_name": doc,
            "section": section,
            "param_name": param,
            "param_value": value,
        },
        score=score,
    )


def test_format_context_empty():
    out = qa_engine.format_context([], "NGUỒN A")
    assert "Không có dữ liệu liên quan" in out
    assert "[NGUỒN A]" in out
    print("[OK] test_format_context_empty")


def test_format_context_with_nodes():
    nodes = [_make_node("YCKT_2024.docx", "1.1 Van xả áp", "Áp suất", "0,3 MPa")]
    out = qa_engine.format_context(nodes, "NGUỒN A")
    assert "YCKT_2024.docx" in out
    assert "Áp suất" in out
    assert out.startswith("[NGUỒN A]")
    print("[OK] test_format_context_with_nodes")


def test_build_citations_dedup_and_fields():
    a = [
        _make_node("YCKT_2024.docx", "1.1 Van", "Áp suất", "0,3 MPa", 0.91),
        # trùng (cùng doc+section+param) → bị khử
        _make_node("YCKT_2024.docx", "1.1 Van", "Áp suất", "0,3 MPa", 0.80),
    ]
    b = [_make_node("Moi.docx", "1.1 Van", "Áp suất", "0,4 MPa", 0.88)]

    cites = qa_engine.build_citations(a, b)
    # 1 từ nguồn A (sau khử trùng) + 1 từ nguồn B
    assert len(cites) == 2, cites
    assert cites[0]["source"] == "YCKT trước đây"
    assert cites[0]["doc_name"] == "YCKT_2024.docx"
    assert cites[0]["param_value"] == "0,3 MPa"
    assert cites[0]["score"] == 0.91
    assert cites[1]["source"] == "Tài liệu đang xét"
    assert cites[1]["doc_name"] == "Moi.docx"
    print("[OK] test_build_citations_dedup_and_fields")


def test_build_citations_same_param_diff_source_kept():
    """Cùng thông số nhưng khác nguồn (A vs B) thì giữ cả hai."""
    a = [_make_node("YCKT_2024.docx", "1.1", "Áp suất", "0,3 MPa")]
    b = [_make_node("YCKT_2024.docx", "1.1", "Áp suất", "0,3 MPa")]
    cites = qa_engine.build_citations(a, b)
    assert len(cites) == 2, cites
    print("[OK] test_build_citations_same_param_diff_source_kept")


def test_build_messages_structure():
    msgs = qa_engine.build_messages(
        question="Áp suất đã dùng giá trị nào?",
        ctx_a="[NGUỒN A]\n1. ...",
        ctx_b="[NGUỒN B]\n1. ...",
        history=[
            {"role": "user", "content": "Xin chào"},
            {"role": "assistant", "content": "Chào bạn"},
            {"role": "user", "content": ""},  # rỗng → bỏ qua
        ],
        focus_param="Áp suất hoạt động",
    )
    # system + 2 history hợp lệ + 1 user cuối = 4
    assert len(msgs) == 4, [m.role for m in msgs]
    assert msgs[0].role.value == "system"
    # câu hỏi + context + focus nằm trong message cuối
    last = msgs[-1].content
    assert "CÂU HỎI: Áp suất đã dùng giá trị nào?" in last
    assert "[NGUỒN A]" in last and "[NGUỒN B]" in last
    assert "Áp suất hoạt động" in last  # focus_param xuất hiện trong message cuối
    print("[OK] test_build_messages_structure")


def test_build_messages_exclude_current():
    """include_current=False: NGUỒN B bị loại khỏi prompt, có ghi chú chỉ tra YCKT cũ."""
    msgs = qa_engine.build_messages(
        question="Cung cấp thông tin Van xả áp?",
        ctx_a="[NGUỒN A — YCKT trước đây]\n1. Van xả áp ...",
        ctx_b="[NGUỒN B — Tài liệu đang xét]\n1. KHÔNG ĐƯỢC LỘ ...",
        include_current=False,
    )
    last = msgs[-1].content
    assert "NGUỒN A" in last
    assert "KHÔNG ĐƯỢC LỘ" not in last          # nội dung NGUỒN B không lọt vào
    assert "KHÔNG dùng tài liệu đang thẩm định" in last
    print("[OK] test_build_messages_exclude_current")


def test_build_messages_include_current_default():
    """Mặc định include_current=True: cả NGUỒN A và B đều có trong prompt."""
    msgs = qa_engine.build_messages(
        question="x?",
        ctx_a="[NGUỒN A]\nA-data",
        ctx_b="[NGUỒN B]\nB-data",
    )
    last = msgs[-1].content
    assert "A-data" in last and "B-data" in last
    print("[OK] test_build_messages_include_current_default")


def test_safe_retrieve_none_and_error():
    # None retriever → []
    assert qa_engine._safe_retrieve(None, "q") == []

    class _Boom:
        def retrieve(self, q):
            raise RuntimeError("nổ")

    assert qa_engine._safe_retrieve(_Boom(), "q") == []

    class _Ok:
        def retrieve(self, q):
            return ["node"]

    assert qa_engine._safe_retrieve(_Ok(), "q") == ["node"]
    print("[OK] test_safe_retrieve_none_and_error")


if __name__ == "__main__":
    test_format_context_empty()
    test_format_context_with_nodes()
    test_build_citations_dedup_and_fields()
    test_build_citations_same_param_diff_source_kept()
    test_build_messages_structure()
    test_build_messages_exclude_current()
    test_build_messages_include_current_default()
    test_safe_retrieve_none_and_error()
    print("\nTất cả test bước 2 PASSED.")
