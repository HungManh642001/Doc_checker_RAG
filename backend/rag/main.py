import time
from knowledge_base.vector_db import get_or_build_index, load_existing_index, test_retrieval
from knowledge_base.rules import load_rules
from document_processing.chunker import chunk_html_table
from audit_logic.audit_engine import run_audit
from audit_logic.audit_models import KetQuaThamDinh

if __name__ == "__main__":
    input_file = 'data/input_documents/Mẫu YCKT đầu vào_1.html'
    try:
        with open(input_file, "r", encoding="utf-8") as f:
            html_upload = f.read()

        print("Đang tiến hành chẻ nhỏ tài liệu HTML...")
        html_chunks = chunk_html_table(html_upload, chunk_size=1, header_rows_count=2)
        print(f"Tài liệu được chia thành {len(html_chunks)} (batches) để AI xử lý.")

        qdrant_index, client = get_or_build_index()
        rules = load_rules()

        all_errors = []

        try:
            for idx, chunk in enumerate(html_chunks):
                if idx == 20:
                    break
                print(f"\n--- Đang thẩm định batch {idx + 1}/{len(html_chunks)} ---")

                try:
                    ket_qua = run_audit(qdrant_index, chunk, rules, top_k=6)
                    if ket_qua.danh_sach_loi:
                        all_errors.extend(ket_qua.danh_sach_loi)
                        print(f"  -> Phát hiện {len(ket_qua.danh_sach_loi)} vấn đề ở batch này.")
                    else:
                        print("  -> Batch này hợp lệ, không có lỗi.")

                except Exception as e:
                    print(f"  -> Lỗi khi xử lý batch {idx + 1}: {e}")
                    pass
        finally:
            client.close()

        print("\n=============================================")
        print("       BÁO CÁO THẨM ĐỊNH HOÀN CHỈNH          ")
        print("=============================================")

        ket_qua_tong_hop = KetQuaThamDinh(danh_sach_loi=all_errors)
        print(ket_qua_tong_hop.model_dump_json(indent=2))

    except FileNotFoundError:
        print(f"Vui lòng đặt file tài liệu cần thẩm định vào đường dẫn: {file_tai_lieu_dau_vao}")