"""
Test cho logic dựng corpus tra cứu YCKT theo DÒNG thông số (bước 1 của chatbot).

Chạy từ thư mục backend/:
    python -m rag.tests.test_yckt_index

Test nhắm vào phần logic THUẦN trong document_processing/chunker.py (chẻ dòng,
trích trường, định dạng text & metadata) — KHÔNG cần llama_index/Ollama, chỉ cần
beautifulsoup4. Phần nhúng vector (yckt_rows_to_nodes) chỉ là lớp mỏng bọc thêm
embedding nên không kiểm ở đây.
"""

from rag.document_processing.chunker import (
    row_chunk_to_fields,
    build_yckt_row_payload,
)


# ---------------------------------------------------------------------------
# Dữ liệu mẫu: một mini-table chunk như chunk_html_table sinh ra (1 dòng dữ liệu)
# ---------------------------------------------------------------------------
SAMPLE_CHUNK = (
    "<!-- Mục: 1.1 Van xả áp -->\n"
    "<table>"
    "<tr><th>TT</th><th>Tên yêu cầu</th><th>Giá trị yêu cầu</th><th>PP đánh giá</th></tr>"
    "<tr><td>1.1.3</td><td>Áp suất hoạt động</td>"
    "<td>0,3 đến 0,95 MPa</td><td>Thử nghiệm</td></tr>"
    "</table>"
)


def test_row_chunk_to_fields():
    fields = row_chunk_to_fields(SAMPLE_CHUNK)
    assert fields["section"] == "1.1 Van xả áp", fields["section"]
    assert fields["tt"] == "1.1.3", fields["tt"]
    assert fields["param_name"] == "Áp suất hoạt động", fields["param_name"]
    assert fields["param_value"] == "0,3 đến 0,95 MPa", fields["param_value"]
    # Header row (<th>) phải bị loại, chỉ còn 4 cell dữ liệu
    assert len(fields["cells"]) == 4, fields["cells"]
    print("[OK] test_row_chunk_to_fields")


def test_row_chunk_to_fields_no_data():
    """Chunk chỉ có header → không có cell dữ liệu."""
    only_header = "<table><tr><th>TT</th><th>Tên</th></tr></table>"
    fields = row_chunk_to_fields(only_header)
    assert fields["cells"] == [], fields["cells"]
    assert fields["param_name"] == ""
    print("[OK] test_row_chunk_to_fields_no_data")


def test_build_yckt_row_payload():
    payload = build_yckt_row_payload(SAMPLE_CHUNK, "YCKT_Bom_2024.docx")
    assert payload is not None

    meta = payload["metadata"]
    assert meta["doc_name"] == "YCKT_Bom_2024.docx"
    assert meta["section"] == "1.1 Van xả áp"
    assert meta["param_name"] == "Áp suất hoạt động"
    assert meta["param_value"] == "0,3 đến 0,95 MPa"

    # text cho LLM phải nêu rõ NGUỒN tài liệu + đề mục để trích dẫn được
    assert "YCKT_Bom_2024.docx" in payload["text_for_llm"]
    assert "1.1 Van xả áp" in payload["text_for_llm"]
    assert "Áp suất hoạt động" in payload["text_for_llm"]

    # embed_source tập trung Mục + Tên + Giá trị (không lẫn cột boilerplate "Thử nghiệm")
    assert "Thử nghiệm" not in payload["embed_source"]
    assert "Áp suất hoạt động" in payload["embed_source"]
    assert "0,3 đến 0,95 MPa" in payload["embed_source"]
    print("[OK] test_build_yckt_row_payload")


def test_build_yckt_row_payload_empty():
    """Dòng không có nội dung trích xuất được → trả None (không tạo node rác)."""
    only_header = "<table><tr><th>TT</th></tr><tr><td>   </td></tr></table>"
    assert build_yckt_row_payload(only_header, "empty.docx") is None
    print("[OK] test_build_yckt_row_payload_empty")


def test_build_yckt_row_payload_no_section():
    """Không có comment <!-- Mục --> thì text_for_llm vẫn hợp lệ, section rỗng."""
    chunk = (
        "<table>"
        "<tr><th>TT</th><th>Tên yêu cầu</th><th>Giá trị yêu cầu</th></tr>"
        "<tr><td>1</td><td>Lưu lượng</td><td>50 m3/h</td></tr>"
        "</table>"
    )
    payload = build_yckt_row_payload(chunk, "doc.docx")
    assert payload is not None
    assert payload["metadata"]["section"] == ""
    assert "Mục:" not in payload["text_for_llm"]
    assert "Lưu lượng" in payload["text_for_llm"]
    print("[OK] test_build_yckt_row_payload_no_section")


if __name__ == "__main__":
    test_row_chunk_to_fields()
    test_row_chunk_to_fields_no_data()
    test_build_yckt_row_payload()
    test_build_yckt_row_payload_empty()
    test_build_yckt_row_payload_no_section()
    print("\nTất cả test bước 1 PASSED.")
