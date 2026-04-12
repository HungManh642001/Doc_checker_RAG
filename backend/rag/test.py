import time
from knowledge_base.vector_db import get_or_build_index, load_existing_index, test_retrieval
from knowledge_base.rules import load_rules
from document_processing.chunker import chunk_html_table
from audit_logic.audit_engine import run_audit
from audit_logic.audit_models import KetQuaThamDinh



input_file = 'data/input_documents/Mẫu YCKT đầu vào_1.html'

with open(input_file, "r", encoding='utf-8') as f:
    html_upload = f.read()

print("Đang tiến hành chunking tài liệu")
html_chunks = chunk_html_table(html_upload, chunk_size=1, header_rows_count=2)
print(f"Tài liệu được chia thành {len(html_chunks)} (batches) để AI xử lý.")

# qdrant_index, client = get_or_build_index()
qdrant_index, client = load_existing_index()

try: 
    test_retrieval(qdrant_index, html_chunks[4], top_k=6)
    print(html_chunks[4])

    start_time = time.time()
    rules = load_rules()
    ketqua = run_audit(qdrant_index, html_chunks[4], rules, top_k=6)
    end_time = time.time()
    print(f"Thời gian thẩm định: {end_time - start_time}")
finally:
    client.close()

print(ketqua)

all_errors = []
all_errors.extend(ketqua.danh_sach_loi)
ket_qua_tong_hop = KetQuaThamDinh(danh_sach_loi=all_errors)
print(ket_qua_tong_hop.model_dump_json(indent=2))
print(ket_qua_tong_hop.danh_sach_loi)
