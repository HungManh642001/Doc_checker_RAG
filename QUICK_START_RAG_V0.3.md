# 🚀 Quick Start - RAG-Based Document Analysis

## What's New in v0.3.0

This version implements a **Retrieval-Augmented Generation (RAG)** architecture for intelligent document analysis:

✅ **Knowledge Base** - Regulations from Phụ lục II, III, V pre-loaded  
✅ **Smart Analysis** - Pattern matching against regulatory rules  
✅ **Detailed Errors** - Each error shows type, reasoning, and references  
✅ **Enhanced UI** - Expandable error details with regulation quotes  

---

## ⚡ Get Started in 2 Minutes

### 1. Generate Test Documents

```bash
cd d:\Workspace\VTX\Doc_checker

# Generate test files with real errors
python create_samples.py
```

**Output**: Creates 3 sample documents in `samples/` folder:
- `sample_main.docx` - Contract with unit notation errors
- `sample_regulation.docx` - Regulatory references
- `sample_reference.docx` - Standard templates

### 2. Start the Application

```bash
# Windows
start_all.bat

# macOS/Linux
bash start_all.sh
```

**Wait for**: Both backend and frontend to be running
- Backend: http://localhost:5000
- Frontend: http://localhost:3000

### 3. Test the RAG System

**a) Upload Document**
- Click **Upload** button
- Select `samples/sample_main.docx` as main document
- Optional: Add regulations for enhanced analysis
- Click **Upload**

**b) View Analysis Results**
- System automatically analyzes the document
- Shows **7 errors** detected via RAG analysis
- See summary: 4 Errors 🔴, 2 Warnings 🟡

**c) Explore Errors**
```
For each error:
1. See original problematic text (e.g., "Mpa")
2. List of specific issues found (e.g., "vi_pham_ky_hieu_don_vi")
3. Click "Chi tiết" to expand details
4. View regulation references (Phụ lục II, V)
5. See suggestion (e.g., "Sửa thành: MPa")
```

**d) Edit & Correct**
- Check the checkbox next to error
- Click pencil (✏️) to edit suggestion
- Click "Chấp nhận" to apply all selected corrections
- Download corrected document

**e) Re-Analyze (Optional)**
```
After manual edits:
1. Click "Tái Thẩm Định" button
2. System re-analyzes the document
3. New error count displayed
4. Repeat until all issues resolved
```

---

## 📋 Expected Errors in Test Document

When you upload `sample_main.docx`, you should see these errors:

### Error: "Mpa" → "MPa"
- **Issue**: Ký hiệu đơn vị sai
- **Reason**: "M" (mega) + "Pa" (pascal) = "MPa" not "Mpa"
- **Reference**: Phụ lục II
- **Suggestion**: Sửa thành: MPa

### Error: "0.3 - 0.9" → "0,3 - 0,9"
- **Issue**: Dấu thập phân sai
- **Reason**: Dùng dấu (.) thay vì dấu (,)
- **Reference**: Phụ lục V
- **Suggestion**: Sửa thành: 0,3 - 0,9

### Error: Thiếu đơn vị đo
- **Issue**: Ranges như "3 - 9" không có đơn vị
- **Reason**: Phải ghi "3 - 9 mm" hoặc "3 - 9 bar"
- **Reference**: Phụ lục V
- **Suggestion**: Thêm mm, bar, v.v.

---

## 🎯 Understanding the NEW Error Display

### Old Format (v0.2)
```
Lỗi #1: Định dạng không nhất quán
Nội dung lỗi: CÔNG TY TNHH
Đề xuất: Công ty
```

### New Format (v0.3 - RAG)
```
📌 Nội dung gốc:
   Mpa

🔴 Danh sách lỗi phát hiện:
   [Ký hiệu đơn vị sai]
   Giải thích: Ký hiệu đơn vị pascal phải là "Pa" không phải "pa"
   
   [Ký hiệu không tiêu chuẩn]  
   Giải thích: Ký hiệu đơn vị phải tuân thủ chuẩn quốc tế

💡 Đề xuất sửa chữa:
   Sửa thành: MPa

📖 Tham chiếu quy định:
   Phụ lục II - Thiết lập bội thập phân, ước thập phân của đơn vị đo
   Tên, ký hiệu của tiền tố và thừa số quy đổi: mega (M), 10^6
```

---

## 🧪 Verify RAG System Works

### Option 1: Quick Python Test
```bash
cd d:\Workspace\VTX\Doc_checker
.\.venv\Scripts\python.exe test_rag.py
```

**Expected Output**:
```
✓ Extracted 16 paragraphs
✓ Analysis complete: 7 issues found

📋 ERROR #1
Original Text: Mpa
Issues Found (2):
  1. vi_pham_ky_hieu_don_vi
  2. vi_pham_ky_hieu_don_vi_khac
```

### Option 2: Full Application Test
1. Start application (`start_all.bat`)
2. Upload `samples/sample_main.docx`
3. See 7 errors displayed in UI
4. Expand one error and verify:
   - ✅ Original text shows: "Mpa"
   - ✅ Multiple error types listed
   - ✅ Reasoning provided
   - ✅ Reference to regulations shown
   - ✅ Suggestion available for editing

---

## 🔍 Key Features to Try

### 1. Error Expansion
- Click "▶ Chi tiết" to expand error details
- Shows full regulation references and quotes
- Verify multi-level error information

### 2. Inline Editing
- Next to suggestion, click ✏️ button
- Edit the proposed correction
- Click ✓ Lưu to save your change
- Now when you accept, it uses your custom value

### 3. Error Selection
- Check boxes to select multiple errors
- Button shows "Chấp nhận 3 đề xuất" with count
- Apply only selected corrections

### 4. Severity Filtering
- Use dropdown to filter by severity level
- ERROR (🔴): 4 in test doc
- WARNING (🟡): 2 in test doc  
- INFO (ℹ️): None in test doc

### 5. Re-Analysis
- After accepting corrections
- Make manual edits to document (if needed)
- Click 🔁 "Tái Thẩm Định"
- System re-analyzes and shows new error count

---

## 📊 RAG Architecture at a Glance

```
Your Document
    ↓
[Extract Text] → Paragraphs & Tables
    ↓
[RAG Knowledge Base] ← Phụ lục II, III, V
    ↓
[Pattern Matching] → Find regulation violations
    ↓
[Error Generation] → Create detailed error objects
    ↓
[Display with UI] → Expandable error cards
    ↓
[User Action] → Accept/Edit/Reject
    ↓
[Apply Corrections] → Update DOCX file
```

---

## 💡 Tips & Tricks

### Debugging Tips
1. **Check error was detected**: Look for original text in error card
2. **Verify rule matched**: See error type name (starts with error_ in id)
3. **Check reference**: Phụ lục II/III/V should be mentioned
4. **Validate suggestion**: Should be different from original text

### Performance
- Analysis runs in <1 second for test document
- UI renders 7 errors instantly
- No network latency (all in browser/backend)

### Common Issues
| Issue | Solution |
|-------|----------|
| "No errors detected" | Verify sample_main.docx in samples/ folder |
| Errors not showing suggestions | Refresh page (Ctrl+R) |
| Can't expand error details | Click "▶" chevron not the error line |
| Re-analyze button missing | Ensure you're on Review page |

---

## 🎓 Understanding the Errors

### Mpa → MPa (Unit Notation)
```
❌ Before: "Mpa" (wrong case for pascal)
✅ After:  "MPa" (M=mega, Pa=pascal)

Quy định (Phụ lục II):
"Tiền tố 'mega' được ký hiệu là 'M', 
 đơn vị 'pascal' được ký hiệu là 'Pa'"
```

### 0.3 → 0,3 (Decimal Point)
```
❌ Before: "0.3" (using dot like English)
✅ After:  "0,3" (using comma like Vietnamese)

Quy định (Phụ lục V):
"Biểu thị dấu thập phân phải sử dụng dấu phẩy (,)
 không sử dụng dấu chấm (.)"
```

### Missing Units
```
❌ Before: "3 - 9" (no unit)
✅ After:  "3 - 9 mm" or "3 - 9 bar"

Quy định (Phụ lục V):
"Giá trị đại lượng đo phải kèm theo đơn vị đo cụ thể"
```

---

## 📞 Support

### Files to Reference
- **Architecture**: `RAG_IMPLEMENTATION.md` (detailed technical docs)
- **Summary**: `RAG_IMPLEMENTATION_SUMMARY.md` (full overview)
- **Test Verification**: Run `test_rag.py` to see raw error output
- **Code**: `backend/app/ai_simulator.py` (RAG logic)

### System Status
- ✅ Backend: Fully functional
- ✅ Frontend: All components ready
- ✅ Test Data: Sample documents generated
- ✅ Testing: System verified working

---

## 🎉 Next Steps

1. **Start Application**: `start_all.bat`
2. **Upload Sample**: Select `samples/sample_main.docx`
3. **Review Errors**: See 7 detailed errors with references
4. **Edit Suggestions**: Customize corrections as needed
5. **Apply Changes**: Download corrected document
6. **Re-Analyze**: Verify all issues resolved

**Enjoy the new RAG-powered document analysis!** 🚀

---

**Version**: 0.3.0  
**Status**: Ready to Use  
**Last Updated**: April 9, 2026
