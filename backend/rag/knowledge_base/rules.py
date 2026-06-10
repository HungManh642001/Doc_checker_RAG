from pathlib import Path

_DEFAULT_RULES = Path(__file__).parent.parent / "data" / "rules" / "quy_dinh_chung.md"


def load_rules(filepath: str | None = None) -> str:
    path = Path(filepath) if filepath else _DEFAULT_RULES
    if path.exists():
        return path.read_text(encoding="utf-8")
    print(f"[RAG] Cảnh báo: không tìm thấy file quy định '{path}'")
    return "Không có quy định chung nào."