"""
Trình thẩm định GIẢ LẬP (mock) — dùng khi không kết nối được LLM/embedding.

Mục tiêu: tạo ra kết quả lỗi *thực tế và khớp đúng nội dung tài liệu* để người
dùng có thể thử toàn bộ UI và tính năng (highlight trên tài liệu, chấp nhận sửa
& tải file đã sửa, xuất Excel, preset...).

Không gọi LLM, không cần embedding, không phụ thuộc llama_index. Chỉ dùng
heuristic regex bám sát các quy tắc trong `data/rules/quy_dinh_chung.md`:

  1. Dấu thập phân phải dùng dấu phẩy (,) — không dùng dấu chấm (.)
  2. Giữa trị số và ký hiệu đơn vị đo phải có một dấu cách (22 m, không 22m)
  3. Không dùng ký hiệu toán học ≥, ≤, ± — thay bằng chữ
"""

import re
from typing import Dict, List

from bs4 import BeautifulSoup

from rag.document_processing.chunker import extract_muc

# Ký hiệu đơn vị đo thường gặp (đặt ký hiệu DÀI trước để regex ưu tiên khớp dài).
_UNITS = [
    "MPa", "Mpa", "kPa", "hPa", "Pa",
    "mm²", "cm²", "m²", "mm", "cm", "dm", "km", "µm", "nm",
    "kg", "mg", "µg", "kV", "mV", "kW", "MW", "kHz", "MHz", "GHz", "Hz",
    "mA", "ml", "ml", "kN", "°C", "°",
    "g", "t", "l", "s", "h", "A", "V", "W", "N", "m", "%",
]
# regex bộ phận đơn vị (đã escape)
_UNIT_ALT = "|".join(re.escape(u) for u in _UNITS)

# 1) Số thập phân dùng dấu CHẤM: "0.3", "1.5" — nhưng KHÔNG khớp số mục "1.1.3"
_RE_DOT_DECIMAL = re.compile(r"(?<![\d.])(\d+\.\d+)(?![\d.])")

# 2) Trị số DÍNH liền ký hiệu đơn vị (không có dấu cách): "22m", "0,3MPa", "0.3MPa"
_RE_NUM_UNIT = re.compile(
    r"(?<![\w.,])(\d+(?:[.,]\d+)?)(" + _UNIT_ALT + r")(?![A-Za-zÀ-ỹ])"
)

# 3) Ký hiệu toán học
_MATH_REPLACE = {
    "≥": "không nhỏ hơn",
    "≤": "không lớn hơn",
    "±": "giá trị tuyệt đối",
}
_RE_MATH = re.compile(r"[≥≤±]")

_MAX_PER_CHUNK = 8


def _chunk_texts(html_chunk: str) -> List[str]:
    """
    Lấy các đoạn text 'có nghĩa' từ chunk HTML để dò lỗi.
    Ưu tiên text trong từng ô <td>/<th>; nếu không có bảng, lấy toàn bộ text.
    """
    soup = BeautifulSoup(html_chunk, "html.parser")
    cells = soup.find_all(["td", "th"])
    if cells:
        texts = [c.get_text(separator=" ", strip=True) for c in cells]
    else:
        texts = [soup.get_text(separator=" ", strip=True)]
    # bỏ rỗng, gộp trùng nhưng giữ thứ tự
    seen = set()
    out = []
    for t in texts:
        if t and t not in seen:
            seen.add(t)
            out.append(t)
    return out


def _make_error(
    chunk_idx: int,
    err_idx: int,
    original_text: str,
    error_type: str,
    reasoning: str,
    suggestion: str,
    reference_quote: str,
    section: str = "",
) -> Dict:
    """Dựng error dict đúng định dạng frontend mong đợi (giống _transform_error)."""
    return {
        "id": f"error_c{chunk_idx}_{err_idx}",
        "original_text": original_text,
        "section": section,
        "elementId": f"chunk_{chunk_idx}",
        "elementType": "chunk",
        "danh_sach_cac_loi": [
            {"error_type": error_type, "reasoning": reasoning, "severity": "error"}
        ],
        "suggestion": suggestion,
        "reference_location": "Quy định chung — Thể thức trình bày",
        "reference_quote": reference_quote,
        "severity": "error",
    }


def audit_chunk(html_chunk: str, rules: str, chunk_idx: int) -> List[Dict]:
    """
    Dò lỗi giả lập trên một chunk HTML, trả về danh sách error dict.

    Mỗi original_text là chuỗi xuất hiện NGUYÊN VĂN trong tài liệu nên highlight
    và phép thay thế (tải file đã sửa) đều hoạt động chính xác.
    """
    errors: List[Dict] = []
    seen = set()  # (original_text, error_type) — tránh trùng trong cùng chunk
    section = extract_muc(html_chunk)  # đề mục/vị trí trong tài liệu

    def add(original, etype, reasoning, suggestion, quote):
        key = (original, etype)
        if key in seen:
            return
        seen.add(key)
        errors.append(
            _make_error(chunk_idx, len(errors), original, etype, reasoning,
                        suggestion, quote, section)
        )

    for text in _chunk_texts(html_chunk):
        if len(errors) >= _MAX_PER_CHUNK:
            break

        # 2) Trị số dính đơn vị (xử lý trước để gộp cả lỗi dấu thập phân nếu có)
        for m in _RE_NUM_UNIT.finditer(text):
            number, unit = m.group(1), m.group(2)
            fixed_number = number.replace(".", ",")
            add(
                m.group(0),
                "Lỗi trình bày đơn vị đo",
                f"Giữa trị số '{number}' và ký hiệu đơn vị '{unit}' phải có một dấu "
                f"cách (ví dụ: 22 m, không viết 22m).",
                f"{fixed_number} {unit}",
                "Khi thể hiện giá trị đại lượng đo, ký hiệu đơn vị đo phải đặt sau "
                "trị số và cách nhau một dấu cách (Ví dụ: 22 m).",
            )
            if len(errors) >= _MAX_PER_CHUNK:
                break

        # 1) Số thập phân dùng dấu chấm
        for m in _RE_DOT_DECIMAL.finditer(text):
            if len(errors) >= _MAX_PER_CHUNK:
                break
            token = m.group(1)
            add(
                token,
                "Sai dấu thập phân",
                f"Số thập phân '{token}' đang dùng dấu chấm. Quy định bắt buộc dùng "
                f"dấu phẩy cho phần thập phân.",
                token.replace(".", ","),
                "Bắt buộc dùng dấu phẩy (,) cho số thập phân, tuyệt đối không dùng "
                "dấu chấm (.).",
            )

        # 3) Ký hiệu toán học
        for m in _RE_MATH.finditer(text):
            if len(errors) >= _MAX_PER_CHUNK:
                break
            sym = m.group(0)
            add(
                sym,
                "Lỗi ký hiệu toán học",
                f"Không được dùng ký hiệu toán học '{sym}'. Phải diễn đạt bằng chữ.",
                _MATH_REPLACE.get(sym, sym),
                "Không sử dụng các ký hiệu toán học (≥, ≤, ±). Thay ≥ thành 'không "
                "nhỏ hơn', ≤ thành 'không lớn hơn'.",
            )

    return errors


def audit_document(html_chunks: List[str], rules: str) -> List[Dict]:
    """Dò lỗi giả lập trên toàn bộ chunk của tài liệu."""
    all_errors: List[Dict] = []
    for idx, chunk in enumerate(html_chunks):
        all_errors.extend(audit_chunk(chunk, rules, idx))
    # Re-index id để duy nhất toàn tài liệu
    for i, e in enumerate(all_errors):
        e["id"] = f"error_{i}"
    return all_errors
