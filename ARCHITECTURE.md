# Architecture & System Design

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    User Interface (React)                    │
│  DocumentUpload Component  │  ErrorViewer Component          │
└────────────────────┬────────────────────────────────────────┘
                     │ (Axios HTTP Requests)
                     │
┌────────────────────▼────────────────────────────────────────┐
│                   Flask Backend API                          │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  API Routes                                          │  │
│  │  - /api/upload      (POST)                          │  │
│  │  - /api/analyze     (POST)                          │  │
│  │  - /api/apply-suggestions (POST)                    │  │
│  │  - /api/download    (GET)                           │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Modules                                             │  │
│  │  - DocumentProcessor (DOCX Handling)                │  │
│  │  - AISimulator (Error Detection)                    │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────────────────┘
                     │ (File I/O)
                     │
        ┌────────────▼─────────────┐
        │                          │
        │   File System            │
        │   /backend/uploads/      │
        │   ├── [session_id]/      │
        │   │   ├── main.docx      │
        │   │   ├── ref_*.docx     │
        │   │   ├── reg_*.docx     │
        │   │   └── main_corrected.docx
        │   └── [session_id]/...   │
        │                          │
        └──────────────────────────┘
```

## Component Architecture

### Frontend (React)

```
App.js (Main Container)
├── DocumentUpload.js
│   ├── File Input Handlers
│   ├── Upload Logic (Axios)
│   ├── Auto-analyze on Upload
│   └── DocumentUpload.css
│
└── ErrorViewer.js
    ├── Error Display Logic
    ├── Filter & Sort
    ├── Edit Mode
    ├── Apply Suggestions
    └── ErrorViewer.css
```

### Backend (Flask)

```
flask_app/
├── __init__.py (App Factory)
├── api.py (Route Handlers)
├── document_processor.py
│   ├── extract_text_with_positions()
│   ├── apply_corrections()
│   └── highlight_error()
│
└── ai_simulator.py
    ├── _init_patterns()
    ├── analyze_document()
    ├── _analyze_text()
    └── _generate_simulated_errors()
```

## Data Flow

### Upload Flow

```
1. User selects files in DocumentUpload component
   ├── mainDocument (required)
   ├── referenceDocuments[] (optional)
   └── regulations[] (optional)

2. User clicks "Upload & Analyze"

3. React/Axios sends multipart/form-data to /api/upload

4. Backend receives files
   ├── Validates file format (.docx)
   ├── Creates session ID (UUID)
   ├── Creates session directory
   ├── Saves files: main.docx, ref_*.docx, reg_*.docx
   └── Extracts text from main.docx

5. Backend returns sessionId to frontend

6. Frontend automatically calls /api/analyze/<sessionId>
```

### Analysis Flow

```
1. Backend receives analyze request with sessionId

2. DocumentProcessor extracts content from main.docx
   ├── Reads paragraphs with formatting info
   ├── Reads tables with cell structure
   └── Returns structured content object

3. AISimulator analyzes content
   ├── Scans text for predefined patterns
   ├── Checks references and regulations
   ├── Generates error list with suggestions
   └── Returns errors with metadata

4. Backend returns errors array to frontend

5. Frontend displays errors in ErrorViewer
   ├── Renders error list with checkboxes
   ├── Shows error details and suggestions
   ├── Enables filtering and sorting
   └── Allows user to edit suggestions
```

### Correction Flow

```
1. User selects errors and clicks "Accept"

2. Frontend collects accepted errors
   ├── Extracts elementId and suggested newText
   └── Sends to /api/apply-suggestions/<sessionId>

3. Backend processes corrections
   ├── Loads main.docx from session
   ├── For each correction:
   │   ├── Parses elementId (para_X, table_X_row_Y_cell_Z)
   │   ├── Locates element in document
   │   └── Replaces text while preserving formatting
   ├── Saves as main_corrected.docx
   └── Returns downloadUrl

4. Frontend triggers download
   ├── User clicks download button
   └── Browser fetches /api/download/<sessionId>/main_corrected.docx
```

## Error Detection Strategy

### Pattern-Based Detection

Current implementation uses regex patterns to detect:

1. **Spacing Errors**: Multiple consecutive spaces
2. **Format Errors**: Inconsistent company name capitalization
3. **Date Format**: Detect non-standard date patterns
4. **Currency**: Inconsistent currency symbols

### Simulated AI Analysis

The `AISimulator` class simulates AI by:

1. Applying predefined pattern rules
2. Generating contextual error messages
3. Providing appropriate suggestions
4. Assigning severity levels

### Future AI Integration

To integrate real AI:

```python
# In ai_simulator.py
from openai import OpenAI

class AISimulator:
    def analyze_document(self, content):
        # Replace simulated logic with:
        response = self.ai_client.analyze(content)
        return response.errors
```

## File Handling

### DOCX Processing

```python
from docx import Document

document = Document('file.docx')

# Access structure
for para in document.paragraphs:
    text = para.text
    for run in para.runs:
        text = run.text

for table in document.tables:
    for row in table.rows:
        for cell in row.cells:
            text = cell.text
```

### Session Management

- Each upload creates unique session directory
- Files stored with structured naming: `<type>_<index>.docx`
- Session persists until browser session ends
- Cleanup handled by OS or scheduled task

## Database Considerations

Current implementation uses file-based storage. For production, consider:

```python
# Option 1: SQLAlchemy with SQLite
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Session(db.Model):
    id = db.Column(db.String, primary_key=True)
    created_at = db.Column(db.DateTime)
    status = db.Column(db.String)
    file_paths = db.Column(db.JSON)

class Error(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String, db.ForeignKey('session.id'))
    error_data = db.Column(db.JSON)
```

## Security Considerations

### Current Implementation

1. File size limit: 100MB
2. Only .docx format allowed
3. Session-based isolation
4. CORS enabled for development

### Production Recommendations

1. **Authentication**: Add JWT or session auth
2. **Rate Limiting**: Limit requests per user
3. **File Validation**: Check DOCX structure integrity
4. **Virus Scanning**: Integrate with antivirus API
5. **HTTPS**: Use SSL/TLS
6. **CORS**: Restrict to known domains
7. **Input Validation**: Sanitize suggestions before storing
8. **File Cleanup**: Automated cleanup of old sessions

## Performance Optimization

### Frontend

```javascript
// Optimize component re-renders
const memoizedErrors = useMemo(() => filterErrors(), []);

// Lazy load error details
const [expandedErrors, setExpandedErrors] = useState({});
```

### Backend

```python
# Process large documents in chunks
def process_large_document(file_path, chunk_size=100):
    for chunk in read_chunks(file_path, chunk_size):
        analyze_chunk(chunk)

# Cache analysis results
from functools import lru_cache

@lru_cache(maxsize=32)
def analyze_pattern(text):
    return re_compile('pattern').findall(text)
```

## Scalability

### Single Server
- Current setup suitable for <100 concurrent users
- File-based storage works for <1000 sessions

### Distributed System

```
┌─────────────────────┐
│   Load Balancer     │
└────────┬────────────┘
         │
    ┌────┼────┐
    │    │    │
┌───▼┐ ┌▼──┐ ┌▼──┐
│ API│ │API│ │API│  (Multiple instances)
└───┬┘ └┬──┘ └┬──┘
    │   │    │
    └─┬─┴────┘
      │
┌─────▼──────────┐
│  Redis Cache   │
└────────────────┘
      │
┌─────▼──────────┐
│  Shared Storage│  (S3, Azure Blob)
└────────────────┘
      │
┌─────▼──────────┐
│   Database     │  (PostgreSQL)
└────────────────┘
```

## Testing Strategy

### Unit Tests

```python
# test_document_processor.py
def test_extract_text():
    processor = DocumentProcessor()
    content = processor.extract_text_with_positions('test.docx')
    assert len(content['paragraphs']) > 0

def test_apply_corrections():
    processor = DocumentProcessor()
    processor.apply_corrections('in.docx', 'out.docx', corrections)
    # Verify output file
```

### Integration Tests

```javascript
// Test complete workflow
test('Upload and analyze document', async () => {
  const form = new FormData();
  form.append('mainDocument', testFile);
  
  const uploadRes = await axios.post('/api/upload', form);
  expect(uploadRes.data.sessionId).toBeDefined();
  
  const analysisRes = await axios.post(`/api/analyze/${uploadRes.data.sessionId}`);
  expect(analysisRes.data.errors).toBeArrayOf(Object);
});
```

---

**Architecture Version**: 1.0
**Last Updated**: April 2026
