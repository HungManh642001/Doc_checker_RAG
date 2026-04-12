# 🎨 Visual Guide - Inline Error Handling UI

## Before (v0.2.0)

### Preview View
```
┌─────────────────────────────────────────────────────┐
│ 📄 Xem trước tài liệu                        [✕]    │
├─────────────────────────────────────────────────────┤
│                                                      │
│  Hợp đồng Mẫu                                       │
│                                                      │
│  Ngày ký: 2024-01-30                               │
│  Công ty: CÔNG TY TNHH 🔴  ← Error highlight only  │
│                                                      │
│  [Document content...]                              │
│                                                      │
├─────────────────────────────────────────────────────┤
│ 🟢 Lỗi  🟡 Cảnh báo  🔵 Thông tin           │ Legend │
└─────────────────────────────────────────────────────┘
        Sidebar (Right)
        ┌────────────────────┐
        │ 👆 Click error     │
        │    to see detail   │
        │                    │
        │ Details when       │
        │ error selected:    │
        │ - Severity        │
        │ - Type            │
        │ - Description     │
        │ - Suggestion      │
        │ - Reference       │
        │                    │
        │ [View References] │
        └────────────────────┘
```

### Review View
```
┌──────────────────────────────────────────────────────┐
│ 📋 Kết quả Phân tích                                 │
├──────────────────────────────────────────────────────┤
│ Total: 5 | 🔴 2 | 🟡 2 | 🔵 1                        │
├──────────────────────────────────────────────────────┤
│ [Filter] [Select All]                               │
├──────────────────────────────────────────────────────┤
│ ☐ 🔴 Lỗi: Company Name                             │
│   Nội dung: "CÔNG TY TNHH"                          │
│   Đề xuất: "Công ty TNHH"                           │
│                                                      │
│ ☐ 🟡 Cảnh báo: Date Format                         │
│   Nội dung: "30/01/2024"                            │
│   Đề xuất: "30-01-2024"                             │
│                                                      │
│ [ต Accept] [Review] [← Back]                        │
└──────────────────────────────────────────────────────┘

⚠️ NO inline editing in v0.2.0
   Must go back to Review to edit
```

---

## After (v0.2.1)

### Preview View
```
┌──────────────────────────────────────────────────────┬──────────────────┐
│ 📄 Xem trước tài liệu                        [✕]     │                  │
├──────────────────────────────────────────────────────┤ 📋 Chi tiết      │
│                                                      │                  │
│  Hợp đồng Mẫu                                       │ 🔴 Lỗi           │
│                                                      │ Loại: Company... │
│  Ngày ký: 2024-01-30                               │ Mô tả: Tên công  │
│  Công ty: [CÔNG TY TNHH] 🔴  ← Highlight 1         │ ty không tuân...  │
│           ├─ Clickable!                             │                  │
│           └─ Show status ✓/✏️/✗ when edited        │ Nội dung:        │
│                                                      │ "CÔNG TY TNHH"   │
│  Thành phố: [TP HCM] 🟡  ← Another error            │                  │
│           ├─ Clickable!                             │ Ngữ cảnh:        │
│           └─ If accepted → show ✓                   │ "...CÔNG TY...   │
│                                                      │ là nhà cung..."  │
│  [Document content...]                              │                  │
│                                                      │ 💡 Đề xuất:      │
│                                                      │ "Công ty TNHH"  │
│                                                      │                  │
│ Tổng: 5 lỗi                                         │ 📚 Viện dẫn:     │
│ 🔴 2, 🟡 2, 🔵 1                                    │ ⚖️ Quy định...   │
├──────────────────────────────────────────────────────┤ Vị trí: Phần 1   │
│ 🟢 Lỗi  🟡 Cảnh báo  🔵 Thông tin           │ Legend │ Excerpt: ...     │
└──────────────────────────────────────────────────────┤                  │
                                                       │ ⚙️ Xử lý lỗi      │
                                                       │                  │
                                                       │ [✓ Chấp nhận]    │
                                                       │ [✏️ Sửa]         │
                                                       │ [✗ Bỏ qua]       │
                                                       │                  │
                                                       └──────────────────┘

✨ NEW: Full inline error handling
   - Click → See details + buttons
   - Accept/Edit/Reject → Instant feedback
   - No tab switching needed!
```

---

## Error Status Indicators

### In Preview Document

#### Pending (No action taken)
```
Công ty: [CÔNG TY TNHH] 🔴
          │
         └─ Red highlight + severity icon
            Click to handle
```

#### Accepted (User clicked ✓)
```
Công ty: [CÔNG TY TNHH] ✓
         │
         └─ Green highlight + ✓ icon
            Status: "✓ Đã chấp nhận"
            Ready to apply
```

#### Edited (User custom edited)
```
Công ty: [CÔNG TY ABC] ✏️
         │
         └─ Blue highlight + ✏️ icon
            Status: "✏️ Đã chỉnh sửa"
            Will apply custom value
```

#### Rejected (User clicked ✗)
```
Công ty: ~~CÔNG TY TNHH~~ ✗
         │
         └─ Gray strikethrough + ✗ icon
            Status: "✗ Bỏ qua"
            NOT applied to document
```

---

## Error Detail Panel - State Changes

### State 1: Error Selected (No Action Yet)

```
┌────────────────────────────────────────────┐
│ 📋 Chi tiết lỗi                            │
├────────────────────────────────────────────┤
│                                             │
│ 🔴 Mức độ: Lỗi                            │
│ 📌 Loại: Company Name                      │
│ 📝 Mô tả: Tên công ty không tuân thủ...   │
│ 🔍 Nội dung: "CÔNG TY TNHH"               │
│ 📖 Ngữ cảnh: "...CÔNG TY TNHH là..."      │
│                                             │
│ 💡 Đề xuất: "Công ty TNHH"               │
│ 📚 Viện dẫn: ⚖️ Quy định...              │
│                                             │
├────────────────────────────────────────────┤
│ ⚙️ Xử lý lỗi                               │
│                                             │
│ ┌──────────────┬────────────────────────┐  │
│ │ ✓ Chấp nhận  │  ✏️ Sửa thủ công      │  │
│ └──────────────┴────────────────────────┘  │
│ ┌──────────────────────────────────────┐   │
│ │ ✗ Bỏ qua lỗi này                    │   │
│ └──────────────────────────────────────┘   │
│                                             │
└────────────────────────────────────────────┘
```

---

### State 2: Accept Selected

```
┌────────────────────────────────────────────┐
│ 📋 Chi tiết lỗi                            │
├────────────────────────────────────────────┤
│                                             │
│ [Details same as above...]                 │
│                                             │
├────────────────────────────────────────────┤
│ ⚙️ Xử lý lỗi                               │
│                                             │
│ ┌──────────────────────────────────────┐   │
│ │ ✓ Đã chấp nhận đề xuất               │   │ ← Green status
│ └──────────────────────────────────────┘   │
│                                             │
│ ┌──────────────┬────────────────────────┐  │
│ │ ✓ Chấp nhận  │  ✏️ Sửa                │  │
│ │ (disabled)   │                        │  │
│ └──────────────┴────────────────────────┘  │
│ ┌──────────────────────────────────────┐   │
│ │ ✗ Bỏ qua (disabled)                  │   │
│ └──────────────────────────────────────┘   │
│                                             │
└────────────────────────────────────────────┘
```

---

### State 3: Edit Mode

```
┌────────────────────────────────────────────┐
│ 📋 Chi tiết lỗi                            │
├────────────────────────────────────────────┤
│                                             │
│ [Details same as above...]                 │
│                                             │
├────────────────────────────────────────────┤
│ ⚙️ Xử lý lỗi                               │
│                                             │
│ ┌──────────────────────────────────────┐   │
│ │ ✏️ Sửa thủ công:                     │   │
│ ├──────────────────────────────────────┤   │
│ │ ┌──────────────────────────────────┐ │   │
│ │ │ Công ty TNHH ABC XYZ             │ │   │ ← Editable textarea
│ │ │                                  │ │   │
│ │ └──────────────────────────────────┘ │   │
│ ├──────────────────────────────────────┤   │
│ │ ┌─────────────────┬────────────────┐ │   │
│ │ │ 💾 Lưu sửa      │  ✕ Hủy        │ │   │
│ │ └─────────────────┴────────────────┘ │   │
│ └──────────────────────────────────────┘   │
│                                             │
└────────────────────────────────────────────┘
```

---

### State 4: Edit Saved

```
┌────────────────────────────────────────────┐
│ 📋 Chi tiết lỗi                            │
├────────────────────────────────────────────┤
│                                             │
│ [Details same...]                           │
│                                             │
├────────────────────────────────────────────┤
│ ⚙️ Xử lý lỗi                               │
│                                             │
│ ┌──────────────────────────────────────┐   │
│ │ ✏️ Đã chỉnh sửa thủ công             │   │ ← Blue status
│ └──────────────────────────────────────┘   │
│                                             │
│ ┌──────────────┬────────────────────────┐  │
│ │ ✓ Chấp nhận  │  ✏️ Sửa                │  │
│ │              │                        │  │
│ └──────────────┴────────────────────────┘  │
│ ┌──────────────────────────────────────┐   │
│ │ ✗ Bỏ qua (disabled)                  │   │
│ └──────────────────────────────────────┘   │
│                                             │
└────────────────────────────────────────────┘

💬 Note: User can still click "✓ Chấp nhận" to use suggestion
   or "✏️ Sửa" to edit the saved value
```

---

### State 5: Error Rejected

```
┌────────────────────────────────────────────┐
│ 📋 Chi tiết lỗi                            │
├────────────────────────────────────────────┤
│                                             │
│ [Details same...]                           │
│                                             │
├────────────────────────────────────────────┤
│ ⚙️ Xử lý lỗi                               │
│                                             │
│ ┌──────────────────────────────────────┐   │
│ │ ✗ Bỏ qua lỗi này                    │   │ ← Red status
│ └──────────────────────────────────────┘   │
│                                             │
│ ┌──────────────┬────────────────────────┐  │
│ │ ✓ Chấp nhận  │  ✏️ Sửa                │  │
│ │ (disabled)   │ (disabled)             │  │
│ └──────────────┴────────────────────────┘  │
│ ┌──────────────────────────────────────┐   │
│ │ ✗ Bỏ qua (disabled)                  │   │
│ └──────────────────────────────────────┘   │
│                                             │
└────────────────────────────────────────────┘

💬 Note: Original content NOT changed in document
```

---

## Color Palette

### Status Colors

| Status | Color | Hex | Use Case |
|--------|-------|-----|----------|
| Accept | Green | #27ae60 | Accepted suggestions |
| Edit | Blue | #3498db | Custom edits |
| Reject | Gray | #95a5a6 | False positives |
| Error | Red | #e74c3c | Severity: error |
| Warning | Orange | #f39c12 | Severity: warning |
| Info | Cyan | #3498db | Severity: info |

---

## Responsive Layouts

### Desktop (> 1200px)
```
┌────────────────────────────────────────────┬─────────────────┐
│ Preview                                    │ Details Panel   │
│ 70%                                        │ 30%             │
└────────────────────────────────────────────┴─────────────────┘
```

### Tablet (768px - 1200px)
```
┌──────────────────────────────────────────────┐
│ Preview                                      │
│ ~60%                                         │
├──────────────────────────────────────────────┤
│ Details Panel                                │
│ ~40%                                         │
└──────────────────────────────────────────────┘
```

### Mobile (< 768px)
```
┌──────────────────┐
│ Preview (scroll) │
│                  │
├──────────────────┤
│ Details (scroll) │
│                  │
└──────────────────┘
```

---

## Button States

### Accept Button

```
DEFAULT:
[✓ Chấp nhận đề xuất]
  - Enabled
  - Green background #27ae60
  - White text
  - Hover: darker green

AFTER CLICKED:
[✓ Chấp nhận đề xuất]
  - Disabled (opacity: 0.5)
  - Gray background
  - Can't click again
```

### Edit Button

```
DEFAULT:
[✏️ Sửa thủ công]
  - Enabled
  - Blue background #3498db
  - White text
  - Hover: darker blue

WHEN EDITING:
Textarea shown, button disappears

AFTER SAVED:
[✏️ Sửa thủ công]
  - Enabled again
  - Can edit again if needed
```

### Reject Button

```
DEFAULT:
[✗ Bỏ qua lỗi này]
  - Enabled
  - Red background #e74c3c
  - White text
  - Full width
  - Hover: darker red

AFTER CLICKED:
[✗ Bỏ qua lỗi này]
  - Disabled (opacity: 0.5)
  - Gray background
  - Can't click again
```

---

## Animation Effects

### Highlight Color Changes
```
Pending → Green:  transition: all 0.2s
Pending → Blue:   transition: all 0.2s
Pending → Gray:   transition: all 0.2s
```

### Button Hover Effects
```
Box-shadow: 0 2px 6px rgba(color, 0.3)
Scale:      1.02 (subtle)
```

### Status Indicator Animation
```
Fade-in when status changes: transition: all 0.3s
```

---

## Keyboard Navigation (Future)

```
Tab           → Next error
Shift+Tab     → Previous error
Enter         → Select error
A             → Accept
E             → Edit
R             → Reject
S             → Save edit
Escape        → Cancel edit
```

---

**This visual guide shows the before/after and all interactive states!**

**Version**: 0.2.1  
**Date**: April 8, 2026  
**Status**: ✅ Ready for visual testing
