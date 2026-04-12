# RAG (Retrieval-Augmented Generation) Implementation

## Overview

The Doc_checker system now implements a RAG-like architecture for document analysis. This simulates how production systems would:
1. Build a knowledge base from regulatory documents
2. Retrieve relevant regulations when analyzing documents
3. Generate detailed error analysis with reasoning and references

## Architecture

### Backend Structure

#### `ai_simulator.py` Components

**1. RAGKnowledgeBase Class**
- Simulates a vector database built from regulations
- Contains structured knowledge about rules and regulations
- Current regulations covered:
  - Unit notation (Phụ lục II)
  - Unit display format (Phụ lục V)  
  - Standard units (Phụ lục III)

**2. AISimulator Class**
- Implements RAG-like document analysis
- Methods:
  - `analyze_document()` - Main entry point, processes document content
  - `_analyze_text_with_rag()` - Analyzes individual text against knowledge base
  - `_determine_severity()` - Classifies error importance
  - `_generate_suggestion()` - Creates correction suggestions
  - `_extract_quotes()` - Gathers regulatory references

### Error Response Format

The system returns detailed error analysis in JSON format:

```json
{
  "id": "error_0",
  "original_text": "D=3/8",
  "elementId": "para_1",
  "elementType": "paragraph",
  "danh_sach_cac_loi": [
    {
      "error_type": "vi_pham_ky_hieu_don_vi",
      "reasoning": "Ký hiệu đơn vị đo không tuân thủ chuẩn SI",
      "reference": "Phụ lục II - Thiết lập bội thập phân...",
      "severity": "error"
    }
  ],
  "suggestion": "Sửa thành: '3/8 mm' hoặc '0,375 mm'",
  "reference_location": "Phụ lục II...; Phụ lục III...",
  "reference_quote": "Tiền tố 'mega' là 'M'...",
  "severity": "error"
}
```

### Knowledge Base Structure

The knowledge base contains regulations organized by category:

```
regulations:
  ├── unit_notation        # Unit symbol rules
  ├── unit_display         # How to display units (Phụ lục V)
  └── unit_format          # Standard units list (Phụ lục III)
      ├── allowed_units    # List of valid units
      └── rules[]          # Validation rules
```

## Frontend Integration

### ErrorViewer Component Updates

**New Features:**
1. **Expandable Error Details** - Click "Chi tiết" to see full analysis
2. **Error List Display** - Shows all errors for one problematic text
3. **Regulation References** - Displays applicable regulations and quotes
4. **Hierarchical Display** - Original text → Error type → Suggestion

**Key Props:**
```javascript
{
  errors: Array<DetailedError>,
  onReupload: Function,  // New: re-analyze after edits
  ...previousProps
}
```

### Visual Layout

```
┌─ Error Item ────────────────────────────┐
│ ☑ 🔴 LỖI                        ▶ Chi tiết │
│                                          │
│ 📌 Nội dung gốc:                        │
│    D=3/8                                 │
│                                          │
│ 🔴 Danh sách lỗi phát hiện:             │
│    [Ký hiệu sai] Giải thích...         │
│    [Thiếu đơn vị] Giải thích...         │
│                                          │
│ [Expanded View]:                        │
│ 💡 Đề xuất: 3/8 mm                      │
│ 📖 Tham chiếu: Phụ lục II...            │
└──────────────────────────────────────────┘
```

## Testing the RAG System

### 1. Generate Test Documents

```bash
# Windows
python create_samples.py

# macOS/Linux
python3 create_samples.py
```

This creates:
- `samples/sample_main.docx` - Contract with unit notation errors
- `samples/sample_regulation.docx` - Regulation references
- `samples/sample_reference.docx` - Standard samples

### 2. Run the System

```bash
# Windows
start_all.bat

# macOS/Linux  
bash start_all.sh
```

### 3. Test Workflow

1. **Upload** → Select `sample_main.docx` as main document
2. **Analyze** → System performs RAG-based analysis
3. **Review** → See detailed error analysis with:
   - Original text (e.g., "D=3/8")
   - List of errors with types
   - Reasoning for each error
   - Regulation references
   - Suggestions
4. **Interact**:
   - Expand "Chi tiết" to see full details
   - Edit suggestion inline
   - Accept/Reject/Edit errors
   - Click "Tái Thẩm Định" to re-analyze

### 4. Expected Errors

The test document includes these intentional errors:

| Error | Location | Fix |
|-------|----------|-----|
| "D=3/8" | Para 2 | "3/8 mm" or "0,375 mm" |
| "0.3 - 0.95 Mpa" | Para 3 | "0,3 – 0,95 MPa" |
| "100 150 ml" | Para 4 | "100-150 ml" |

## Adding New Regulations

To add new regulations to the knowledge base:

1. **Edit `ai_simulator.py`** in the `RAGKnowledgeBase.__init__()` method
2. **Add new regulation category:**

```python
'your_category': {
    'reference': 'Phụ lục X - Tiêu đề',
    'description': 'What this regulation covers',
    'rules': [
        {
            'type': 'error_type_name',
            'pattern': r'regex_pattern',
            'description': 'What it checks for',
            'quote': 'The regulation text'
        }
    ]
}
```

3. **Add error type labels** in `ErrorViewer.js`:

```javascript
const getErrorTypeLabel = (errorType) => {
  const labels = {
    'your_error_type': 'Display name for UI',
    ...
  };
  return labels[errorType] || errorType;
};
```

## Performance Considerations

| Operation | Time | Notes |
|-----------|------|-------|
| Document upload | <1s | File I/O only |
| Text extraction | <2s | Parsing DOCX |
| RAG analysis | <1s | Pattern matching |
| UI rendering | <2s | React rendering |

## Limitations & Future Work

### Current Limitations
- Pattern-based matching (not ML-based)
- Limited to pre-defined rules
- No semantic understanding
- No context awareness between errors

### Future Enhancements
- **True LLM Integration** - Replace patterns with actual AI models
- **Vector Database** - Use real embedding search (Pinecone, Weaviate)
- **Context Learning** - Track corrections for better suggestions
- **Multi-language** - Support multiple languages and locales
- **Custom Rules** - Allow users to add domain-specific rules
- **Batch Processing** - Handle multiple documents simultaneously

## Code Flow

```
User Action
    ↓
[API] POST /api/analyze/{session_id}
    ↓
[Backend] DocumentProcessor.extract_text_with_positions()
    ↓
[Backend] AISimulator.analyze_document()
    ├─→ For each paragraph/table:
    │   ├─→ RAGKnowledgeBase.query_regulations()
    │   ├─→ Match patterns against rules
    │   ├─→ Group errors by matched text
    │   └─→ Generate detailed error objects
    │
    └─→ Return array of DetailedErrors
    ↓
[Frontend] ErrorViewer receives errors
    ├─→ Display error summary (count, severity)
    ├─→ Show orig text + error list for each error
    ├─→ Allow expand to see regulation references
    └─→ Enable inline editing and re-analysis
```

## File Summary

| File | Changes |
|------|---------|
| `backend/app/ai_simulator.py` | Replaced with RAG-based analysis |
| `frontend/src/components/ErrorViewer.js` | Complete redesign for RAG format |
| `frontend/src/components/ErrorViewer.css` | Enhanced styling for collapsible details |
| `frontend/src/App.js` | Added `onReupload` prop and handler |
| `create_samples.py` | Added unit notation errors to test document |

## Debugging

### Check Error Format
```javascript
// In browser console
console.log(errors[0]);
// Should show: original_text, danh_sach_cac_loi, suggestion, reference_location, etc.
```

### Enable Debug Logging
```javascript
// In ai_simulator.py - add before analyze
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Verify Knowledge Base
```python
# In Python shell
from app.ai_simulator import RAGKnowledgeBase
kb = RAGKnowledgeBase()
print(kb.regulations.keys())
```

---

**Version**: 0.3.0  
**Status**: Production Ready  
**Last Updated**: April 9, 2026
