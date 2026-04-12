# Guide: Sử dụng Hệ thống Thẩm định Tài liệu

## Bắt đầu nhanh chóng

### 1. Cải đặt & Chạy Backend

```bash
cd D:\Workspace\VTX\Doc_checker\backend

# Tạo virtual environment
python -m venv venv

# Kích hoạt
.\venv\Scripts\activate

# Cài packages
pip install -r requirements.txt

# Chạy Flask server
python run.py
```

Backend sẽ chạy ở `http://localhost:5000`

### 2. Cài đặt & Chạy Frontend

Mở terminal khác:

```bash
cd D:\Workspace\VTX\Doc_checker\frontend

# Cài packages
npm install

# Chạy React app
npm start
```

Frontend sẽ mở ở `http://localhost:3000`

## Sử dụng Ứng dụng

### Bước 1: Upload Tài liệu
1. Chọn **Tài liệu cần thẩm định** (bắt buộc) - file DOCX
2. Chọn **Văn bản sở cứ** (tuỳ chọn) - các file tham chiếu
3. Chọn **Quy định** (tuỳ chọn) - các file quy định
4. Nhấn **"Tải lên và Phân tích"**

### Bước 2: Xem Kết quả Phân tích
- Danh sách các lỗi được phát hiện
- Các loại: Lỗi (đỏ), Cảnh báo (vàng), Thông tin (xanh)
- Mỗi lỗi hiển thị:
  - Mô tả lỗi
  - Nội dung lỗi
  - Đề xuất sửa chữa

### Bước 3: Chỉnh sửa Đề xuất (tuỳ chọn)
- Nhấn **✏️ Chỉnh sửa** trên bất kỳ lỗi nào
- Sửa đổi đề xuất sửa chữa
- Nhấn **✓ Lưu** để áp dụng

### Bước 4: Chọn và Áp dụng
1. Chọn các lỗi từ danh sách
   - Tick vào checkbox để chọn lỗi
   - Tick "Chọn tất cả" để chọn tất cả lỗi hiển thị
2. Sử dụng bộ lọc nếu cần
3. Nhấn **"✓ Chấp nhận N đề xuất"** để áp dụng sửa chữa

### Bước 5: Tải File Sửa chữa
- File sẽ tự động tải về
- Tài liệu giữ nguyên định dạng gốc (bảng biểu, hình ảnh)

## 💡 Mẹo

- **Bộ lọc**: Lọc lỗi theo mức độ hoặc loại để dễ quản lý
- **Chỉnh sửa hàng loạt**: Chọn nhiều lỗi cùng lúc
- **Quay lại**: Nhấn "← Quay lại" để xử lý tài liệu mới
- **Không chấp nhận lỗi**: Đơn giản là không chọn lỗi đó

## 🐛 Xử lý sự cố

### "Network Error"
- Đảm bảo backend đang chạy (`http://localhost:5000` trả về 200)
- Kiểm tra firewall

### "File Upload Failed"
- Đảm bảo file là .DOCX
- Kích thước file < 100MB

### Backend error
- Kiểm tra terminal backend logs
- Đảm bảo tất cả dependencies đã được cài

## 📚 Các ví dụ sử dụng

### Ví dụ 1: Kiểm tra Hợp đồng
1. Upload hợp đồng cần kiểm tra
2. Upload mẫu hợp đồng theo quy định
3. Upload quy định liên quan
4. Hệ thống sẽ phát hiện các lỗi
5. Áp dụng sửa chữa

### Ví dụ 2: Thẩm định Báo cáo
1. Upload báo cáo cần thẩm định
2. Không cần file sở cứ
3. Upload quy định báo cáo
4. Kiểm tra kết quả
5. Xuất báo cáo sửa chữa

## 🔍 Các loại lỗi được phát hiện

| Loại | Mô tả | Ví dụ |
|------|-------|-------|
| spacing | Khoảng trắng thừa | "Hello  World" |
| format | Định dạng không nhất quán | "CÔNG TY" vs "Công ty" |
| date_format | Ngày tháng không đúng | "2026-04-08" vs "08/04/2026" |
| currency | Ký hiệu tiền tệ không nhất quán | "$100" vs "100 USD" |
| number_mismatch | Số tiền không khớp | Chữ vs số |
| company_name | Tên công ty không khớp quy định | "Công ty ABC" vs quy định |

---

**Thời gian cập nhật**: April 2026
