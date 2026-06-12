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
    build_yckt_section_payload,
    build_yckt_overview_payload,
    chunk_html_table,
    extract_muc,
    _section_depth,
)

# Bảng nhiều cột (mô phỏng bảng so sánh NSX): thông tin quan trọng nằm ở cột sau
MULTICOL_TABLE = (
    "<table>"
    "<tr><th>TT</th><th>Tên</th><th>Yêu cầu</th><th>Sở cứ NSX</th></tr>"
    "<tr><td>1.1.3</td><td>Áp suất</td><td>0,3 đến 0,95 MPa</td>"
    "<td>NSX dùng VHS3 trang 1</td></tr>"
    "</table>"
)


# Bảng YCKT có 1 mục 'Van xả áp' với 4 dòng thông số (mô phỏng cấu trúc thật)
SECTION_TABLE = (
    "<table>"
    "<tr><th>TT</th><th>Tên yêu cầu</th><th>Giá trị yêu cầu</th></tr>"
    "<tr><th></th><th>Tên</th><th>Giá trị</th></tr>"
    "<tr><td>1</td><td colspan='2'>Bộ công cụ dụng cụ</td></tr>"
    "<tr><td>1.1</td><td colspan='2'>Van xả áp</td></tr>"
    "<tr><td>1.1.1</td><td>Môi chất áp dụng</td><td>Khí nén</td></tr>"
    "<tr><td>1.1.2</td><td>Kích thước cổng kết nối</td><td>D=3/8</td></tr>"
    "<tr><td>1.1.3</td><td>Áp suất hoạt động</td><td>0,3 đến 0,95 MPa</td></tr>"
    "<tr><td>1.1.4</td><td>Nhiệt độ hoạt động</td><td>-4 đến 55 C</td></tr>"
    "</table>"
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


def test_section_grouping_one_chunk_per_section():
    """chunk_html_table(chunk_size lớn) gom cả mục 'Van xả áp' vào 1 chunk."""
    chunks = chunk_html_table(SECTION_TABLE, chunk_size=40, header_rows_count=2)
    van = [c for c in chunks if "Van xả áp" in extract_muc(c)]
    assert len(van) == 1, f"Kỳ vọng 1 chunk cho mục Van xả áp, được {len(van)}"
    print("[OK] test_section_grouping_one_chunk_per_section")


def test_section_hierarchy_path_preserved():
    """
    Đường dẫn phân cấp cha→con phải được giữ: chunk của 'Van xả áp' vẫn chứa tên
    mục CHA 'Bộ công cụ dụng cụ' → hỏi nhóm cha vẫn truy hồi được mục con.
    """
    chunks = chunk_html_table(SECTION_TABLE, chunk_size=40, header_rows_count=2)
    van_chunk = next(c for c in chunks if "Van xả áp" in extract_muc(c))
    muc = extract_muc(van_chunk)
    assert "Bộ công cụ dụng cụ" in muc, f"Mất tên mục cha trong path: {muc!r}"
    assert "Van xả áp" in muc
    assert ">" in muc  # có dạng đường dẫn cha > con
    print("[OK] test_section_hierarchy_path_preserved")


def test_build_yckt_section_payload_full_section():
    """Payload theo mục phải gom ĐỦ 4 dòng thông số của 'Van xả áp'."""
    chunks = chunk_html_table(SECTION_TABLE, chunk_size=40, header_rows_count=2)
    van_chunk = next(c for c in chunks if "Van xả áp" in extract_muc(c))

    payload = build_yckt_section_payload(van_chunk, "YCKT_2024.docx")
    assert payload is not None
    # section giờ là đường dẫn cha→con, chứa cả tên nhóm cha
    assert "Bộ công cụ dụng cụ" in payload["metadata"]["section"]
    assert "Van xả áp" in payload["metadata"]["section"]
    assert payload["metadata"]["row_count"] == 4, payload["metadata"]["row_count"]

    text = payload["text_for_llm"]
    # đủ cả 4 thông số trong cùng một node
    for p in ("Môi chất áp dụng", "Kích thước cổng kết nối",
              "Áp suất hoạt động", "Nhiệt độ hoạt động"):
        assert p in text, f"Thiếu '{p}' trong node mục"
    assert "0,3 đến 0,95 MPa" in text
    # embed_source nêu tên mục + tên/giá trị các dòng (để query 'Van xả áp' khớp)
    assert "Van xả áp" in payload["embed_source"]
    assert "Áp suất hoạt động" in payload["embed_source"]
    # param_name gộp danh sách các thông số con
    assert "Áp suất hoạt động" in payload["metadata"]["param_name"]
    print("[OK] test_build_yckt_section_payload_full_section")


def test_build_yckt_section_payload_empty():
    only_header = "<table><tr><th>TT</th></tr><tr><td>   </td></tr></table>"
    assert build_yckt_section_payload(only_header, "empty.docx") is None
    print("[OK] test_build_yckt_section_payload_empty")


def test_section_payload_embeds_all_columns_and_headers():
    """embed_source gồm MỌI cột (recall) + text_for_llm có nhãn cột."""
    payload = build_yckt_section_payload(MULTICOL_TABLE, "YCKT_2024.docx")
    assert payload is not None
    # Thông tin ở cột sau (sở cứ NSX) phải có trong embed_source → tìm được khi hỏi
    assert "VHS3" in payload["embed_source"], "embed_source bỏ sót cột sau"
    # text_for_llm có dòng nhãn cột để LLM hiểu ý nghĩa từng cột
    assert "Cột:" in payload["text_for_llm"]
    assert "Sở cứ NSX" in payload["text_for_llm"]
    assert "NSX dùng VHS3 trang 1" in payload["text_for_llm"]
    print("[OK] test_section_payload_embeds_all_columns_and_headers")


def test_build_yckt_overview_payload():
    payload = build_yckt_overview_payload(
        "YCKT_2024.docx", ["1.1 Van xả áp", "1.2 Cờ lê SMA", "1.1 Van xả áp"]
    )
    assert payload is not None
    assert payload["metadata"]["section"] == "(Tổng quan tài liệu)"
    # liệt kê đủ thiết bị, khử trùng
    assert "Van xả áp" in payload["text_for_llm"]
    assert "Cờ lê SMA" in payload["text_for_llm"]
    assert payload["text_for_llm"].count("Van xả áp") == 1  # đã khử trùng
    assert "YCKT_2024.docx" in payload["text_for_llm"]
    print("[OK] test_build_yckt_overview_payload")


def test_build_yckt_overview_payload_empty():
    assert build_yckt_overview_payload("d.docx", []) is None
    assert build_yckt_overview_payload("d.docx", ["", "  "]) is None
    print("[OK] test_build_yckt_overview_payload_empty")


def test_section_depth():
    assert _section_depth("1 Bộ công cụ dụng cụ") == 1
    assert _section_depth("1.1 Van xả áp") == 2
    assert _section_depth("1.1.3 Áp suất") == 3
    assert _section_depth("Không có số") == 1  # mặc định cấp 1
    print("[OK] test_section_depth")


if __name__ == "__main__":
    test_row_chunk_to_fields()
    test_row_chunk_to_fields_no_data()
    test_build_yckt_row_payload()
    test_build_yckt_row_payload_empty()
    test_build_yckt_row_payload_no_section()
    test_section_grouping_one_chunk_per_section()
    test_section_hierarchy_path_preserved()
    test_build_yckt_section_payload_full_section()
    test_build_yckt_section_payload_empty()
    test_section_payload_embeds_all_columns_and_headers()
    test_build_yckt_overview_payload()
    test_build_yckt_overview_payload_empty()
    test_section_depth()
    print("\nTất cả test bước 1+ PASSED.")
