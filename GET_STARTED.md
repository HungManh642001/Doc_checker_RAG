# 🚀 GET STARTED - Hệ thống Thẩm định Tài liệu

## Bắt Đầu Nhanh Chóng (5 phút)

### 1. **Chạy Toàn Bộ Hệ Thống**

#### Windows:
```bash
start_all.bat
```

Hoặc chạy từng cái:
```bash
# Terminal 1 - Backend
cd backend
.\venv\Scripts\activate.bat
pip install -r requirements.txt
python run.py

# Terminal 2 - Frontend
cd frontend
npm install
npm start
```

#### macOS/Linux:
```bash
bash start_all.sh
```

### 2. **Mở Ứng Dụng**

- Frontend: [http://localhost:3000](http://localhost:3000)
- Backend: [http://localhost:5000](http://localhost:5000)

### 3. **Tạo File Test**

```bash
# Windows
create_samples.bat

# macOS/Linux
python create_samples.py
```

Files sẽ được tạo trong thư mục `samples/`

### 4. **Dùng Thử**

1. Vào http://localhost:3000
2. Click "Chọn tài liệu (DOCX)" - chọn `samples/sample_main.docx`
3. Tuỳ chọn: Chọn `samples/sample_regulation.docx` trong "Quy định"
4. Click "Tải lên và Phân tích"
5. Xem các lỗi phát hiện
6. Chọn lỗi cần sửa
7. Click "Chấp nhận" để áp dụng
8. Tải file sửa chữa về

---

## 📚 Tài Liệu Chi Tiết

| Tài Liệu | Nội Dung |
|----------|---------|
| [QUICKSTART.md](QUICKSTART.md) | Hướng dẫn sử dụng cơ bản |
| [README.md](README.md) | Tài liệu chính chi tiết |
| [API_DOCUMENTATION.md](API_DOCUMENTATION.md) | Tài liệu API endpoints |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Kiến trúc hệ thống |
| [TROUBLESHOOTING.md](TROUBLESHOOTING.md) | Xử lý sự cố |
| [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) | Tóm tắt toàn dự án |

---

## 🛠️ Cấu Hình Lần Đầu

### Xóa & Cài Lại

```bash
# Backend
cd backend
rmdir /s /q venv  (Windows) hoặc rm -rf venv (Linux/Mac)
pip install -r requirements.txt

# Frontend  
cd frontend
rmdir /s /q node_modules package-lock.json (Windows)
rm -rf node_modules package-lock.json (Linux/Mac)
npm install
```

---

## 🆘 Gắp Vấn Đề?

### Backend không chạy
```bash
# Kiểm tra
python --version
pip list | grep Flask

# Cài lại
cd backend
pip install -r requirements.txt

# Kiểm tra port
# Windows: netstat -ano | findstr :5000
# Mac/Linux: lsof -i :5000
```

### Frontend không chạy
```bash
# Kiểm tra
node --version
npm --version

# Cài lại
cd frontend
npm cache clean --force
rm -rf node_modules package-lock.json
npm install
```

### Upload fail
- ✓ File phải là .docx
- ✓ File < 100MB
- ✓ Backend đang chạy
- ✓ Không có lỗi typo trong API

### Xem logs
```bash
# Backend logs: Xem terminal backend
# Frontend logs: Mở DevTools (F12) > Console tab
```

---

## 💡 Mẹo Hữu Ích

1. **Test nhanh**: Dùng `create_samples.bat/sh` để tạo file test
2. **Clear data**: Xóa thư mục `backend/uploads/` để reset sessions
3. **Debug**: Mở browser DevTools (F12) để xem API requests
4. **Ports**: Nếu ports 3000 hoặc 5000 bị chiếm:
   - Đổi port trong `backend/run.py` 
   - Đổi proxy trong `frontend/package.json`

---

## 🎯 Sử Dụng Ứng Dụng

### Quy Trình

1. **Upload** → Tải lên 1-3 file DOCX
2. **Phân Tích** → Hệ thống tự động phát hiện lỗi
3. **Xem** → Danh sách lỗi với đề xuất sửa chữa
4. **Chỉnh Sửa** → Tuỳ chọn: Sửa đề xuất
5. **Chấp Nhận** → Chọn lỗi để sửa
6. **Tải Về** → File DOCX đã sửa chữa

### Mức Độ Lỗi

- 🔴 **Lỗi (Error)**: Phải sửa
- 🟡 **Cảnh Báo (Warning)**: Nên sửa
- 🔵 **Thông Tin (Info)**: Gợi ý

### Loại Lỗi

- Định dạng (công ty, tên gọi)
- Khoảng trắng thừa
- Ngày tháng không đúng
- Tiền tệ không nhất quán
- Số không khớp
- Quy định

---

## 📁 Cấu Trúc File Quan Trọng

```
Doc_checker/
├── start_all.bat / start_all.sh     ← Chạy tất cả
├── create_samples.bat / .py         ← Tạo file test
│
├── backend/                          ← Server
│   ├── run.py                        ← Chạy backend
│   ├── app/                          ← Code chính
│   └── uploads/                      ← File upload
│
├── frontend/                         ← Web app
│   ├── public/index.html
│   └── src/
│
├── README.md                         ← Tài liệu chính
├── QUICKSTART.md                     ← Bắt đầu nhanh
└── API_DOCUMENTATION.md              ← API docs
```

---

## 🔗 Liên Kết Nhanh

- **Frontend**: http://localhost:3000
- **Backend**: http://localhost:5000
- **API Health**: http://localhost:5000/api/health

---

## 📞 Hỗ Trợ

### Nếu mọi việc không hoạt động:

1. Xem [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
2. Kiểm tra console/terminal để xem lỗi
3. Đảm bảo Python 3.8+ và Node 14+ được cài
4. Thử xóa `venv` và `node_modules` rồi cài lại
5. Kiểm tra cổng 3000 và 5000 không bị chiếm

---

## ✅ Checklist

Trước khi dùng:
- [ ] Python 3.8+ cài
- [ ] Node 14+ cài
- [ ] Clone/download project
- [ ] Đọc README.md
- [ ] Chạy start_all.bat/start_all.sh HOẶC setup từng cái
- [ ] Mở http://localhost:3000
- [ ] Tạo samples nếu cần
- [ ] Upload file test
- [ ] Kiểm tra kết quả

---

## 🚀 Tiếp Theo

Sau khi setup thành công:

1. **Hiểu kiến trúc**: Xem [ARCHITECTURE.md](ARCHITECTURE.md)
2. **Tinh chỉnh**: Sửa quy tắc lỗi trong `backend/app/ai_simulator.py`
3. **Mở rộng**: Thêm tính năng mới
4. **Deploy**: Chuẩn bị cho production

---

## 💬 Thông Tin Hữu Ích

- **Backend Framework**: Flask (Python)
- **Frontend Framework**: React (JavaScript)
- **Database**: File-based (có thể thêm SQLite/PostgreSQL)
- **Format**: DOCX (Microsoft Word 2007+)

---

**⏱️ Thời gian setup**: 5 phút
**📦 Dung lượng**: ~500MB (với dependencies)
**💻 Requirements**: Python 3.8+, Node 14+, 1GB RAM tối thiểu

---

**Sẵn sàng chưa? 🎉** Chạy `start_all.bat` (Windows) hoặc `bash start_all.sh` (Mac/Linux) ngay bây giờ!

