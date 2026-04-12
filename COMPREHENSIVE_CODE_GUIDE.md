# 📚 Hướng Dẫn Chi Tiết Kiến Trúc Code & Tích Hợp AI Thực Tế

## Table of Contents
1. [Kiến Trúc Tổng Quan](#kiến-trúc-tổng-quan)
2. [Backend - Cấu Trúc Chi Tiết](#backend---cấu-trúc-chi-tiết)
3. [Frontend - Cấu Trúc Chi Tiết](#frontend---cấu-trúc-chi-tiết)
4. [Flow Dữ Liệu](#flow-dữ-liệu)
5. [Hướng Dẫn Tích Hợp AI Thực Tế](#hướng-dẫn-tích-hợp-ai-thực-tế)
6. [Ví Dụ Code Thực Tế](#ví-dụ-code-thực-tế)

---

## Kiến Trúc Tổng Quan

### Sơ Đồ Kiến Trúc

```
┌─────────────────────────────────────────────────────────────┐
│                         FRONTEND (React)                     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  App.js      │  │   Upload     │  │   Preview    │      │
│  │  (Router)    │→ │ (Upload Doc) │→ │ (Show Doc)   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│         ↓                                    ↓               │
│         └────→ ┌──────────────┐ ←────────────┘              │
│                │ ErrorViewer  │                             │
│                │(Show Errors) │                             │
│                └──────────────┘                             │
│                                                              │
└─────────────────────────────────────────────────────────────┘
                          ↕️ (HTTP/JSON)
┌─────────────────────────────────────────────────────────────┐
│                      BACKEND (Python/Flask)                  │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  api.py      │→ │ document_    │→ │ ai_simulator │      │
│  │  (Routes)    │  │ processor.py │  │ (RAG Engine) │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                              ↓              │
│                                       [Knowledge Base]      │
│                                       [Phụ lục II, III, V] │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Thành Phần Chính

**Frontend**:
- `App.js` - Router chính, quản lý state
- `DocumentUpload.js` - Upload tài liệu
- `DocumentPreview.js` - Xem trước tài liệu
- `ErrorViewer.js` - Hiển thị lỗi chi tiết

**Backend**:
- `api.py` - API endpoints
- `document_processor.py` - Xử lý DOCX
- `ai_simulator.py` - RAG engine (cần upgrade)

---

## Backend - Cấu Trúc Chi Tiết

### 1. File: `backend/app/api.py`

**Mục đích**: Định nghĩa tất cả API endpoints

**Bộ Endpoints**:

```
POST   /api/upload
       ├─ Upload tài liệu chính, quy định, sở cứ
       ├─ Tạo session_id (UUID)
       └─ Lưu vào: uploads/{session_id}/

GET    /api/document/{session_id}
       ├─ Lấy nội dung tài liệu
       └─ Return: {paragraphs: [], tables: []}

GET    /api/references/{session_id}
       ├─ Lấy nội dung quy định & sở cứ
       └─ Return: {regulations: [], references: []}

POST   /api/analyze/{session_id}
       ├─ Gọi AISimulator.analyze_document()
       ├─ Tìm lỗi trong tài liệu
       └─ Return: {errors: [...]}

POST   /api/apply-suggestions/{session_id}
       ├─ Áp dụng sửa chữa vào DOCX
       ├─ Tạo file mới "main_corrected.docx"
       └─ Return: {downloadUrl: "..."}

POST   /api/save-and-reupload/{session_id}
       ├─ Áp dụng sửa chữa + re-analyze
       ├─ Phuc vụ "Tái Thẩm Định"
       └─ Return: {errors: [...], updateCount: ...}
```

**Chi Tiết: `POST /api/analyze/{session_id}`**

```python
@api_bp.route('/analyze/<session_id>', methods=['POST'])
def analyze_document(session_id):
    """
    Bước 1: Lấy đường dẫn tài liệu
    """
    upload_dir = os.path.join(..., 'uploads', session_id)
    main_path = os.path.join(upload_dir, 'main.docx')
    
    """
    Bước 2: Extract text từ DOCX
    """
    processor = DocumentProcessor()
    content = processor.extract_text_with_positions(main_path)
    # Return: {paragraphs: [...], tables: [...]}
    
    """
    Bước 3: Phân tích với AI
    """
    ai = AISimulator()
    errors = ai.analyze_document(content)
    # Return: [
    #   {
    #     "id": "error_0",
    #     "original_text": "Mpa",
    #     "danh_sach_cac_loi": [...],
    #     "suggestion": "MPa",
    #     ...
    #   }
    # ]
    
    """
    Bước 4: Return response
    """
    return jsonify({
        'sessionId': session_id,
        'errors': errors
    })
```

### 2. File: `backend/app/document_processor.py`

**Mục đích**: Xử lý file DOCX (đọc/ghi)

**Các Phương Thức Chính**:

```python
class DocumentProcessor:
    
    def extract_text_with_positions(file_path):
        """
        Lấy toàn bộ text từ DOCX theo position
        
        Return:
        {
            'paragraphs': [
                {
                    'id': 'para_0',
                    'text': 'HỢP ĐỒNG MUA BÁN HÀNG HÓA',
                    'type': 'heading'
                },
                ...
            ],
            'tables': [
                {
                    'id': 'table_0',
                    'rows': [
                        {
                            'cells': [
                                {
                                    'id': 'cell_0_0',
                                    'text': 'Mã hàng'
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        """
        
    def apply_corrections(input_path, output_path, corrections):
        """
        Áp dụng sửa chữa vào DOCX
        
        corrections = [
            {
                'elementId': 'para_7',
                'newText': 'MPa'
            }
        ]
        
        Tìm thành phần có id = elementId
        Thay đổi text
        Lưu vào output_path
        """
```

### 3. File: `backend/app/ai_simulator.py`

**Mục đích**: Phân tích tài liệu để tìm lỗi (hiện tại là pattern-based, sẽ upgrade lên AI)

**Cấu Trúc Hiện Tại**:

```python
class RAGKnowledgeBase:
    """Cơ sở dữ liệu quy định (simulated vector DB)"""
    
    def __init__(self):
        self.regulations = {
            'unit_notation': {
                'reference': 'Phụ lục II - ...',
                'rules': [
                    {
                        'type': 'vi_pham_ky_hieu_don_vi',
                        'pattern': r'\bMpa\b',
                        'description': 'Ký hiệu sai',
                        'quote': 'Quy định...'
                    }
                ]
            },
            'unit_display': {...},
            'unit_format': {...}
        }
    
    def query_regulations(self, text):
        """
        Tìm quy định áp dụng cho text
        
        Dùng regex pattern để match
        Return: [{
            'category': 'unit_notation',
            'rule_type': 'vi_pham_ky_hieu_don_vi',
            'matched_text': 'Mpa',
            'description': '...'
        }]
        """

class AISimulator:
    """Phân tích tài liệu (sẽ replace với AI thực)"""
    
    def analyze_document(self, content):
        """
        Chính là nơi cần integrate AI
        
        Input: content từ DocumentProcessor
        Output: array của errors
        
        Hiện tại:
        - Query knowledge base
        - Sử dụng pattern matching (regex)
        - Sinh ra error objects
        
        Sẽ thay thế bằng:
        - Gọi Claude/GPT API
        - Gửi các quy định làm context
        - Yêu cầu phân tích
        """
```

**Cấu Trúc Error Object**:

```python
error_object = {
    'id': 'error_0',                          # Unique ID
    'original_text': 'Mpa',                   # Text có lỗi
    'elementId': 'para_7',                    # Vị trí trong doc
    'elementType': 'paragraph',               # paragraph/table_cell
    'danh_sach_cac_loi': [                    # Array lỡi
        {
            'error_type': 'vi_pham_ky_hieu_don_vi',
            'reasoning': 'Ký hiệu đơn vị...',
            'reference': 'Phụ lục II - ...',
            'severity': 'error'
        },
        {
            'error_type': 'vi_pham_ky_hieu_don_vi_khac',
            'reasoning': 'Ký hiệu phải tuân...',
            'reference': 'Phụ lục II - ...',
            'severity': 'error'
        }
    ],
    'suggestion': 'Sửa thành: MPa',          # Đề xuất sửa
    'reference_location': 'Phụ lục II - ...', # Quy định áp dụng
    'reference_quote': 'Tiền tố mega...',     # Trích dẫn
    'severity': 'error'                       # error/warning/info
}
```

---

## Frontend - Cấu Trúc Chi Tiết

### 1. File: `frontend/src/App.js`

**Mục đích**: Router chính, quản lý state toàn ứng dụng

**State Management**:

```javascript
function App() {
    // Quản lý step hiện tại: upload → preview → review → complete
    const [step, setStep] = useState('upload');
    
    // Session ID (UUID từ backend)
    const [sessionId, setSessionId] = useState(null);
    
    // Nội dung tài liệu
    const [documentContent, setDocumentContent] = useState(null);
    
    // Danh sách lỗi
    const [errors, setErrors] = useState([]);
    
    // Trạng thái loading
    const [loading, setLoading] = useState(false);
    
    // Trạng thái từng lỗi (accept/edit/reject)
    const [errorStatus, setErrorStatus] = useState({
        'error_0': { status: 'accepted', value: 'MPa' },
        'error_1': { status: 'rejected' },
        'error_2': { status: 'edited', value: '0,3' }
    });
}
```

**Workflow State**:

```
┌─────────────────┐
│ 'upload'        │ ← Người dùng chọn file
│ (DocumentUpload)│
└────────┬────────┘
         ↓
┌─────────────────┐
│ 'preview'       │ ← Xem trước tài liệu + hiển thị lỗi
│ (DocumentPreview│
│  + ErrorViewer) │
└────────┬────────┘
         ↓
┌─────────────────┐
│ 'review'        │ ← Chọn lỗi để sửa
│ (ErrorViewer)   │
└────────┬────────┘
         ↓
┌─────────────────┐
│ 'complete'      │ ← Tải file đã sửa
│ (Success screen)│
└─────────────────┘
```

**API Calls Flow**:

```javascript
// 1. Upload
handleUploadComplete(sessionId)
  → POST /api/upload
  → setStep('preview')

// 2. Load document
useEffect(() => {
    if (step === 'preview') {
        fetch(`/api/document/${sessionId}`)
        → get content
        → setDocumentContent()
    }
})

// 3. Analyze
useEffect(() => {
    if (documentContent) {
        fetch(`/api/analyze/${sessionId}`, {method: 'POST'})
        → get errors
        → setErrors()
        → setStep('review')
    }
})

// 4. Apply suggestions
handleApplySuggestions()
  → filter by errorStatus
  → POST /api/apply-suggestions
  → download file
  → setStep('complete')
```

### 2. File: `frontend/src/components/DocumentUpload.js`

**Mục đích**: Cho người dùng upload tài liệu

**Chức Năng**:

```javascript
function DocumentUpload({ onUploadComplete }) {
    // State
    const [mainDoc, setMainDoc] = useState(null);
    const [refDocs, setRefDocs] = useState([]);
    const [regulations, setRegulations] = useState([]);
    
    // Handle upload
    const handleUpload = async () => {
        const formData = new FormData();
        
        // Add files
        formData.append('mainDocument', mainDoc);
        refDocs.forEach(doc => 
            formData.append('referenceDocuments', doc)
        );
        regulations.forEach(reg => 
            formData.append('regulations', reg)
        );
        
        // POST to backend
        // backend sẽ:
        // 1. Tạo session_id
        // 2. Lưu vào uploads/{session_id}/
        // 3. Return session_id
        
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        onUploadComplete(data.sessionId);
    };
}
```

### 3. File: `frontend/src/components/DocumentPreview.js`

**Mục đích**: Xem trước tài liệu

**Hiển Thị**:
- Hiển thị paragraphs + tables từ content
- Highlight text có lỗi
- Double-click để sửa nội dung
- Tracking thay đổi qua contentUpdates state

**State**:

```javascript
const [contentUpdates, setContentUpdates] = useState({
    'para_7': {
        'error_0': 'MPa',           // Sửa từ error
        'manual': 'Custom value'    // Sửa thủ công
    }
});

// getDisplayText() - tính toán text hiển thị
// Priority: manual > error > original
const displayText = 
    contentUpdates['para_7']?.manual ||
    contentUpdates['para_7']?.['error_0'] ||
    originalText;
```

### 4. File: `frontend/src/components/ErrorViewer.js`

**Mục đích**: Hiển thị danh sách lỗi chi tiết

**Cấu Trúc**:

```javascript
function ErrorViewer({ errors, ... }) {
    // Filter state
    const [filterSeverity, setFilterSeverity] = useState('all');
    const [selectedErrors, setSelectedErrors] = useState(new Set());
    const [expandedErrorId, setExpandedErrorId] = useState(null);
    
    // Render
    return (
        <div className="error-viewer">
            {/* Header với stats */}
            <div className="stats">
                Total: {errors.length}
                Error: 4, Warning: 2
            </div>
            
            {/* Filters */}
            <select onChange={(e) => setFilterSeverity(e.target.value)}>
                <option>All</option>
                <option>Error</option>
                <option>Warning</option>
            </select>
            
            {/* Error list */}
            {errors.map(error => (
                <div className="error-item">
                    {/* Error header */}
                    Original: {error.original_text}
                    
                    {/* Error types */}
                    {error.danh_sach_cac_loi.map(err => (
                        <div>
                            {err.error_type}
                            {err.reasoning}
                        </div>
                    ))}
                    
                    {/* Expanded: suggestions + refs */}
                    {expandedErrorId === error.id && (
                        <>
                            <p>Suggestion: {error.suggestion}</p>
                            <p>Reference: {error.reference_location}</p>
                        </>
                    )}
                </div>
            ))}
            
            {/* Actions */}
            <button onClick={handleApplySuggestions}>
                Accept {selectedErrors.size} suggestions
            </button>
        </div>
    );
}
```

---

## Flow Dữ Liệu

### Scenario 1: Upload & Analyze

```
User selects file
        ↓
DocumentUpload.handleUpload()
        ↓
POST /api/upload
        ↓
Backend:
├─ Create session_id (UUID)
├─ Save to uploads/{session_id}/
└─ Return {sessionId: 'abc-123'}
        ↓
Frontend:
├─ setSessionId('abc-123')
├─ setStep('preview')
└─ Load document
        ↓
GET /api/document/{session_id}
        ↓
Backend:
├─ Load main.docx
├─ DocumentProcessor.extract_text_with_positions()
└─ Return {paragraphs: [...], tables: [...]}
        ↓
Frontend:
├─ setDocumentContent(data.content)
├─ Render DocumentPreview
└─ Trigger analysis
        ↓
POST /api/analyze/{session_id}
        ↓
Backend:
├─ Extract content lần nữa
├─ AISimulator.analyze_document(content)
├─ Find errors (RAG matching)
└─ Return {errors: [...]}
        ↓
Frontend:
├─ setErrors(data.errors)
├─ setStep('review')
└─ Render ErrorViewer
```

### Scenario 2: Accept & Download

```
User checks errors & clicks "Accept"
        ↓
Frontend:
├─ Get selected error IDs
├─ Filter by errorStatus (skip rejected)
└─ POST /api/apply-suggestions/{session_id}
        ↓
POST body:
{
    acceptedSuggestions: [
        {elementId: 'para_7', newText: 'MPa'},
        {elementId: 'para_8', newText: '0,3'}
    ]
}
        ↓
Backend:
├─ Load main.docx
├─ DocumentProcessor.apply_corrections()
├─ Save as main_corrected.docx
└─ Return {downloadUrl: '/download/...'}
        ↓
Frontend:
├─ window.location.href = downloadUrl
├─ User downloads file
└─ Show completion screen
```

### Scenario 3: Re-Analyze (Tái Thẩm Định)

```
User makes manual edits + clicks "Tái Thẩm Định"
        ↓
Frontend:
├─ Get contentUpdates from state
├─ Save to localStorage
└─ POST /api/save-and-reupload/{session_id}
        ↓
POST body:
{
    contentUpdates: {
        'para_7': {
            'error_0': 'MPa',
            'manual': 'Custom'
        }
    }
}
        ↓
Backend:
├─ Transform contentUpdates to corrections
├─ Load & apply corrections
├─ Re-extract content
├─ Re-analyze with AISimulator
├─ Save updated file
└─ Return {errors: [...], updateCount: 5}
        ↓
Frontend:
├─ setErrors(new_errors)
├─ Update state
└─ Re-render with new errors
```

---

## Hướng Dẫn Tích Hợp AI Thực Tế

### Phần 1: Hiểu Hiện Tại Hoạt Động

**Hiện tại** (`ai_simulator.py`):
- Dùng regex pattern matching
- Cứng không có AI
- Phù hợp để giả lập, nhưng phải upgrade

```python
# Hiện tại
pattern = r'\bMpa\b'
if re.search(pattern, text):
    error = {...}
```

### Phần 2: Tích Hợp Claude API

**Bước 1**: Install Anthropic SDK

```bash
pip install anthropic
```

**Bước 2**: Thay thế AISimulator

```python
# backend/app/ai_simulator.py

from anthropic import Anthropic

class RAGWithClaude:
    def __init__(self):
        self.client = Anthropic()
        self.regulations = self._load_regulations()
    
    def _load_regulations(self):
        """Tải quy định từ file"""
        return {
            'phuluc_2': """
                Phụ lục II - Thiết lập bội thập phân...
                - Tiền tố 'mega' = 'M'
                - Đơn vị 'pascal' = 'Pa'  
                - Ví dụ: 'MPa' không phải 'Mpa'
            """,
            'phuluc_3': """
                Phụ lục III - Đơn vị đo tiêu chuẩn...
                - mm, cm, m, bar, Pa, MPa, K, °C
                - Không dùng: D, Mpa, inches
            """,
            'phuluc_5': """
                Phụ lục V - Trình bày đơn vị đo...
                - Dùng dấu phẩy (,) không dấu chấm (.)
                - Ví dụ: '0,3 MPa' không phải '0.3 Mpa'
                - Phải có unit sau giá trị
            """
        }
    
    def analyze_document(self, content):
        """
        Phân tích với Claude
        """
        errors = []
        
        # Xử lý từng paragraph
        for para in content.get('paragraphs', []):
            error_list = self._analyze_text_with_claude(
                para['text'],
                para['id'],
                'paragraph'
            )
            errors.extend(error_list)
        
        # Xử lý từng table cell
        for table in content.get('tables', []):
            for row in table.get('rows', []):
                for cell in row.get('cells', []):
                    error_list = self._analyze_text_with_claude(
                        cell['text'],
                        cell['id'],
                        'table_cell'
                    )
                    errors.extend(error_list)
        
        return errors
    
    def _analyze_text_with_claude(self, text, element_id, element_type):
        """
        Gọi Claude để phân tích 1 đoạn text
        """
        if not text or len(text.strip()) < 5:
            return []
        
        # Tạo prompt
        prompt = f"""
        Bạn là chuyên gia về quy định tiêu chuẩn tài liệu Việt Nam.
        
        QுIRM ĐỊNH:
        {self.regulations['phuluc_2']}
        {self.regulations['phuluc_3']}
        {self.regulations['phuluc_5']}
        
        NHIỆM VỤ: Phân tích text sau để tìm lỗi:
        "{text}"
        
        Trả về JSON có cấu trúc:
        {{
            "errors": [
                {{
                    "error_type": "vi_pham_ky_hieu_don_vi",
                    "reasoning": "Giải thích cụ thể",
                    "reference": "Phụ lục nào",
                    "suggestion": "Sửa thành..."
                }}
            ]
        }}
        
        Nếu không tìm lỗi: return {{"errors": []}}
        """
        
        # Gọi Claude
        message = self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        
        # Parse response
        try:
            response_text = message.content[0].text
            
            # Extract JSON từ response
            import json
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            json_str = response_text[json_start:json_end]
            response_json = json.loads(json_str)
            
            # Transform thành format của app
            errors = []
            for err in response_json.get('errors', []):
                error_obj = {
                    'id': f'error_{len(errors)}',
                    'original_text': text,
                    'elementId': element_id,
                    'elementType': element_type,
                    'danh_sach_cac_loi': [{
                        'error_type': err.get('error_type'),
                        'reasoning': err.get('reasoning'),
                        'reference': err.get('reference')
                    }],
                    'suggestion': err.get('suggestion'),
                    'severity': 'error'
                }
                errors.append(error_obj)
            
            return errors
        
        except Exception as e:
            print(f"Error parsing Claude response: {e}")
            return []
```

**Bước 3**: Update API endpoint

```python
# backend/app/api.py

from app.ai_simulator import RAGWithClaude

@api_bp.route('/analyze/<session_id>', methods=['POST'])
def analyze_document(session_id):
    try:
        upload_dir = os.path.join(..., 'uploads', session_id)
        main_path = os.path.join(upload_dir, 'main.docx')
        
        processor = DocumentProcessor()
        content = processor.extract_text_with_positions(main_path)
        
        # Thay từ AISimulator → RAGWithClaude
        ai = RAGWithClaude()  # ← THAY ĐỔI
        errors = ai.analyze_document(content)
        
        return jsonify({
            'sessionId': session_id,
            'errors': errors
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

### Phần 3: Lựa Chọn AI Provider

#### Option A: Claude (Anthropic)

**Ưu điểm**:
✅ Giá rẻ ($3/$15 per 1M tokens)  
✅ Context window lớn (200K)  
✅ Tiếng Việt tốt  
✅ API đơn giản

**Code**:
```python
from anthropic import Anthropic

client = Anthropic()
message = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1024,
    messages=[request]
)
```

#### Option B: OpenAI (GPT-4)

**Ưu điểm**:
✅ Model mạnh nhất  
✅ Phổ biến nhất  
✅ Hỗ trợ tốt

**Code**:
```python
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
response = client.chat.completions.create(
    model="gpt-4-turbo",
    messages=[request]
)
```

#### Option C: Gemini (Google)

**Ưu điểm**:
✅ Free tier 2M requests/month  
✅ Tích hợp với Google tools

**Code**:
```python
import google.generativeai as genai

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-pro")
response = model.generate_content(prompt)
```

### Phần 4: Setup Environment Variables

**File: `.env`**

```
# Clone từ .env.example
ANTHROPIC_API_KEY=sk-ant-xxxxxxxx
OPENAI_API_KEY=sk-xxxxxxxx
GOOGLE_API_KEY=AIzaxxxxxxxx
```

**Load trong app**:

```python
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv('ANTHROPIC_API_KEY')
```

### Phần 5: Improve Prompts

**Current** (Generic):
```
Phân tích text để tìm lỗi về quy định
```

**Better** (Specific context):
```
Bạn là chuyên gia về quy định tài liệu hợp đồng Việt Nam.
Chuyên biệt về:
1. Trình bày đơn vị đo (Phụ lục V)
2. Ký hiệu tiêu chuẩn (Phụ lục II, III)
3. Định dạng số thập phân (phẩy thay dấu)

QIRMDIN CHỊ TIẾT:
[Full regulations text]

Phân tích text:
"{text}"

Trả về:
1. Danh sách lỗi với chiều chi tiết
2. Giải thích theo quy định cụ thể
3. Đề xuất sửa chữa chính xác

Format JSON:
{
    "errors": [
        {
            "error_type": "...",
            "severity": "error/warning",
            "original": "...",
            "suggestion": "...",
            "reference": "Phụ lục ...",
            "reasoning": "..."
        }
    ]
}
```

### Phần 6: Caching & Performance

**Problem**: Gọi Claude mỗi lần analyze → chậm + tốn tiền

**Solution**: Implement caching

```python
import json
from functools import lru_cache

class CachedAnalyzer:
    def __init__(self):
        self.cache = {}
        self.client = Anthropic()
    
    def analyze_text(self, text):
        """
        Check cache before calling Claude
        """
        # Hash text để dùng làm key
        cache_key = hash(text)
        
        if cache_key in self.cache:
            print(f"Cache hit for: {text[:50]}")
            return self.cache[cache_key]
        
        # Not in cache - call Claude
        result = self._call_claude(text)
        
        # Save to cache
        self.cache[cache_key] = result
        
        return result
    
    def _call_claude(self, text):
        # Actual Claude call
        ...
```

### Phần 7: Testing & Validation

**Test script**:

```python
# test_claude_integration.py

from backend.app.ai_simulator import RAGWithClaude
from backend.app.document_processor import DocumentProcessor

def test_claude_analysis():
    """Test Claude integration"""
    
    # Load test document
    processor = DocumentProcessor()
    content = processor.extract_text_with_positions('samples/sample_main.docx')
    
    # Analyze with Claude
    analyzer = RAGWithClaude()
    errors = analyzer.analyze_document(content)
    
    # Verify
    print(f"Found {len(errors)} errors")
    for error in errors:
        print(f"  - {error['original_text']}: {error['suggestion']}")

if __name__ == '__main__':
    test_claude_analysis()
```

**Chạy test**:
```bash
python test_claude_integration.py
```

### Phần 8: Error Handling

```python
class AnalyzerWithErrorHandling:
    def analyze_document(self, content):
        errors = []
        
        for para in content.get('paragraphs', []):
            try:
                para_errors = self._analyze_text_safe(para)
                errors.extend(para_errors)
            
            except RateLimitError:
                print("Rate limited - retrying...")
                time.sleep(30)
                para_errors = self._analyze_text_safe(para)
                errors.extend(para_errors)
            
            except APIConnectionError as e:
                print(f"Connection error: {e}")
                # Return partial results
                return errors
            
            except Exception as e:
                print(f"Unexpected error for {para['id']}: {e}")
                # Skip this paragraph
                continue
        
        return errors
```

---

## Ví Dụ Code Thực Tế

### Example 1: Tích Hợp Claude Step-by-Step

**File: `backend/app/claude_analyzer.py`**

```python
import os
from anthropic import Anthropic
import json
import re

class ClaudeAnalyzer:
    """
    RAG with Claude for document analysis
    """
    
    def __init__(self):
        self.client = Anthropic()
        self.model = "claude-3-5-sonnet-20241022"
        self.regulations = self._load_regulations()
        self.conversation_history = []
    
    def _load_regulations(self):
        """Load Vietnamese regulations"""
        return """
        QUY ĐỊNH TIÊU CHUẨN TRÌNH BÀY TÀI LIỆU HỢP ĐỒNG
        
        PHỤLỤC II - Thiết lập bội thập phân đơn vị đo
        ============================================
        - Tiền tố "mega" = ký hiệu "M"
        - Đơn vị "pascal" = ký hiệu "Pa"
        - Megapascal = "MPa" (không phải "Mpa", "mpa", "MPA")
        - Tất cả ký hiệu đơn vị theo chuẩn SI
        
        PHỤLỤC III - Đơn vị đo tiêu chuẩn
        =================================
        Danh sách đơn vị được cho phép:
        - Độ dài: mm, cm, m, km
        - Diện tích: mm², cm², m²
        - Thể tích: ml, l, cm³
        - Áp lực: Pa, bar, MPa
        - Nhiệt độ: K, °C, °F
        - Khác: kg, g, mg, s, min, h, V, A, W, Hz, Ω
        
        PHỤLỤC V - Trình bày đơn vị đo pháp định
        =======================================
        - Khi viết giá trị đại lượng, phải có đơn vị đo
        - Ví dụ: "3/8 mm" không phải "3/8"
        - Giữa số và đơn vị phải cách 1 dấu cách
        - Dấu thập phân phải dùng dấu phẩy (,) không dấu chấm (.)
        - Ví dụ: "0,375" không phải "0.375"
        - Range: "3 - 9 mm" không phải "3-9" hay "3-9mm"
        
        QUYẾT ĐỊNH: Chỉ chấp nhận lỗi có bằng chứng rõ ràng từ quy định
        """
    
    def analyze_document(self, content):
        """
        Analyze entire document
        """
        all_errors = []
        
        # Analyze paragraphs
        for para in content.get('paragraphs', []):
            if len(para['text'].strip()) > 5:
                para_errors = self.analyze_text(
                    para['text'],
                    para['id'],
                    'paragraph'
                )
                all_errors.extend(para_errors)
        
        # Analyze table cells
        for table in content.get('tables', []):
            for row in table.get('rows', []):
                for cell in row.get('cells', []):
                    if len(cell['text'].strip()) > 5:
                        cell_errors = self.analyze_text(
                            cell['text'],
                            cell['id'],
                            'table_cell'
                        )
                        all_errors.extend(cell_errors)
        
        return all_errors
    
    def analyze_text(self, text, element_id, element_type):
        """
        Analyze single text with Claude
        """
        # Add to conversation for context
        self.conversation_history.append({
            "role": "user",
            "content": f"""
Phân tích text sau theo quy định:
"{text}"

Trả về JSON với cấu trúc:
{{
    "has_errors": true/false,
    "errors": [
        {{
            "error_type": "vi_pham_ky_hieu_don_vi",
            "problem": "Chi tiết lỗi",
            "suggestion": "Cách sửa",
            "reference": "Phụ lục X",
            "severity": "error"
        }}
    ]
}}
            """
        })
        
        # Call Claude with conversation history
        response = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            system=f"Bạn là chuyên gia quy định tài liệu. Quy định:\n{self.regulations}",
            messages=self.conversation_history
        )
        
        # Extract response
        response_text = response.content[0].text
        self.conversation_history.append({
            "role": "assistant",
            "content": response_text
        })
        
        # Parse JSON
        try:
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
            else:
                return []
            
            # Transform to app format
            errors = []
            for err in data.get('errors', []):
                error_obj = {
                    'id': f'error_{element_id}_{len(errors)}',
                    'original_text': text[:100],
                    'elementId': element_id,
                    'elementType': element_type,
                    'danh_sach_cac_loi': [{
                        'error_type': err.get('error_type', 'unknown'),
                        'reasoning': err.get('problem', ''),
                        'reference': err.get('reference', '')
                    }],
                    'suggestion': err.get('suggestion', ''),
                    'severity': err.get('severity', 'warning')
                }
                errors.append(error_obj)
            
            return errors
        
        except Exception as e:
            print(f"Error parsing response: {e}")
            print(f"Response: {response_text}")
            return []
```

**Sử dụng trong api.py**:

```python
from app.claude_analyzer import ClaudeAnalyzer

@api_bp.route('/analyze/<session_id>', methods=['POST'])
def analyze_document(session_id):
    processor = DocumentProcessor()
    content = processor.extract_text_with_positions(main_path)
    
    analyzer = ClaudeAnalyzer()
    errors = analyzer.analyze_document(content)
    
    return jsonify({'errors': errors}), 200
```

### Example 2: Custom Prompt Template

```python
class AdvancedAnalyzer:
    """
    Sử dụng prompt template để better control
    """
    
    SYSTEM_PROMPT = """
Bạn là chuyên gia kiểm soát chất lượng tài liệu hợp đồng.
Nhiệm vụ: Phát hiện lỗi không tuân thủ quy định tiêu chuẩn.

HƯỚNG DẪN PHÂN TÍCH:
1. Kiểm tra TỪNG LỖI một cách cụ thể
2. Trích dẫn quy định liên quan
3. Giải thích tại sao là lỗi
4. Đề xuất sửa chữa chính xác
5. Ghi rõ mức độ (error/warning/info)

CHỈ báo lỗi nếu CHẮC CHẮN có bằng chứng từ quy định.
    """
    
    def create_analysis_prompt(self, text, regulations):
        return f"""
QUYRNDIN:
{regulations}

TEXT CẦN PHÂN TÍCH:
"{text}"

PHÂN TÍCH:
Hãy phân tích text trên để tìm các lỗi không tuân thủ quy định.

Trả về JSON:
{{
    "analysis": "Mô tả quá trình phân tích",
    "errors_found": [
        {{
            "text_fragment": "Phần text có lỗi",
            "error_type": "Loại lỗi",
            "problem_description": "Mô tả chi tiết lỗi",
            "applicable_regulation": "Phụ lục X - Tiêu đề",
            "citation": "Trích dẫn cụ thể từ quy định",
            "suggested_fix": "Cách sửa đúng",
            "confidence": "high/medium/low"
        }}
    ],
    "total_errors": 0
}}
        """
```

### Example 3: Batch Processing

```python
class BatchAnalyzer:
    """
    Phân tích nhiều tài liệu cùng lúc
    """
    
    def __init__(self, num_workers=3):
        self.num_workers = num_workers
    
    def analyze_batch(self, documents):
        """
        Process multiple documents
        """
        import concurrent.futures
        
        results = {}
        
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=self.num_workers
        ) as executor:
            futures = {
                executor.submit(self.analyze_one, doc): doc_id
                for doc_id, doc in documents.items()
            }
            
            for future in concurrent.futures.as_completed(futures):
                doc_id = futures[future]
                try:
                    errors = future.result()
                    results[doc_id] = {
                        'status': 'success',
                        'errors': errors
                    }
                except Exception as e:
                    results[doc_id] = {
                        'status': 'error',
                        'message': str(e)
                    }
        
        return results
    
    def analyze_one(self, document):
        analyzer = ClaudeAnalyzer()
        return analyzer.analyze_document(document)
```

---

## Checklist Tích Hợp

### ✅ Bước 1: Chuẩn Bị
- [ ] Install anthropic: `pip install anthropic`
- [ ] Lấy API key từ https://console.anthropic.com
- [ ] Tạo file `.env` với `ANTHROPIC_API_KEY`
- [ ] Test connection: `python test_claude_connection.py`

### ✅ Bước 2: Implement
- [ ] Tạo `backend/app/claude_analyzer.py`
- [ ] Update `api.py` để dùng `ClaudeAnalyzer`
- [ ] Test với sample document
- [ ] Verify output format matches frontend

### ✅ Bước 3: Optimize
- [ ] Add caching layer
- [ ] Implement error handling
- [ ] Add logging
- [ ] Performance test

### ✅ Bước 4: Deploy
- [ ] Setup environment variables trên server
- [ ] Test trên production data
- [ ] Monitor API usage & costs
- [ ] Implement rate limiting nếu cần

---

## Tóm Tắt

Ứng dụng được thiết kế modular để dễ integrate AI:

1. **Backend**: `ai_simulator.py` là nơi logic phân tích
   - Hiện tại: Pattern matching (regex)
   - Upgrade: Gọi Claude/GPT API
   - Future: Vector database + embeddings

2. **Frontend**: Không thay đổi
   - ErrorViewer hiển thị errors từ backend
   - Tự động làm việc với format mới

3. **Integration points**:
   - `analyze_document()` method
   - JSON error format
   - API endpoints

Chỉ cần thay backend phần AI - frontend tự động hoạt động! 🚀
