# Hệ thống AI thẩm định YCKT nội bộ

## Tổng quan dự án
- Hệ thống tự động thẩm định tài liệu Yêu Cầu Kỹ Thuật (YCKT) theo quy định nội bộ và sở cứ liên quan
- Stack: Flask (backend) + React/Vite (frontend)
- LLM: Qwen3-27B qua vLLM server nội bộ, truy cập qua LiteLLM proxy

## Cấu trúc thư mục
- `backend/` — Flask app, pipeline AI
- `frontend/` — React UI
- `docs/references/` — NĐ 86/2012, sở cứ
- `docs/samples/` — mẫu tài liệu cần thẩm định
- `docs/faults/` - bảng lỗi thường gặp

## LLM endpoint nội bộ
- Base URL: http://[LITELLM_HOST]:4000
- Model: qwen3:27b (hoặc tên alias trong LiteLLM)

## Quy tắc code
- Python: black formatter, type hints bắt buộc
- Tên biến và comment: tiếng Anh, docstring: tiếng Việt được
- Mọi thay đổi logic AI pipeline phải kèm test case

