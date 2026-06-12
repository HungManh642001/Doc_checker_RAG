"""
Test cho việc lắp ráp lỗi sau khi thẩm định SONG SONG (giữ thứ tự xác định).

Chạy từ thư mục backend/:
    python -m rag.tests.test_assemble_errors

Test nhắm RAGAnalyzer._assemble_errors — phần THUẦN gom kết quả các chunk theo
thứ tự, không gọi LLM. RAGAnalyzer import được mà không cần llama_index vì các
module nặng chỉ import lazy bên trong phương thức.
"""

from app.rag_analyzer import RAGAnalyzer, clean_doc_name


# --- Đối tượng lỗi giả mô phỏng pydantic model LoiThamDinh/ChiTietLoi ---
class _FakeChiTiet:
    def __init__(self, error_type, reasoning):
        self.error_type = error_type
        self.reasoning = reasoning


class _FakeLoi:
    def __init__(self, original_text, types):
        self.original_text = original_text
        self.danh_sach_cac_loi = [_FakeChiTiet(t, f"lý do {t}") for t in types]
        self.suggestion = f"sửa {original_text}"
        self.reference_location = "Mục X"
        self.reference_quote = "trích dẫn"


class _FakeKetQua:
    def __init__(self, errors):
        self.danh_sach_loi = errors


def _chunk(section, rows_text="<tr><td>x</td></tr>"):
    return f"<!-- Mục: {section} -->\n<table>{rows_text}</table>"


def test_assemble_preserves_order_and_ids():
    analyzer = RAGAnalyzer()
    ordered = [
        (_chunk("1.1 Van xả áp"), _FakeKetQua([_FakeLoi("22m", ["Lỗi đơn vị"])])),
        (_chunk("1.2 Cờ lê"), _FakeKetQua([])),  # chunk hợp lệ, 0 lỗi
        (_chunk("1.3 Connector"),
         _FakeKetQua([_FakeLoi("0.3", ["Sai dấu"]), _FakeLoi("≥5", ["Ký hiệu"])])),
    ]
    errors = analyzer._assemble_errors(ordered)

    assert len(errors) == 3, len(errors)
    # id mang chunk_idx + err_idx, theo đúng thứ tự chunk
    assert errors[0]["id"] == "error_c0_0"
    assert errors[0]["section"] == "1.1 Van xả áp"
    assert errors[0]["original_text"] == "22m"
    # chunk 1 (0 lỗi) bị bỏ qua → chunk 2 giữ idx=2
    assert errors[1]["id"] == "error_c2_0"
    assert errors[1]["original_text"] == "0.3"
    assert errors[1]["section"] == "1.3 Connector"
    assert errors[2]["id"] == "error_c2_1"
    assert errors[2]["original_text"] == "≥5"
    print("[OK] test_assemble_preserves_order_and_ids")


def test_assemble_skips_failed_chunks():
    """Chunk lỗi (ket_qua=None) hoặc phần tử None bị bỏ qua, không làm hỏng phần còn lại."""
    analyzer = RAGAnalyzer()
    ordered = [
        (_chunk("A"), None),                                   # chunk lỗi
        None,                                                   # slot rỗng
        (_chunk("B"), _FakeKetQua([_FakeLoi("t", ["E"])])),    # hợp lệ
    ]
    errors = analyzer._assemble_errors(ordered)
    assert len(errors) == 1, errors
    assert errors[0]["id"] == "error_c2_0"
    assert errors[0]["section"] == "B"
    print("[OK] test_assemble_skips_failed_chunks")


def test_assemble_empty():
    analyzer = RAGAnalyzer()
    assert analyzer._assemble_errors([]) == []
    print("[OK] test_assemble_empty")


class _FakeCanhBao:
    def __init__(self, original_text, muc_do, reasoning, ref_loc, ref_quote):
        self.original_text = original_text
        self.muc_do = muc_do
        self.reasoning = reasoning
        self.reference_location = ref_loc
        self.reference_quote = ref_quote


class _FakeNoiDung:
    def __init__(self, items):
        self.danh_sach_canh_bao = items


def test_assemble_warnings():
    analyzer = RAGAnalyzer()
    ordered = [
        (_chunk("1.1 Van xả áp"), _FakeNoiDung([
            _FakeCanhBao("0,3 MPa", "Khác biệt lớn", "lệch dải so với trước",
                         "YCKT_2023.docx - Van xả áp", "0,1 đến 1,0 MPa"),
        ])),
        (_chunk("1.2 Cờ lê"), _FakeNoiDung([])),  # không cảnh báo
        (_chunk("X"), None),                       # chunk lỗi
    ]
    ws = analyzer._assemble_warnings(ordered)
    assert len(ws) == 1, ws
    w = ws[0]
    assert w["severity"] == "warning"
    assert w["id"] == "warn_c0_0"
    assert w["original_text"] == "0,3 MPa"
    assert "Đối chiếu nội dung" in w["danh_sach_cac_loi"][0]["error_type"]
    assert w["danh_sach_cac_loi"][0]["severity"] == "warning"
    assert w["reference_location"] == "YCKT_2023.docx - Van xả áp"
    assert w["suggestion"] == ""  # cảnh báo không tự sửa
    print("[OK] test_assemble_warnings")


def test_clean_doc_name():
    # Ưu tiên tên gốc (giữ dấu tiếng Việt)
    assert clean_doc_name(
        "/up/hist_0_M_u_YCKT.docx", "Mẫu YCKT đầu vào_1.docx"
    ) == "Mẫu YCKT đầu vào_1.docx"
    # Không có tên gốc → strip tiền tố upload
    assert clean_doc_name("/up/hist_0_M_u_YCKT.docx") == "M_u_YCKT.docx"
    assert clean_doc_name("/up/ref_12_NĐ86.docx") == "NĐ86.docx"
    # Không có tiền tố → giữ nguyên basename
    assert clean_doc_name("/up/bao_cao.docx") == "bao_cao.docx"
    print("[OK] test_clean_doc_name")


if __name__ == "__main__":
    test_assemble_preserves_order_and_ids()
    test_assemble_skips_failed_chunks()
    test_assemble_empty()
    test_assemble_warnings()
    test_clean_doc_name()
    print("\nTất cả test song song-hoá PASSED.")
