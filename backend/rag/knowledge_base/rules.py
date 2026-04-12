import os

def load_rules(filepath='./data/rules/quy_dinh_chung.md'):
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    
    return "Không có quy định chung nào."