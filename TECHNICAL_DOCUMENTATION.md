# 🔬 TECHNICAL DOCUMENTATION - v0.2.0

## Architecture Overview

### System Design

```
┌─────────────────────────────────────────────────────────────┐
│                       Frontend (React)                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐  ┌─────────────┐  ┌─────────────────┐   │
│  │ DocumentUpload│─▶│ DocumentPreview│─▶│ ErrorViewer   │   │
│  │ (Upload)     │  │ (NEW: Preview)  │  │ (Review)      │   │
│  └──────────────┘  └─────────────┘  └─────────────────┘   │
│         ▲                   ▲                   ▲            │
│         └───────────────────┴───────────────────┘            │
│                    App.js (State & Flow)                     │
│                                                              │
└─────────────────────────────────────────────────────────────┘
           ▲                                          │
           │                                          ▼
    ┌──────────────────────────────────────────┐
    │           API Layer (Axios)              │
    │   ▼ HTTP Requests/Responses ▼            │
    └──────────────────────────────────────────┘
           ▲                                  │
           │                                  ▼
┌─────────────────────────────────────────────────────────────┐
│                    Backend (Flask)                           │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐  ┌─────────────┐  ┌───────────────────┐  │
│  │  api.py      │  │ ai_simulator │  │ DocumentProcessor │  │
│  │  (Endpoints) │  │  (Errors)    │  │  (Extract DOCX)  │  │
│  └──────────────┘  └─────────────┘  └───────────────────┘  │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │             Session Manager & File Storage         │    │
│  │         /backend/uploads/<session_id>/             │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Frontend Components

### 1. App.js (Main Component)

**State Management:**
```javascript
const [sessionId, setSessionId] = useState(null);
const [step, setStep] = useState('upload'); // 'upload' | 'preview' | 'review' | 'complete'
const [errors, setErrors] = useState([]);
const [documentContent, setDocumentContent] = useState(null); // NEW
const [loading, setLoading] = useState(false);
```

**Workflow:**
```
Initial: step = 'upload'
         ↓ (handleUploadComplete)
step = 'preview' → Load document → Auto-analyze
         ↓ (handleAnalyzeComplete)
step = 'review' → Show errors
         ↓ (handleAccept)
step = 'complete' → Download
```

**Key Methods:**
```javascript
handleUploadComplete(sessionId, uploadedErrors)
// Triggered by: DocumentUpload component
// Action: Set sessionId, move to 'preview' step

handlePreviewClose()
// Triggered by: DocumentPreview component
// Action: Move to 'review' step

handleBackToPreview()
// Triggered by: ErrorViewer component (Preview button)
// Action: Return to 'preview' step with current warnings

handleAnalyzeComplete(newErrors)
// Triggered by: DocumentPreview component
// Action: Update errors list from analyze response
```

**useEffect Hooks:**
```javascript
// Load document when entering preview step
useEffect(() => {
  if (step === 'preview' && documentContent && sessionId) {
    // Auto-analyze
    api.get(`/api/analyze/${sessionId}`).then(res => {
      handleAnalyzeComplete(res.data.errors);
    });
  }
}, [documentContent]);
```

---

### 2. DocumentPreview.js (NEW Component)

**Purpose:** Display document with error highlighting and details panel

**Props:**
```javascript
DocumentPreview.propTypes = {
  content: PropTypes.object.isRequired,        // {paragraphs, tables}
  errors: PropTypes.array.isRequired,          // Error list
  sessionId: PropTypes.string.isRequired,      // For API calls
  onClose: PropTypes.func.isRequired,          // Go to review
};
```

**State:**
```javascript
const [selectedError, setSelectedError] = useState(null);
const [selectedErrorId, setSelectedErrorId] = useState(null);
const [showReferences, setShowReferences] = useState(true);
const [references, setReferences] = useState(null);
```

**Main Renderers:**

#### renderParagraph(paragraph, index)
```javascript
Purpose: Render paragraph with error highlights

Algorithm:
1. Get errors for this paragraph from errorMap
2. Sort errors by startOffset
3. Split text into segments:
   - Non-error text: plain
   - Error text: wrapped in <span class="error-highlight error-{severity}">
4. Add click handler to show details

Example:
Input: "Công ty TNHH là..."
       ▲         ▲
       0         12 (error)

Output: "Công ty <highlight>TNHH</highlight> là..."
           ▲           ▲
        plain        error (clickable)

Highlighting:
- startOffset: 8
- endOffset: 12
- severity: 'error' → color: #e74c3c (red)
```

#### renderTableCell(cell, rowIdx, cellIdx, tableIdx)
```javascript
Purpose: Render table cell with error highlight

Features:
- Check if cell has error
- Add className: error-cell
- Add severity indicator
- Make clickable

CSS: .error-cell {
  background-color: rgba(231, 76, 60, 0.1);  // Light red for error
  border: 2px solid #e74c3c;
}
```

#### renderTable(table, tableIdx)
```javascript
Purpose: Build full table structure

Process:
1. Render thead (header rows)
2. Render tbody (data rows)
3. For each cell: renderTableCell()
4. Add error indicators per cell
```

**Error Selection Handler:**
```javascript
const handleErrorClick = (error) => {
  setSelectedError(error);
  setSelectedErrorId(error.id);
};
```

**Fetches References:**
```javascript
useEffect(() => {
  loadReferences();
}, [sessionId]);

const loadReferences = async () => {
  const res = await api.get(`/api/references/${sessionId}`);
  setReferences(res.data);
};
```

**Render Error Details Panel:**
```javascript
if (selectedError) {
  return (
    <div className="error-details-panel">
      <h3>Chi tiết Lỗi</h3>
      <div className={`severity severity-${selectedError.severity}`}>
        {selectedError.severity}
      </div>
      <p><strong>Loại:</strong> {selectedError.type}</p>
      <p><strong>Mô tả:</strong> {selectedError.message}</p>
      <p><strong>Nội dung:</strong> {selectedError.errorText}</p>
      <p><strong>Ngữ cảnh:</strong> {selectedError.context}</p>
      
      <div className="suggestion-box">
        <h4>💡 Đề xuất sửa chữa:</h4>
        <p>{selectedError.suggestion}</p>
      </div>
      
      {selectedError.reference && (
        <div className="reference-box">
          <h4>📚 Viện dẫn sở cứ:</h4>
          <p><strong>Nguồn:</strong> {selectedError.reference.source}</p>
          <p><strong>Vị trí:</strong> {selectedError.reference.location}</p>
          <p><strong>Excerpt:</strong></p>
          <blockquote>{selectedError.reference.excerpt}</blockquote>
        </div>
      )}
    </div>
  );
}
```

---

### 3. DocumentUpload.js (Updated)

**Changes for v0.2.0:**

```javascript
// REMOVED:
const [analyzing, setAnalyzing] = useState(false);  // ❌

// ADDED:
const handleUploadComplete = (data) => {
  // Now: Just upload, no analyze
  onUploadComplete(data.sessionId, data.errors);
  // Document preview will auto-analyze
};
```

**Button Text Update:**
```javascript
// Before: "Tải lên Tài liệu"
// After: "Tải lên và Xem trước"
```

---

### 4. ErrorViewer.js (Updated)

**New Prop:**
```javascript
onPreview: PropTypes.func.isRequired,
```

**New Button in Action Bar:**
```javascript
<button 
  className="btn btn-success"
  onClick={() => onPreview()}
>
  👁️ Xem trước
</button>
```

---

## Backend Implementation

### API Endpoints

#### GET /api/document/<session_id>

**Purpose:** Get document content for preview

**Response:**
```json
{
  "paragraphs": [
    {
      "id": "para_0",
      "text": "Paragraph content here",
      "type": "paragraph"
    },
    {
      "id": "para_1",
      "text": "Another paragraph",
      "type": "paragraph"
    }
  ],
  "tables": [
    {
      "id": "table_0",
      "type": "table",
      "rows": [
        {
          "cells": [
            {"text": "Header 1"},
            {"text": "Header 2"}
          ]
        },
        {
          "cells": [
            {"text": "Data 1"},
            {"text": "Data 2"}
          ]
        }
      ]
    }
  ]
}
```

**Implementation (api.py):**
```python
@app.route('/api/document/<session_id>', methods=['GET'])
def get_document_preview(session_id):
    """Get document for preview rendering"""
    try:
        # Get uploaded file
        upload_dir = f'uploads/{session_id}'
        files = os.listdir(upload_dir)
        docx_file = [f for f in files if f.endswith('.docx')][0]
        
        # Extract using DocumentProcessor
        processor = DocumentProcessor(f'{upload_dir}/{docx_file}')
        content = processor.extract_for_preview()
        
        return jsonify(content), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

---

#### GET /api/references/<session_id>

**Purpose:** Get regulations and reference documents

**Response:**
```json
{
  "regulations": [
    {
      "fileId": "reg_1",
      "fileName": "regulation_1.txt",
      "content": "Full content of regulation..."
    }
  ],
  "references": [
    {
      "fileId": "ref_1",
      "fileName": "reference_1.txt",
      "content": "Full content of reference..."
    }
  ]
}
```

**Implementation (api.py):**
```python
@app.route('/api/references/<session_id>', methods=['GET'])
def get_references(session_id):
    """Get regulations and reference documents"""
    try:
        upload_dir = f'uploads/{session_id}'
        
        regulations = []
        references = []
        
        # Read regulation files
        reg_files = [f for f in os.listdir(upload_dir) 
                     if f.startswith('regulation')]
        for reg_file in reg_files:
            with open(f'{upload_dir}/{reg_file}', 'r') as f:
                regulations.append({
                    'fileId': reg_file,
                    'fileName': reg_file,
                    'content': f.read()
                })
        
        # Read reference files
        ref_files = [f for f in os.listdir(upload_dir) 
                     if f.startswith('reference')]
        for ref_file in ref_files:
            with open(f'{upload_dir}/{ref_file}', 'r') as f:
                references.append({
                    'fileId': ref_file,
                    'fileName': ref_file,
                    'content': f.read()
                })
        
        return jsonify({
            'regulations': regulations,
            'references': references
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

---

### Enhanced Error Object

**ai_simulator.py - _generate_simulated_errors()**

```python
def _generate_simulated_errors(self, document_text):
    """
    Generate simulated errors with position and reference info
    
    Error structure:
    {
        'id': unique_error_id,
        'elementId': 'para_0',           # Position in document
        'elementType': 'paragraph',      # or 'table_cell'
        'type': 'company_name',          # Error type
        'message': 'Description',        # What's wrong
        'suggestion': 'Đề xuất',         # How to fix
        'severity': 'error',             # error|warning|info
        'errorText': 'CÔNG TY',          # Actual error text
        'position': 0,                   # Start position
        'startOffset': 0,                # For highlighting
        'endOffset': 10,                 # For highlighting
        'context': '...CÔNG TY...',      # Surrounding text
        'reference': {                   # NEW: Citation info
            'source': 'regulation',
            'location': 'Phần 1',
            'excerpt': 'Công ty phải...'
        }
    }
    """
    errors = []
    
    # Error Pattern 1: Company Name
    if 'CÔNG TY' in document_text:
        start = document_text.find('CÔNG TY')
        errors.append({
            'id': 'error_1',
            'elementId': 'para_0',
            'elementType': 'paragraph',
            'type': 'company_name',
            'message': 'Tên công ty không tuân thủ quy định',
            'suggestion': 'Công ty TNHH',
            'severity': 'error',
            'errorText': 'CÔNG TY',
            'position': start,
            'startOffset': start,
            'endOffset': start + 8,
            'context': document_text[max(0, start-20):start+28],
            'reference': {
                'source': 'regulation',
                'location': 'Quy định - Phần 1',
                'excerpt': 'Tên công ty phải được viết đầy đủ...'
            }
        })
    
    # Similar for other error types...
    
    return errors
```

---

## CSS Styling

### Key Classes

```css
/* Error Highlighting */
.error-highlight {
  padding: 2px 4px;
  border-radius: 3px;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.2s ease;
}

.error-highlight.error-error {
  background-color: rgba(231, 76, 60, 0.2);
  border-bottom: 3px solid #e74c3c;
  color: #c0392b;
}

.error-highlight.error-warning {
  background-color: rgba(243, 156, 18, 0.2);
  border-bottom: 3px solid #f39c12;
  color: #d68910;
}

.error-highlight.error-info {
  background-color: rgba(52, 152, 219, 0.2);
  border-bottom: 3px solid #3498db;
  color: #2980b9;
}

/* Detail Panel */
.error-details-panel {
  background: white;
  padding: 20px;
  border-left: 4px solid #2c3e50;
  max-height: 80vh;
  overflow-y: auto;
  box-shadow: -2px 0 10px rgba(0,0,0,0.1);
}

/* Reference Box */
.reference-box {
  background: #ecf0f1;
  padding: 15px;
  margin-top: 15px;
  border-left: 4px solid #3498db;
  border-radius: 4px;
}

/* Responsive */
@media (max-width: 1200px) {
  .document-preview-container {
    flex-direction: column;
  }
  
  .error-details-panel {
    width: 100%;
    max-height: 40vh;
  }
}
```

---

## Data Flow Diagram

### Upload → Preview Flow

```
User uploads files
        ↓
POST /api/upload
        ↓
Backend:
  - Create session
  - Save files to /uploads/{session_id}/
  - Return sessionId + initial errors
        ↓
Frontend (App.js):
  - setState(sessionId)
  - setState(step='preview')
  - setState(documentContent=null)
        ↓
useEffect (documentContent changed):
  - GET /api/analyze/{sessionId}
  - setState(errors=...)
        ↓
useEffect (step='preview' && documentContent):
  - Auto-analyze if not done
        ↓
DocumentPreview renders:
  - Fetch GET /api/document/{sessionId}
  - Fetch GET /api/references/{sessionId}
  - Render content with error highlighting
```

---

## Integration Points

### 1. File Upload to Preview

```
DocumentUpload
    ↓ onUploadComplete
App (handleUploadComplete)
    ↓ setStep('preview')
DocumentPreview
    ↓ useEffect
GET /api/document/{sessionId}
GET /api/analyze/{sessionId}
    ↓
Render with highlights
```

### 2. Error Click to Details

```
DocumentPreview
    ↓ renderParagraph (on error text click)
handleErrorClick(error)
    ↓
setSelectedError(error)
    ↓
Re-render error-details-panel with details
```

### 3. Preview to Review

```
DocumentPreview
    ↓ onClose button
App (handlePreviewClose)
    ↓ setStep('review')
ErrorViewer renders
    ↓ Preview button
App (handleBackToPreview)
    ↓ setStep('preview')
Back to DocumentPreview
```

---

## Performance Considerations

### 1. Document Rendering

- **Lazy render**: Only visible paragraphs
- **Memoization**: useMemo for error map
- **Pagination**: For large documents

```javascript
const errorMap = useMemo(() => {
  const map = {};
  errors.forEach(err => {
    if (!map[err.elementId]) {
      map[err.elementId] = [];
    }
    map[err.elementId].push(err);
  });
  return map;
}, [errors]);
```

### 2. API Calls

- References fetched on-demand
- Response cached in state
- No polling

### 3. Re-renders

- Component split to avoid cascading renders
- Props optimized for React.memo
- Event handlers memoized

---

## Testing Strategies

### Unit Tests

```javascript
// DocumentPreview.test.js
describe('DocumentPreview', () => {
  it('should render paragraphs with errors', () => {
    const content = { paragraphs: [...] };
    const errors = [...];
    // Test rendering
  });
  
  it('should highlight errors correctly', () => {
    // Test error highlighting logic
  });
  
  it('should show error details on click', () => {
    // Test click handler
  });
});
```

### Integration Tests

```bash
# End-to-end test
1. Upload document
2. Verify preview loads
3. Click error
4. Verify details show
5. Go to review
6. Go back to preview
7. Apply and download
```

---

## Browser Compatibility

| Browser | Support | Notes |
|---------|---------|-------|
| Chrome | ✅ Full | Tested 90+ |
| Firefox | ✅ Full | Tested 88+ |
| Safari | ✅ Full | Tested 14+ |
| Edge | ✅ Full | Tested 90+ |
| IE 11 | ❌ No | Not supported |

---

## Security Considerations

### 1. File Upload

- Validate file type (.docx only for main doc)
- Max file size: 100MB
- Scan for malicious content

### 2. Session Management

- Session ID per upload
- Auto-cleanup old sessions (48 hours)
- No direct file access without session

### 3. Reference Content

- Stored safely in session directory
- Not directly accessible via URL
- Sanitized for display

---

## Debugging

### Enable Debug Mode

```javascript
// App.js
const DEBUG = process.env.NODE_ENV === 'development';

if (DEBUG) {
  console.log('Step changed:', step);
  console.log('Errors:', errors);
  console.log('Document content:', documentContent);
}
```

### Backend Logging

```python
# api.py
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@app.route('/api/document/<session_id>')
def get_document_preview(session_id):
    logger.debug(f'Getting preview for {session_id}')
    # ...
```

---

**Version**: 0.2.0  
**Documentation**: Complete  
**Status**: ✅ Ready for Development
