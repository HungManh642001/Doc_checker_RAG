from pathlib import Path
from typing import List, Optional

_DEFAULT_RULES = Path(__file__).parent.parent / "data" / "rules" / "quy_dinh_chung.md"


def load_rules(filepath: str | None = None) -> str:
    """Nạp quy định mặc định (hoặc từ 1 đường dẫn cụ thể)."""
    path = Path(filepath) if filepath else _DEFAULT_RULES
    if path.exists():
        return path.read_text(encoding="utf-8")
    print(f"[RAG] Cảnh báo: không tìm thấy file quy định '{path}'")
    return "Không có quy định chung nào."


def _read_rule_file(path: Path) -> str:
    """
    Đọc nội dung 1 file quy định và trả về plain text / markdown.

    Hỗ trợ: .md, .txt (đọc thẳng) và .docx/.doc (chuyển sang markdown qua mammoth
    để giữ cấu trúc heading + danh sách — quan trọng vì quy định thường đánh số).
    """
    suffix = path.suffix.lower()
    if suffix in (".md", ".txt"):
        return path.read_text(encoding="utf-8")
    if suffix in (".docx", ".doc"):
        try:
            import mammoth
            with open(path, "rb") as f:
                return mammoth.convert_to_markdown(f).value
        except Exception as e:  # noqa: BLE001
            print(f"[RAG] Không đọc được file quy định docx '{path}': {e}")
            return ""
    print(f"[RAG] Định dạng quy định không hỗ trợ: {path}")
    return ""


def load_rules_from_files(paths: Optional[List[str]]) -> str:
    """
    Nạp quy định từ các file người dùng upload.

    - Mỗi file được gắn tiêu đề '# Nguồn: <tên file>' để LLM phân biệt nguồn.
    - Nếu không truyền file nào, hoặc không có file hợp lệ → fallback quy định mặc định.

    Args:
        paths: danh sách đường dẫn file quy định (.md/.txt/.docx). Có thể None.

    Returns:
        Chuỗi quy định gộp, sẵn sàng inject vào system prompt.
    """
    if not paths:
        return load_rules()

    chunks: List[str] = []
    for p in paths:
        path = Path(p)
        if not path.exists():
            print(f"[RAG] Bỏ qua quy định (không tồn tại): {p}")
            continue
        text = _read_rule_file(path).strip()
        if text:
            chunks.append(f"# Nguồn: {path.name}\n{text}")

    if not chunks:
        print("[RAG] Không có file quy định hợp lệ — dùng quy định mặc định.")
        return load_rules()

    print(f"[RAG] Đã nạp quy định từ {len(chunks)} file upload.")
    return "\n\n".join(chunks)
