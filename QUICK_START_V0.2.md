# 🚀 QUICK START - Document Preview Feature

## Tính Năng Mới: Xem Trực Tiếp Tài Liệu với Viện Dẫn

Bạn có thể **xem trực tiếp nội dung tài liệu trên giao diện** với **highlight lỗi** và **viện dẫn sở cứ**.

---

## 📖 Workflow Mới

```
1️⃣  Upload
     └─ Tải file + quy định + sở cứ
     
2️⃣  Preview ← 👈 NEW
     ├─ Xem tài liệu với highlight lỗi
     ├─ Click lỗi → Chi tiết + Đề xuất
     └─ Xem quy định & viện dẫn
     
3️⃣  Review
     ├─ Danh sách lỗi chi tiết
     ├─ Chỉnh sửa đề xuất (nếu cần)
     └─ Chọn lỗi để áp dụng
     
4️⃣  Apply & Download
     └─ Tải file đã sửa
```

---

## 🎯 Các Bước Sử Dụng

### Bước 1: Upload Files

1. Nhập **Tài liệu chính** (Main Document)
2. Chọn **Quy định** (Regulations)
3. Chọn **Sở cứ** (Reference Documents)
4. Click **"Tải lên và Xem trước"**

```
📝 Main Document:      [Chọn file...]
⚖️  Regulations:       [Chọn files...]
📚 References:         [Chọn files...]
                       [Tải lên và Xem trước]
```

---

### Bước 2: Preview Tài Liệu

Tài liệu sẽ **tự động hiển thị** với:

#### 📄 **Bên trái**: Nội dung tài liệu
```
============================================
Hợp đồng Mẫu

Ngày ký: 2024-01-30
Công ty: CÔNG TY TNHH  ← 🔴 Lỗi (highlight)
                        🟡 Cảnh báo (nếu có)
                        🔵 Info (nếu có)

[Nội dung tiếp tục...]
============================================
```

#### 📋 **Bên phải**: Chi tiết lỗi (khi click)

```
Chi tiết Lỗi
─────────────────
🔴 Lỗi

Loại lỗi:
Company Name

Mô tả:
Tên công ty không tuân thủ quy định

Nội dung bị lỗi:
"CÔNG TY TNHH"

Ngữ cảnh:
"...Công ty: CÔNG TY TNHH... là nhà cung cấp..."

💡 Đề xuất sửa chữa:
"Công ty TNHH..."

━━━━━━━━━━━━━━━━━

📚 Viện dẫn Sở Cứ:

⚖️  Quy định
    Tên: Quy định Thành lập Hợp đồng
    Vị trí: Phần 1
    Excerpt: "Công ty phải được viết đầy đủ với định dạng..."

- [Xem đầy đủ]
```

---

### Bước 3: Tương Tác với Lỗi

#### 🎨 **Màu Sắc Lỗi**

| Màu | Ý Nghĩa | Ví Dụ |
|-----|---------|-------|
| 🔴 Đỏ | Lỗi (Error) | Tên công ty sai định dạng |
| 🟡 Vàng | Cảnh báo (Warning) | Định dạng số điện thoại lạ |
| 🔵 Xanh | Thông tin (Info) | Gợi ý cải thiện văn phong |

#### 👆 **Click Vào Lỗi**

```
1. Xác định lỗi trên tài liệu (text được highlight)
2. Click vào text được highlight
3. Side panel bên phải sẽ hiển thị:
   - Mô tả chi tiết
   - Đề xuất sửa chữa
   - Viện dẫn quy định
```

#### 📚 **Xem Quy Định & Sở Cứ**

```
1. Scroll xuống side panel
2. Kéo thả để xem "Tất cả quy định & sở cứ"
3. Xem nội dung từng quy định/sở cứ
4. Trở lại tài liệu nếu cần
```

---

### Bước 4: Quay Lại Danh Sách Lỗi

Sau khi xem trước:

```
1. Click "👁️ Xem trước" trong tab Review
   HOẶC
2. Click nút "Review" ở dưới preview
```

Sẽ quay lại view danh sách lỗi với:
- Bộ lọc theo loại & mức độ
- Chọn lỗi để áp dụng
- Chỉnh sửa đề xuất (nếu cần)

---

### Bước 5: Áp Dụng & Tải Về

```
1. Chọn lỗi cần sửa (checkbox ☑️)
2. Click "Accept" để áp dụng
3. File sẽ được tháo trong thư mục downloads
   tên: [original_name]_corrected.docx
```

---

## 💡 Ví Dụ Thực Tế

### Ví Dụ 1: Lỗi Tên Công Ty

**Tài liệu gốc:**
```
Bên A: CÔNG TY TNHH
```

**Trên preview:**
```
Bên A: [CÔNG TY TNHH]  ← 🔴 Highlight đỏ
         ↑ Click vào đây
```

**Chi tiết hiện lên:**
```
🔴 Lỗi: Company Name
Mô tả: Tên công ty không tuân thủ quy định
Nội dung: "CÔNG TY TNHH"
Đề xuất: "Công ty TNHH"

📚 Viện dẫn:
⚖️  Quy định Thành lập Hợp đồng
    "Tên công ty phải được viết đầy đủ..."
```

---

### Ví Dụ 2: Lỗi Định Dạng Ngày

**Tài liệu gốc:**
```
Ký ngày: 30/01/2024
```

**Trên preview:**
```
Ký ngày: [30/01/2024]  ← 🟡 Highlight vàng
         ↑ Click vào
```

**Chi tiết hiện lên:**
```
🟡 Cảnh báo: Date Format
Mô tả: Định dạng ngày không chuẩn
Nội dung: "30/01/2024"
Đề xuất: "30-01-2024" hoặc "30 tháng 01 năm 2024"

📚 Viện dẫn:
⚖️  Quy định Định dạng Văn bản
    "Ngày tháng năm nên viết theo định dạng..."
```

---

## 🔧 Tính Năng Nâng Cao

### Filter Lỗi trong Preview

*Tính năng này có thể được thêm trong phiên bản tương lai*

### Export Preview

*Chó được lưu preview dưới dạng PDF với highlight*

### Track Changes

*Một phiên bản sau sẽ có Track Changes like Word*

---

## ⚙️ Thiết Lập

### Yêu Cầu

- Python 3.7+
- Node.js 14+
- Browser: Chrome, Firefox, Safari, Edge

### Cài Đặt & Chạy

```bash
# Windows
start_all.bat

# macOS/Linux
bash start_all.sh
```

### Tạo File Test

```bash
# Windows
create_samples.bat

# macOS/Linux
python create_samples.py
```

---

## 🎓 Hướng Dẫn Chi Tiết

### Đối Với Người Quản Lý

1. **Upload** quy định + sở cứ lần đầu
2. Nhân viên upload các tài liệu cần kiểm tra
3. Review lỗi trong danh sách
4. Download file sửa

### Đối Với Nhân Viên Pháp Chế

1. Upload tài liệu chính
2. **[NEW]** Xem trực tiếp trên preview
3. Hiểu rõ lỗi từ viện dẫn
4. Quay lại sửa nếu cần
5. Download file đã kiểm tra

### Đối Với Nhà Phát Triển

1. Xem `CHANGELOG.md` để chi tiết thay đổi
2. Xem `UPGRADE_V0.2.md` để kiến trúc
3. Xem code trong `frontend/src/components/DocumentPreview.js`

---

## 🐛 Troubleshooting

### Preview không hiển thị

```
✓ Check: Backend chạy (http://localhost:5000)
✓ Check: File upload thành công
✓ Check: Browser F12 → Console for errors
✓ Restart services: start_all.bat
```

### Lỗi không hiện highlight

```
✓ Đảm bảo file là .docx (không .doc)
✓ Thử upload file khác
✓ Check backend logs
✓ Khởi động lại
```

### Side panel không hiển thị

```
✓ Click vào text/cell có highlight
✓ Check screen width (minimum 1200px recommended)
✓ Zoom out nếu cần
✓ Refresh page
```

---

## 📞 Hỗ Trợ

Gặp vấn đề?

1. Check `UPGRADE_V0.2.md` - feature details
2. Check `CHANGELOG.md` - changes list
3. Check browser console cho errors
4. Check backend logs

---

## ✨ Tips & Tricks

### Tip 1: Sử Dụng Keyboard
- `Tab` để di chuyển giữa lỗi
- `Enter` để mở chi tiết
- `Esc` để đóng panel

*(Tính năng này có thể thêm trong v0.2.1)*

### Tip 2: Xem Quy Định
- Luôn xem viện dẫn để hiểu lỗi
- Lưu quy định để tham khảo sau

### Tip 3: Chỉnh Sửa Đề Xuất
- Tab Review cho phép chỉnh sửa suggestion
- Sửa nếu cần phù hợp con text cụ thể

---

## 📊 So Sánh: Old vs New

### Cách Cũ (v0.1.0)
```
1. Upload
2. Xem danh sách lỗi trong bảng
3. Không biết lỗi ở đâu trong tài liệu
4. Phải tự mở file để kiểm tra
5. Download kết quả
```

### Cách Mới (v0.2.0)
```
1. Upload
2. PREVIEW: Xem trực tiếp tài liệu với highlight
3. Biết lỗi ở đâu, viện dẫn là gì
4. Hiểu rõ sửa chữa tại sao
5. Review & Download
```

---

## 🎉 Kết Thúc

Đó là tất cả! Hãy thử tính năng mới:

1. Chạy `start_all.bat`
2. Vào http://localhost:3000
3. Upload file test
4. Xem preview
5. Click lỗi
6. Xem viện dẫn
7. Review & Download

**Chúc bạn sử dụng vui vẻ! 🚀**

---

**Phiên bản**: 0.2.0  
**Cập nhật**: April 8, 2026  
**Trạng thái**: ✅ Sẵn sàng sử dụng
