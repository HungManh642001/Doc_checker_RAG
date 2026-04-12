# 🎯 Tính Năng Mới: Xử Lý Lỗi Trực Tiếp Trên Preview

## Tổng Quan

Người dùng bây giờ có thể **xử lý lỗi trực tiếp trên tài liệu preview** thay vì chỉ xem danh sách lỗi. Ba cách xử lý:

1. ✅ **Chấp nhận đề xuất** - Sửa theo gợi ý của hệ thống
2. ✏️ **Sửa thủ công** - Nhập nội dung sửa tùy ý
3. ❌ **Bỏ qua lỗi** - Lỗi sai, không cần sửa

---

## Workflow & UX

### Bước 1: Upload & Preview

```
1. Upload tài liệu + quy định
   ↓
2. Xem preview với highlight lỗi (🔴 🟡 🔵)
   ↓
3. Click vào lỗi để xem chi tiết
```

### Bước 2: Xử Lý Lỗi Trên Preview

Khi click vào lỗi, side panel hiển thị:

```
┌─────────────────────────────────────────────┐
│ 📋 Chi tiết lỗi                             │
├─────────────────────────────────────────────┤
│                                              │
│ 🔴 Mức độ: Lỗi                             │
│ 📌 Loại: Company Name                       │
│ 📝 Mô tả: Tên công ty không tuân thủ...    │
│ 🔍 Nội dung: "CÔNG TY TNHH"                │
│ 📖 Ngữ cảnh: "...CÔNG TY TNHH là nhà..."   │
│                                              │
│ 💡 Đề xuất: "Công ty TNHH"                │
│                                              │
│ 📚 Viện dẫn: ⚖️ Quy định...                │
│                                              │
├─────────────────────────────────────────────┤
│ ⚙️ Xử lý lỗi                                │
│                                              │
│ [✓ Accept]  [✏️ Edit]                      │
│ [✗ Reject (full width)]                    │
│                                              │
└─────────────────────────────────────────────┘
```

---

## 3 Cách Xử Lý Lỗi

### Cách 1️⃣: Chấp Nhận Đề Xuất (Accept)

**Bước:**
1. Click lỗi trên tài liệu
2. Xem chi tiết + đề xuất
3. Click **"✓ Chấp nhận đề xuất"**
4. Status: ✓ Đã chấp nhận

**Hiệu quả:**
- Lỗi được highlighted bằng màu xanh (#27ae60)
- Button disable để không duplicate
- Khi apply, sửa theo suggestion

**Ví dụ:**
```
Trước: "Bên A: CÔNG TY TNHH"
Sau:  "Bên A: Công ty TNHH"
```

---

### Cách 2️⃣: Sửa Thủ Công (Manual Edit)

**Bước:**
1. Click lỗi trên tài liệu
2. Click **"✏️ Sửa thủ công"**
3. Modal edit xuất hiện:
   ```
   ✏️ Sửa thủ công:
   ┌─────────────────────────┐
   │ Công ty TNHH             │  (editable)
   │                          │
   └─────────────────────────┘
   [💾 Lưu sửa] [✕ Hủy]
   ```
4. Nhập nội dung sửa theo ý
5. Click **"💾 Lưu sửa"**
6. Status: ✏️ Đã chỉnh sửa

**Hiệu quả:**
- Lỗi được highlighted bằng màu xanh (#3498db)
- Giữ custom value
- Khi apply, sửa theo custom value

**Ví dụ:**
```
Trước: "Bên A: CÔNG TY TNHH ABC XYZ"
Suggestion: "Công ty TNHH"
Bạn sửa: "Công ty TNHH ABC XYZ"  (custom)
Sau:  "Bên A: Công ty TNHH ABC XYZ"
```

---

### Cách 3️⃣: Bỏ Qua Lỗi (Reject)

**Bước:**
1. Click lỗi trên tài liệu
2. Click **"✗ Bỏ qua lỗi này"**
3. Status: ✗ Bỏ qua

**Hiệu quả:**
- Lỗi được strikethrough (gạch ngang)
- Button disable
- Khi apply, KHÔNG sửa gì

**Ví dụ:**
```
Trước: "Bên A: CÔNG TY TNHH"
       ~~CÔNG TY TNHH~~  (strikethrough)
Sau:  "Bên A: CÔNG TY TNHH"  (giữ nguyên)
```

---

## Visual Indicators

### Màu Sắc & Icon

| Status | Màu | Icon | Ý Nghĩa |
|--------|-----|------|---------|
| Accepted | 🟢 Xanh (#27ae60) | ✓ | Chấp nhận |
| Edited | 🔵 Xanh dương (#3498db) | ✏️ | Sửa thủ công |
| Rejected | 🔴 Xám (strikethrough) | ✗ | Bỏ qua |
| Pending | 🔴 🟡 🔵 (severity) | ⚪ | Chưa xử lý |

### Trên Tài Liệu Preview

```
Lỗi chưa xử lý:
"CÔNG TY TNHH" ← 🔴 (hover: click để xử lý)

Đã chấp nhận:
[CÔNG TY TNHH] ✓ ← 🟢 (background xanh)

Đã sửa thủ công:
[CÔNG TY ABC] ✏️ ← 🔵 (background xanh dương)

Bỏ qua:
~~CÔNG TY~~ ✗ ← Xám, gạch ngang
```

---

## Tương Tác Flow

### Flow Đầy Đủ

```
User Upload
     ↓
Preview Auto-load
     ↓
        Click Error
           ↓
        Show Detail Panel
           ↓
     ┌─────┬──────┬────────┐
     ↓     ↓      ↓        ↓
  Accept Edit Reject  Toggle Ref
     ↓     ↓      ↓        ↓
  ✓Done ✏Edit ✗Done Show Reg
     ↓     ↓      ↓        ↓
    (Continued Interaction...)
     ↓     ↓      ↓
     └─────┴──────┴────────┘
            ↓
   Click Another Error
   or Click "Review" Button
            ↓
        Go to Review Tab
            ↓
    Show All Errors + Status
    (✓ Accepted, ✏ Edited, ✗ Rejected)
            ↓
      Select & Apply
            ↓
        Download File
```

---

## 💾 Backend Changes

### Error Status Tracking

Frontend sends to backend when applying:

```json
{
  "acceptedSuggestions": [
    {
      "id": "error_1",
      "elementId": "para_0",
      "type": "company_name",
      "originalText": "CÔNG TY TNHH",
      "fixedValue": "Công ty TNHH",              // from accept/edit
      "status": "accepted" | "edited",           // NOT rejected
      "startOffset": 10,
      "endOffset": 20
    },
    // rejected errors NOT included
  ]
}
```

### Apply Endpoint Update

`POST /api/apply-suggestions/<session_id>`

```python
# Updated to handle fixedValue
for suggestion in data['acceptedSuggestions']:
    if suggestion['status'] == 'rejected':
        continue  # Skip
    
    # Use fixedValue (from accept or manual edit)
    value_to_apply = suggestion['fixedValue']
    # Apply to document at startOffset:endOffset
```

---

## 🎨 Component Architecture

### DocumentPreview.js Updates

```javascript
// New State
const [errorStatus, setErrorStatus] = useState({});
const [editingErrorId, setEditingErrorId] = useState(null);
const [editingValue, setEditingValue] = useState('');

// New Handlers
handleAcceptSuggestion(error)     // Set status: accepted
handleStartEdit(error)             // Show textarea
handleSaveEdit(error)              // Set status: edited + value
handleRejectError(error)           // Set status: rejected

// UI Sections
Action Buttons
├─ Accept Button
├─ Edit Button (toggle textarea)
├─ Reject Button
└─ Edit Textarea (if editing)

Status Indicators
├─ ✓ Accepted (green)
├─ ✏️ Edited (blue)
└─ ✗ Rejected (gray)
```

### App.js Updates

```javascript
// New State
const [errorStatus, setErrorStatus] = useState({});

// New Handler
handleErrorStatusChange(errorId, status, value)
{
  // Track: which error, status, custom value
}

// Updated handleApplySuggestions
Filter errors:
├─ Skip rejected (status === 'rejected')
├─ Use fixedValue if edited
└─ Use suggestion if accepted
```

---

## 🧪 Test Scenarios

### Test 1: Accept Workflow

```
1. Upload file with error "CÔNG TY"
2. Preview load, see highlight
3. Click "CÔNG TY" 
4. Click "✓ Chấp nhận đề xuất"
5. Button disabled ✓
6. Status green "✓ Đã chấp nhận" ✓
7. On highlighted text: icon change to "✓" ✓
8. Review tab → show error with status ✓
9. Apply → use suggestion "Công ty TNHH" ✓
10. Result: "Bên A: Công ty TNHH" ✓
```

### Test 2: Edit Workflow

```
1. Upload file with error "CÔNG TY"
2. Preview load, click error
3. Click "✏️ Sửa thủ công"
4. Textarea appear with suggestion
5. Change to "Công ty ABC XYZ"
6. Click "💾 Lưu sửa"
7. Status blue "✏️ Đã chỉnh sửa" ✓
8. Icon change to "✏️" ✓
9. Review tab → show error with edited value
10. Apply → use edited value "Công ty ABC XYZ" ✓
11. Result: "Bên A: Công ty ABC XYZ" ✓
```

### Test 3: Reject Workflow

```
1. Upload file with error "CÔNG TY"
2. Preview load, click error
3. Click "✗ Bỏ qua lỗi này"
4. Button disabled ✓
5. Status gray "✗ Bỏ qua lỗi này" ✓
6. Highlighted text strikethrough ✓
7. Icon change to "✗" ✓
8. Review tab → error marked as rejected
9. Apply → ERROR NOT APPLIED ✓
10. Result: "Bên A: CÔNG TY" (unchanged) ✓
```

### Test 4: Multiple Operations

```
1. Upload file with 5 errors
2. Error 1: Accept
3. Error 2: Edit (custom value)
4. Error 3: Reject
5. Error 4: Accept
6. Error 5: Edit
7. Review tab: Show all statuses
8. Apply: Only 1,2,4,5 applied (3 skipped)
9. Download: Verify all correct values
```

---

## 📱 Responsive Design

### Desktop (> 1200px)
```
┌─────────────────────┬──────────────┐
│   Preview (flex)    │  Details (400px) │
│   + Errors highlight│  + Buttons       │
│   + Tables          │  + Textarea      │
│                     │  + References    │
└─────────────────────┴──────────────┘
```

### Tablet (768px - 1200px)
```
┌──────────────────────┐
│  Preview             │
│  + Errors highlight  │
│  + Tables            │
├──────────────────────┤
│ Details (full width) │
│ + Buttons            │
│ + Textarea           │
└──────────────────────┘
```

### Mobile (< 768px)
```
┌──────────────────────┐
│  Preview (scroll)    │
│  + Errors highlight  │
│  + Tables (horiz)    │
├──────────────────────┤
│ Details (scroll)     │
│ + Buttons            │
│ + Textarea           │
└──────────────────────┘
```

---

## 🔒 Data Flow

```
User Action (Click Button)
    ↓
handleAccept/Edit/Reject(error)
    ↓
setErrorStatus(prev => {..., [errorId]: {status, value}})
    ↓
DocumentPreview Re-render
├─ Update highlight color
├─ Update icon indicator
└─ Update action buttons status
    ↓
App.handleErrorStatusChange(errorId, status, value)
    ↓
setErrorStatus(prev => {...})  [in App]
    ↓
[When Apply]
ReviewTab → handleApplySuggestions(errors)
    ↓
Filter based on errorStatus
├─ Skip rejected (status === 'rejected')
├─ Use fixedValue if edited
└─ Use suggestion if accepted
    ↓
POST /api/apply-suggestions
    ↓
Backend applies to DOCX
    ↓
Download file
```

---

## 🎯 Benefits

1. **Faster Workflow**: Fix errors without switching tabs
2. **Visual Feedback**: See immediately what status
3. **Flexibility**: Accept, edit, or reject per error
4. **Precision**: Custom fixes for complex cases
5. **Control**: Don't apply wrong suggestions
6. **Efficiency**: No need to re-review in list form

---

## 🚀 Future Enhancements

- [ ] Undo/Redo for error actions
- [ ] Redo button for rejected errors
- [ ] Keyboard shortcuts (Enter=accept, Tab=next)
- [ ] Batch actions (accept all errors of type X)
- [ ] Side-by-side before/after view
- [ ] Export preview with markup
- [ ] Save changes to document without download
- [ ] Collaborative editing mode

---

**Version**: 0.2.1 (In-line Error Management)  
**Feature**: Complete inline error handling  
**Status**: ✅ Ready for testing
