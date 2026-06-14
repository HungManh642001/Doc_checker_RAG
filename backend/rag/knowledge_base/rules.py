from pathlib import Path
from typing import List, Optional

_DEFAULT_RULES = Path(__file__).parent.parent / "data" / "rules" / "quy_dinh_chung.md"


def load_rules(filepath: str | None = None) -> str:
    """Load the default rules (or from a specific path)."""
    path = Path(filepath) if filepath else _DEFAULT_RULES
    if path.exists():
        return path.read_text(encoding="utf-8")
    print(f"[RAG] Cảnh báo: không tìm thấy file quy định '{path}'")
    return "Không có quy định chung nào."


def _read_rule_file(path: Path) -> str:
    """
    Read the content of one rules file and return plain text / markdown.

    Supports: .md, .txt (read directly) and .docx/.doc (converted to markdown via
    mammoth to preserve heading + list structure — important because rules are
    usually numbered).
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
    Load rules from user-uploaded files.

    - Each file gets a '# Nguồn: <file name>' heading so the LLM can distinguish sources.
    - If no files are passed, or no file is valid → fall back to the default rules.

    Args:
        paths: list of rules-file paths (.md/.txt/.docx). May be None.

    Returns:
        The merged rules string, ready to inject into the system prompt.
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
