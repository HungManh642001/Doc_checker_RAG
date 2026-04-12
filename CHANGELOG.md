# 📋 CHANGELOG - Nâng Cấp v0.2.0

## 🔄 Thay Đổi Chi Tiết

### Backend (`backend/`)

#### 1. **app/ai_simulator.py**
```python
# CHANGED: Enhanced error structure with references
def _generate_simulated_errors():
    # Now includes:
    # - startOffset, endOffset (for highlighting)
    # - reference: { source, excerpt, location }
    # - context (surrounding text)
```

**Changes:**
- Line ~80-150: Enhanced `_generate_simulated_errors()` to include reference data
- Added 4 error patterns with full reference information
- Each error now has position tracking for highlighting

---

#### 2. **app/api.py**
```python
# NEW: Two new endpoints for preview

@app.route('/api/document/<session_id>', methods=['GET'])
def get_document_preview(session_id):
    """Get document content for preview rendering"""
    # Returns paragraphs and tables with IDs

@app.route('/api/references/<session_id>', methods=['GET'])
def get_references(session_id):
    """Get regulations and reference documents"""
    # Returns list of regulations and references with content
```

**Changes:**
- Added endpoint: `GET /api/document/<session_id>` (~20 lines)
- Added endpoint: `GET /api/references/<session_id>` (~20 lines)
- Both endpoints integrated with DocumentProcessor

---

### Frontend (`frontend/src/`)

#### 1. **components/DocumentPreview.js** ✨ NEW
```javascript
// NEW COMPONENT: Display document with error highlighting
// ~350 lines of functional component

Features:
- renderParagraph() - Render paragraphs with error highlights
- renderTableCell() - Render table cells with highlights
- renderTable() - Build table structure
- Error handlers - Click to show details
- Reference display - Show regulations & sources
```

**Content:**
- Main component: DocumentPreview
- Sub-renders: renderParagraph, renderTable, renderTableCell
- State: selectedError, selectedErrorId, showReferences
- Styling: Inline styles + CSS modules

---

#### 2. **components/DocumentPreview.css** ✨ NEW
```css
/* Styling for Document Preview Component */
/* ~450 lines */

Includes:
- .error-highlight.error-error (red #e74c3c)
- .error-highlight.error-warning (yellow #f39c12)
- .error-highlight.error-info (blue #3498db)
- .error-cell - Table cell highlighting
- .error-details-panel - Side panel
- .reference-box - Citation display
- Responsive design (1200px breakpoint)
```

---

#### 3. **App.js** (Updated)
```javascript
// CHANGED: Added preview step to workflow

// New state variable:
const [documentContent, setDocumentContent] = useState(null);

// Workflow update:
// 'upload' → 'preview' → 'review' → 'complete'
//            ↑ NEW STEP

// New useEffect for document preview:
useEffect(() => {
  if (step === 'preview' && documentContent && sessionId) {
    // Auto-analyze errors when preview loads
    analyzeDocument();
  }
}, [documentContent]);

// New method: handleBackToPreview()
```

**Changes:**
- Line ~80-100: Added documentContent state
- Line ~150-170: Added useEffect for preview step
- Line ~200-230: Added handleBackToPreview function
- Line ~280: Updated condition for DocumentPreview render

---

#### 4. **components/DocumentUpload.js** (Updated)
```javascript
// CHANGED: Removed auto-analyze, simplified flow

// Removed:
// - analyzing state
// - onAnalyzeComplete callback
// - auto-analyze logic in upload handler

// Updated button text:
// "Tải lên Tài liệu" → "Tải lên và Xem trước"
```

**Changes:**
- Line ~30: Removed `analyzing` from state
- Line ~50: Removed analyzing state update
- Line ~100: Removed analyzing completion logic
- Line ~150: Updated button text
- Line ~160: Updated onUploadComplete callback (simpler)

---

#### 5. **components/ErrorViewer.js** (Updated)
```javascript
// CHANGED: Added preview button to action bar

// New props:
onPreview: PropTypes.func.isRequired

// New button in action-bar:
<button className="btn btn-success" onClick={() => onPreview()}>
  👁️ Xem trước
</button>
```

**Changes:**
- Line ~15: Added onPreview prop definition
- Line ~300: Added preview button to action-bar
- Line ~310: Added btn-success styling class

---

#### 6. **components/ErrorViewer.css** (Updated)
```css
/* CHANGED: Added btn-success styling */

.btn-success {
  background-color: #27ae60;
  border-color: #229954;
  color: white;
}

.btn-success:hover {
  background-color: #229954;
  background-color: #1e8449;
}

/* Also adjusted action-bar button min-width */
.action-bar button {
  min-width: 150px;  /* from 200px */
}
```

**Changes:**
- Line ~200: Added .btn-success class
- Line ~350: Adjusted action-bar button width

---

## 📊 File Statistics

### New Files (2)
| File | Lines | Purpose |
|------|-------|---------|
| DocumentPreview.js | ~350 | Document preview component |
| DocumentPreview.css | ~450 | Styling for preview |
| **Total** | **~800** | **New component + styles** |

### Modified Files (6)
| File | Changes | Type |
|------|---------|------|
| ai_simulator.py | Enhanced error structure | Backend |
| api.py | +2 endpoints | Backend |
| App.js | Added preview step | Frontend |
| DocumentUpload.js | Removed auto-analyze | Frontend |
| ErrorViewer.js | Added preview button | Frontend |
| ErrorViewer.css | Added btn-success | Frontend |
| **Total** | **~100+ lines** | **Modifications** |

### Total
- **New files**: 2 (~800 lines)
- **Modified files**: 6 (~100+ lines)
- **Total additions**: ~900 lines
- **Breaking changes**: None

---

## 🔄 Backward Compatibility

✅ **Fully backward compatible**

- Old API endpoints still work
- Error structure enhanced but compatible
- New fields are optional
- No database migrations needed

---

## 📝 API Changes

### New Endpoints

```
GET /api/document/<session_id>
Response: {
  "paragraphs": [
    {
      "id": "para_0",
      "text": "Paragraph content...",
      "type": "paragraph"
    }
  ],
  "tables": [...]
}

GET /api/references/<session_id>
Response: {
  "regulations": [
    {
      "fileId": "reg_1",
      "fileName": "regulation.txt",
      "content": "..."
    }
  ],
  "references": [...]
}
```

### Enhanced Endpoints

```
GET /api/analyze/<session_id>
Response error objects now include:
{
  "startOffset": 0,
  "endOffset": 20,
  "reference": {
    "source": "regulation",
    "excerpt": "...",
    "location": "..."
  },
  "context": "..."
}
```

---

## 🎯 Impact Analysis

### Performance
- Minimal: New endpoints lazy-loaded
- Preview only loads on demand
- References fetched separately

### Compatibility
- No breaking changes
- All existing features work
- New features additive

### Security
- No changes to auth/session
- References handled safely
- Same upload restrictions

### Code Quality
- Follows existing patterns
- Consistent styling
- Proper error handling

---

## ✅ Testing Completed

- [x] Backend endpoints test
- [x] Frontend component rendering
- [x] Error highlighting logic
- [x] Reference data loading
- [x] Click interaction
- [x] Responsive layout
- [x] Integration test

---

## 🚀 Deployment Steps

1. Backup current code
2. Apply backend changes
3. Apply frontend changes
4. Restart services
5. Test preview workflow
6. Monitor logs

```bash
# No migration needed
# Just restart:
start_all.bat  # Windows
bash start_all.sh  # macOS/Linux
```

---

## 📖 Documentation Updated

- ✅ UPGRADE_V0.2.md (this folder)
- ✅ README.md (new features section)
- ✅ QUICKSTART.md (new workflow)

---

## 🐛 Bug Fixes

None - this is a feature release

---

## 📋 Checklist

- [x] Feature implemented
- [x] Code tested
- [x] Documentation updated
- [x] Backward compatibility verified
- [x] Performance verified
- [x] Security verified
- [x] Ready for deployment

---

**Version**: 0.2.0  
**Date**: April 8, 2026  
**Type**: Feature Release  
**Status**: ✅ Production Ready
