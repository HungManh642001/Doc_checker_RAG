# RAG_INTEGRATION_GUIDE.md

## 🚀 Hướng Dẫn Tích Hợp RAG System

Hướng dẫn chi tiết để tích hợp RAG system từ Doc_checker_RAG vào Doc_checker app, chỉ giữ lại giao diện thắm định lỗi (ErrorViewer).

### 📋 Yêu Cầu

**Các thành phần cần có:**
- ✅ Doc_checker project (đã có)
- ✅ Doc_checker_RAG project (hệ thống RAG của bạn)
- ✅ Ollama running với models:
  - `qwen3:4b` (LLM để phân tích)
  - `nomic-embed-text` (Embedding model)
- ✅ Qdrant vector store

**Cấu trúc folder hiện tại:**
```
d:\Workspace\VTX\
├── Doc_checker/              ← Main app
│   ├── backend/
│   │   ├── app/
│   │   │   ├── __init__.py (update)
│   │   │   ├── api_simplified.py (new) ← Simplified API
│   │   │   ├── rag_analyzer.py (new) ← RAG adapter
│   │   │   └── ...
│   │   └── ...
│   ├── frontend/
│   │   ├── src/
│   │   │   ├── AppSimplified.js (new) ← Thay App.js
│   │   │   ├── AppSimplified.css (new)
│   │   │   ├── components/
│   │   │   │   ├── DocumentUploadSimplified.js (new)
│   │   │   │   ├── DocumentUploadSimplified.css (new)
│   │   │   │   └── ErrorViewer.js (keep)
│   │   │   └── ...
│   │   └── ...
│   └── setup-rag.md (new)
│
└── Doc_checker_RAG/          ← RAG system (keep as-is)
    └── src/
        ├── audit_logic/
        ├── knowledge_base/
        ├── document_processing/
        ├── data/
        ├── config.py
        └── main.py
```

---

### 🔧 Bước 1: Kiểm Tra Config RAG

Đảm bảo `Doc_checker_RAG/src/config.py` có các thiết lập đúng:

```python
MODEL = "qwen3:4b"                    # ← Model cho AI analysis
EMBEDDING_MODEL = "nomic-embed-text"  # ← Model cho embeddings
OLLAMA_URL = "http://127.0.0.1:11434"  # ← Ollama server
REQUEST_TIMEOUT = 600.0
CONTEXT_WINDOW = 8192
NUM_CTX = 10240
```

**Kiểm tra:**
```bash
# Verify Ollama is running
curl http://127.0.0.1:11434/api/tags

# Output should show available models
# như: qwen3:4b, nomic-embed-text
```

---

### 🔧 Bước 2: Cài Dependencies cho Backend

```bash
cd Doc_checker/backend

# Cài dependencies cơ bản
pip install -r requirements.txt

# Cài thêm dependencies cho RAG
pip install llama-index qdrant-client python-docx html2text

# Kiểm tra:
python -c "from app.rag_analyzer import RAGAnalyzer; print('✓ OK')"
```

**requirements.txt cho RAG:**
```
Flask==2.3.0
flask-cors==4.0.0
python-docx==0.8.11
html2text==2024.2.26
llama-index==0.9.0
llama-index-vector-stores-qdrant==0.1.0
llama-index-embeddings-ollama==0.1.0
llama-index-llms-ollama==0.1.0
qdrant-client==2.7.0
```

---

### 🔧 Bước 3: Update Flask App

**Hãy tạo file mới hoặc update `backend/app/__init__.py`:**

Có 2 cách setup:

#### **Option A: Chỉ dùng Simplified API (Khuyên dùng)**

```python
# backend/app/__init__.py
from flask import Flask
from flask_cors import CORS
import os

def create_app():
    app = Flask(__name__)
    CORS(app)
    
    # Configuration
    app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024
    app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), '..', 'uploads')
    
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Register simplified RAG API
    from app.api_simplified import api_bp
    app.register_blueprint(api_bp)
    
    return app
```

#### **Option B: Dùng cả 2 API (Legacy + RAG)**

```python
# backend/app/__init__.py
from flask import Flask
from flask_cors import CORS
import os

def create_app():
    app = Flask(__name__)
    CORS(app)
    
    app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024
    app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), '..', 'uploads')
    
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Register both APIs
    from app.api import api_bp as api_legacy_bp
    from app.api_simplified import api_bp as api_rag_bp
    
    app.register_blueprint(api_legacy_bp)  # Old: /api/upload, /api/analyze, etc
    app.register_blueprint(api_rag_bp)     # New: /api/upload (simplified)
    
    return app
```

**Chọn Option A nếu chỉ dùng RAG** (gọn gàng hơn)

---

### 🔧 Bước 4: Update Frontend

**Chọn một trong hai:**

#### **Option A: Thay toàn bộ App (Khuyên dùng)**

```bash
# Backup old app
mv frontend/src/App.js frontend/src/App.js.bak
mv frontend/src/App.css frontend/src/App.css.bak

# Copy simplified version
cp frontend/src/AppSimplified.js frontend/src/App.js
cp frontend/src/AppSimplified.css frontend/src/App.css
```

#### **Option B: Giữ cả hai apps**

Để có app cũ và app RAG mới cùng lúc:

```bash
# Keep old App.js as App-legacy.js
mv frontend/src/App.js frontend/src/App-legacy.js

# Use RAG app as the new default
cp frontend/src/AppSimplified.js frontend/src/App.js
cp frontend/src/AppSimplified.css frontend/src/App.css
```

---

### 🚀 Bước 5: Chạy Ứng Dụng

**Cửa sổ Terminal 1 - Ollama:**
```bash
# Đảm bảo Ollama đang chạy
ollama serve

# Hoặc nếu đã chạy rồi, bỏ qua bước này
```

**Cửa sổ Terminal 2 - Backend:**
```bash
cd Doc_checker/backend

# Chạy Flask server
python run.py

# Output:
# WARNING in __main__: This is a development server...
# Running on http://127.0.0.1:5000
```

**Cửa sổ Terminal 3 - Frontend:**
```bash
cd Doc_checker/frontend

# Chạy React
npm start

# Output:
# Compiled successfully!
# You can now view App in the browser at: http://localhost:3000
```

---

### 📤 Bước 6: Test Upload

**1. Chuẩn bị file test:**

Bạn cần:
- ✅ **Tài liệu cần thẩm định** (DOCX)
  - Ví dụ: `sample_main.docx`
  - Có các lỗi để phát hiện

- ✅ **Tài liệu sở cứ** (DOCX - tùy chọn nhưng khuyên dùng)
  - Ví dụ: `reference_standards.docx`
  - Chứa các tiêu chuẩn/quy định

- ✅ **Tài liệu quy định** (DOCX - tùy chọn)
  - Ví dụ: `regulations.docx`
  - Chứa các quy tắc kiểm tra

**2. Mở app:**
```
http://localhost:3000
```

**3. Upload:**
- Kéo/thả hoặc click để chọn **Tài liệu cần thẩm định**
- Thêm **Tài liệu sở cứ** (optional)
- Thêm **Quy định** (optional)
- Click **"🚀 Bắt Đầu Thẩm Định"**

**4. Xem kết quả:**
- Hệ thống sẽ hiển thị lỗi phát hiện
- Mỗi lỗi hiển thị:
  - ✓ Text bị lỗi
  - ✓ Chi tiết lỗi
  - ✓ Đề xuất sửa chữa
  - ✓ Tham chiếu quy định

---

### ✅ Kiểm Tra Hoạt Động

#### **Test 1: Check API**
```bash
# Kiểm tra backend health
curl http://127.0.0.1:5000/api/health

# Output nếu OK:
# {"status":"ok","sessions":0}
```

#### **Test 2: Test RAG Analyzer**
```python
# backend/test_rag_manual.py
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.rag_analyzer import RAGAnalyzer

analyzer = RAGAnalyzer()

# Mock reference docs path
ref_docs = [r"D:\Workspace\VTX\Doc_checker_RAG\data\reference_documents\..."]

# Try initialize
success = analyzer.initialize_rag_system(ref_docs)
print(f"Initialize: {'✓ OK' if success else '✗ FAILED'}")

# Try analyze (if file exists)
test_file = r"D:\Workspace\VTX\Doc_checker_RAG\data\input_documents\Mẫu YCKT đầu vào_1.html"
if Path(test_file).exists():
    errors = analyzer.analyze_document(test_file)
    print(f"Analysis: Found {len(errors)} errors")
    if errors:
        print(errors[0])  # Show first error
```

#### **Test 3: Browser Console**
```bash
# F12 trong browser → Console
# Xem logs của React app
# Kiểm tra API calls trong Network tab
```

---

### 🐛 Troubleshooting

| Vấn Đề | Giải Pháp |
|--------|----------|
| `ImportError: RAGAnalyzer` | Đảm bảo `rag_analyzer.py` được lưu đúng vị trí |
| `Path D:\Workspace\VTX\Doc_checker_RAG not found` | Update đường dẫn trong `rag_analyzer.py` (line ~13) |
| `Ollama connection error` | Kiểm tra: `ollama serve` đang chạy |
| `Model qwen3:4b not found` | Cài: `ollama pull qwen3:4b` |
| `Embedding model not found` | Cài: `ollama pull nomic-embed-text` |
| `Qdrant connection failed` | Ollama sẽ tự startup Qdrant, kiểm tra logs Ollama |
| `DOCX to HTML conversion error` | Đảm bảo file DOCX không bị corrupt |
| `Analysis timeout (>600s)` | Tài liệu quá lớn hoặc Ollama quá chậm |

---

### 🎯 Luồng Hoạt Động

```
┌─────────────────────────────────────┐
│ User Upload Documents               │
│ - Main DOCX                         │
│ - References DOCX (optional)        │
│ - Rules DOCX (optional)             │
└────────────┬────────────────────────┘
             │
             ↓
┌─────────────────────────────────────┐
│ Backend: POST /api/upload           │
│ - Save files to uploads/            │
│ - Initialize RAG system             │
└────────────┬────────────────────────┘
             │
             ↓
┌─────────────────────────────────────┐
│ RAG Analyzer:                       │
│ 1. Convert DOCX → HTML              │
│ 2. Build Qdrant index from refs     │
│ 3. Chunk main document              │
│ 4. Query Ollama for analysis        │
│ 5. Transform results                │
└────────────┬────────────────────────┘
             │
             ↓
┌─────────────────────────────────────┐
│ Return errors to frontend:          │
│ {                                   │
│   errors: [                         │
│     {                               │
│       original_text: "...",         │
│       danh_sach_cac_loi: [...],     │
│       suggestion: "...",            │
│       reference_location: "...",    │
│       severity: "error"             │
│     }                               │
│   ]                                 │
│ }                                   │
└────────────┬────────────────────────┘
             │
             ↓
┌─────────────────────────────────────┐
│ Frontend: ErrorViewer Component     │
│ - Show errors hierarchically        │
│ - User accepts/rejects/edits        │
│ - Submit suggestions back           │
└─────────────────────────────────────┘
```

---

### 📝 API Endpoints

#### **Simplified RAG API** (`/api`)

```
POST /api/upload
  Input: multipart/form-data
    - mainDocument (DOCX) *
    - referenceDocuments (DOCX) []
    - ruleDocuments (DOCX) []
  Output: {
    sessionId: "uuid",
    results: {
      errorCount: 5,
      errors: [...]
    }
  }
    
GET /api/session/<session_id>
  Output: { sessionId, results: { errorCount, errors } }

POST /api/session/<session_id>/apply-suggestions
  Input: {
    updates: [
      { errorId, action: 'accept'|'reject'|'custom', customSuggestion }
    ]
  }
  Output: { success: true, message, acceptedCount }

DELETE /api/session/<session_id>/cleanup
  Output: { success: true, message }

GET /api/health
  Output: { status: 'ok', sessions: 0 }
```

---

### 🎨 Giao Diện

**Màn hình Upload:**
- ✅ Upload tài liệu cần thẩm định
- ✅ Thêm tài liệu sở cứ (optional)
- ✅ Thêm quy định (optional)
- ✅ Button "Bắt Đầu Thẩm Định"

**Màn hình Kết Quả:**
- ✅ Hiển thị số lỗi phát hiện
- ✅ Liệt kê từng lỗi với chi tiết
- ✅ Mỗi lỗi có nút Accept/Reject/Edit
- ✅ Button "Ghi Lại Sửa Chữa"
- ✅ Button "Thẩm Định Tài Liệu Khác"

---

### 📚 File Tham Khảo

| File | Mục Đích |
|------|---------|
| `backend/app/rag_analyzer.py` | RAG adapter |
| `backend/app/api_simplified.py` | Simplified API endpoints |
| `frontend/src/AppSimplified.js` | Simplified React app |
| `frontend/src/AppSimplified.css` | Styling |
| `frontend/src/components/DocumentUploadSimplified.js` | Upload component |
| `frontend/src/components/DocumentUploadSimplified.css` | Upload styling |
| `frontend/src/components/ErrorViewer.js` | Error display (reused) |

---

### 🚀 Tiếp Theo

Sau khi RAG integration hoạt động:

1. **Tối ưu Prompts**: Điều chỉnh prompts trong `audit_engine.py` để cải thiện độ chính xác
2. **Caching**: Thêm caching cho embeddings để tăng tốc độ
3. **Batch Processing**: Xử lý nhiều tài liệu song song
4. **Monitoring**: Thêm logging/monitoring cho production
5. **Alternative Models**: Thử models khác (LLaMA, Mistral, etc)

---

### ❓ FAQ

**Q: Tại sao phải chuyển từ pattern-matching sang RAG?**
A: RAG hiểu context tốt hơn, không phải hard-code patterns, tự adapt với quy định mới.

**Q: Có thể dùng offline không?**
A: Có! Ollama + Qdrant đều chạy locally, không cần internet sau khi download models.

**Q: File lớn thì sao?**
A: Chunking tự động, từng chunk analyze riêng, sau đó combine kết quả.

**Q: Bao lâu thì hoàn thành 1 tài liệu?**
A: Trung bình 2-5 phút tùy độ lớn tài liệu và tốc độ Ollama.

**Q: Có thể dùng GPT/Claude thay Ollama không?**
A: Có! Update `config.py` + `rag_analyzer.py` để gọi API ngoài.

---

### 📞 Support

Nếu gặp vấn đề:

1. Check logs backend: `python run.py` (xem error messages)
2. Check browser console: F12 → Console
3. Check Ollama logs: Terminal chạy Ollama
4. Check path config: Đường dẫn Doc_checker_RAG đúng chưa?

