"""
MOCK auditor — used when the LLM/embedding service is unreachable.

Goal: produce *realistic error results that match the actual document content* so
the user can try out the whole UI and feature set (document highlighting, accepting
fixes & downloading the corrected file, Excel export, presets...).

Does not call an LLM, needs no embeddings, has no llama_index dependency. Uses only
regex heuristics that closely follow the rules in `data/rules/quy_dinh_chung.md`:

  1. Decimal separator must be a comma (,) — not a dot (.)
  2. There must be a space between the number and the unit symbol (22 m, not 22m)
  3. No math symbols ≥, ≤, ± — spell them out instead
"""

import re
from typing import Dict, List

from bs4 import BeautifulSoup

from rag.document_processing.chunker import extract_muc

# Common unit symbols (put LONGER symbols first so the regex prefers longer matches).
_UNITS = [
    "MPa", "Mpa", "kPa", "hPa", "Pa",
    "mm²", "cm²", "m²", "mm", "cm", "dm", "km", "µm", "nm",
    "kg", "mg", "µg", "kV", "mV", "kW", "MW", "kHz", "MHz", "GHz", "Hz",
    "mA", "ml", "ml", "kN", "°C", "°",
    "g", "t", "l", "s", "h", "A", "V", "W", "N", "m", "%",
]
# unit alternation regex fragment (escaped)
_UNIT_ALT = "|".join(re.escape(u) for u in _UNITS)

# 1) Decimal number using a DOT: "0.3", "1.5" — but does NOT match section number "1.1.3"
_RE_DOT_DECIMAL = re.compile(r"(?<![\d.])(\d+\.\d+)(?![\d.])")

# 2) Number STUCK to the unit symbol (no space): "22m", "0,3MPa", "0.3MPa"
_RE_NUM_UNIT = re.compile(
    r"(?<![\w.,])(\d+(?:[.,]\d+)?)(" + _UNIT_ALT + r")(?![A-Za-zÀ-ỹ])"
)

# 3) Math symbols
_MATH_REPLACE = {
    "≥": "không nhỏ hơn",
    "≤": "không lớn hơn",
    "±": "giá trị tuyệt đối",
}
_RE_MATH = re.compile(r"[≥≤±]")

_MAX_PER_CHUNK = 8


def _chunk_texts(html_chunk: str) -> List[str]:
    """
    Extract the 'meaningful' text segments from an HTML chunk for error detection.
    Prefer text inside each <td>/<th> cell; if there is no table, take all the text.
    """
    soup = BeautifulSoup(html_chunk, "html.parser")
    cells = soup.find_all(["td", "th"])
    if cells:
        texts = [c.get_text(separator=" ", strip=True) for c in cells]
    else:
        texts = [soup.get_text(separator=" ", strip=True)]
    # drop empties, dedupe while preserving order
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
    """Build an error dict in the format the frontend expects (like _transform_error)."""
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
    Run mock error detection on one HTML chunk, returning a list of error dicts.

    Each original_text is a string that appears VERBATIM in the document, so both
    highlighting and replacement (downloading the corrected file) work correctly.
    """
    errors: List[Dict] = []
    seen = set()  # (original_text, error_type) — avoid duplicates within the same chunk
    section = extract_muc(html_chunk)  # heading/position within the document

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

        # 2) Number stuck to unit (handled first to also fold in a decimal-dot error if any)
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

        # 1) Decimal number using a dot
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

        # 3) Math symbols
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
    """Run mock error detection across every chunk of the document."""
    all_errors: List[Dict] = []
    for idx, chunk in enumerate(html_chunks):
        all_errors.extend(audit_chunk(chunk, rules, idx))
    # Re-index id to be unique across the whole document
    for i, e in enumerate(all_errors):
        e["id"] = f"error_{i}"
    return all_errors
