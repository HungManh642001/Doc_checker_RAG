# Hệ thống Thẩm định Tài liệu

Một ứng dụng web hiện đại để phát hiện lỗi và đề xuất sửa chữa tài liệu DOCX.

## 🎯 Tính năng chính

- **Tải tài liệu**: Hỗ trợ tải tài liệu cần thẩm định, văn bản sở cứ, và quy định
- **Phân tích tự động**: Phát hiện lỗi theo các quy tắc được xác định trước
- **Đề xuất sửa chữa**: Cung cấp các đề xuất sửa chữa thông minh
- **Chỉnh sửa trực tiếp**: Cho phép chỉnh sửa đề xuất trước khi áp dụng
- **Xuất tài liệu**: Tải về tài liệu đã sửa chữa với định dạng gốc (DOCX) được bảo toàn

## 🏗️ Kiến trúc

```
Doc_checker/
├── backend/              # Flask API
│   ├── app/
│   │   ├── __init__.py  # Khởi tạo Flask app
│   │   ├── api.py       # API routes
│   │   ├── document_processor.py  # Xử lý file DOCX
│   │   └── ai_simulator.py        # Mô phỏng phân tích AI
│   ├── uploads/         # Thư mục tài liệu tải lên
│   ├── requirements.txt  # Dependencies
│   ├── run.py          # Entry point
│   └── .env            # Biến môi trường
│
└── frontend/            # React app
    ├── public/
    │   └── index.html
    ├── src/
    │   ├── components/
    │   │   ├── DocumentUpload.js      # Component tải tài liệu
    │   │   ├── DocumentUpload.css
    │   │   ├── ErrorViewer.js         # Component xem lỗi
    │   │   └── ErrorViewer.css
    │   ├── App.js       # Main app component
    │   ├── App.css
    │   ├── index.js     # React entry point
    │   └── index.css
    ├── package.json
    └── .env
```

## 📋 API Endpoints

### POST `/api/upload`
Tải lên tài liệu
- **Body**: MultipartForm (mainDocument, referenceDocuments[], regulations[])
- **Response**: `{ sessionId, documentsCount }`

### POST `/api/analyze/<session_id>`
Phân tích tài liệu
- **Response**: `{ sessionId, errors[] }`

### POST `/api/apply-suggestions/<session_id>`
Áp dụng các sửa chữa được chấp nhận
- **Body**: `{ acceptedSuggestions: [{elementId, newText}] }`
- **Response**: `{ message, downloadUrl }`

### GET `/api/download/<session_id>/<filename>`
Tải về file đã sửa chữa

## 🚀 Hướng dẫn chạy

### Backend Setup

1. **Tạo virtual environment**:
```bash
cd backend
python -m venv venv
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # macOS/Linux
```

2. **Cài đặt dependencies**:
```bash
pip install -r requirements.txt
```

3. **Chạy server**:
```bash
python run.py
```

Server sẽ chạy trên `http://localhost:5000`

### Frontend Setup

1. **Cài đặt dependencies**:
```bash
cd frontend
npm install
```

2. **Chạy development server**:
```bash
npm start
```

Ứng dụng sẽ mở tại `http://localhost:3000`

## 🔄 Luồng công việc

1. **Upload**: Tải lên tài liệu cần thẩm định, văn bản sở cứ (tuỳ chọn), và quy định (tuỳ chọn)
2. **Phân tích**: Hệ thống tự động phân tích tài liệu
3. **Xem kết quả**: Hiển thị danh sách lỗi với các đề xuất sửa chữa
4. **Chỉnh sửa**: Có thể chỉnh sửa đề xuất nếu cần thiết
5. **Chấp nhận**: Chọn các lỗi để sửa chữa
6. **Xuất file**: Tải về tài liệu đã sửa chữa

## 🤖 Mô phỏng AI

Hiện tại, hệ thống sử dụng mô phỏng AI để phát hiện lỗi. Các loại lỗi mô phỏng:

- **Spacing**: Khoảng trắng thừa
- **Format**: Lỗi định dạng (ví dụ: tên công ty không nhất quán)
- **Number Mismatch**: Số tiền không khớp
- **Date Format**: Ngày tháng năm không đúng định dạng
- **Company Name**: Tên công ty không khớp quy định
- **Currency**: Ký hiệu tiền tệ không nhất quán

## 🔧 Tùy chỉnh

### Thêm quy tắc phát hiện lỗi mới

Chỉnh sửa `backend/app/ai_simulator.py`:

```python
def _init_patterns(self):
    return {
        'your_error_type': {
            'pattern': r'regex_pattern',
            'message': 'Mô tả lỗi',
            'severity': 'error'  # error, warning, info
        }
    }
```

### Thay đổi cổng chạy

Backend: Sửa biến `port` trong `backend/run.py`
Frontend: Sửa `package.json` proxy field

## 📦 Dependencies

**Backend**:
- Flask 3.0.0
- python-docx 0.8.11
- Flask-CORS 4.0.0

**Frontend**:
- React 18.2.0
- Axios 1.6.0
- React Toastify 9.1.3

## ⚠️ Lưu ý

- Chỉ hỗ trợ file DOCX (Microsoft Word 2007+)
- Kích thước file tối đa: 100MB
- Các bảng và định dạng được bảo toàn khi xuất tài liệu
- Session được lưu trữ trong `/backend/uploads/`

## 🔐 Bảo mật

- Các file tải lên được lưu trong thư mục riêng biệt với session ID duy nhất
- Không tạo bản sao vĩnh viễn của tài liệu gốc
- CORS được cấu hình cho phép kết nối từ frontend

## 📝 Giấy phép

MIT License - Tự do sử dụng cho mục đích thương mại và cá nhân

## 👨‍💻 Hỗ trợ

Để báo cáo lỗi hoặc đề xuất tính năng, vui lòng tạo issue trong repository.

---

**Phiên bản**: 0.1.0
**Cập nhật lần cuối**: April 2026
