# API Documentation

## Base URL
```
http://localhost:5000/api
```

## Endpoints

### 1. Upload Documents

**Endpoint**: `POST /api/upload`

**Description**: Upload documents for analysis (main document, reference documents, and regulations)

**Request**:
- **Method**: POST
- **Content-Type**: multipart/form-data
- **Parameters**:
  - `mainDocument` (file, required): Main DOCX file to analyze
  - `referenceDocuments[]` (file, optional): Reference DOCX files
  - `regulations[]` (file, optional): Regulation DOCX files

**Example**:
```bash
curl -X POST http://localhost:5000/api/upload \
  -F "mainDocument=@main.docx" \
  -F "referenceDocuments=@ref1.docx" \
  -F "regulations=@reg1.docx"
```

**Response** (200 OK):
```json
{
  "sessionId": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Documents uploaded successfully",
  "documentsCount": {
    "reference": 1,
    "regulations": 1
  }
}
```

**Error Responses**:
- 400: Main document is required
- 400: Main document must be .docx format
- 500: Internal server error

---

### 2. Analyze Document

**Endpoint**: `POST /api/analyze/<session_id>`

**Description**: Analyze the uploaded document and detect errors

**Request**:
- **Method**: POST
- **URL Parameters**:
  - `session_id`: Session ID from upload response

**Example**:
```bash
curl -X POST http://localhost:5000/api/analyze/550e8400-e29b-41d4-a716-446655440000
```

**Response** (200 OK):
```json
{
  "sessionId": "550e8400-e29b-41d4-a716-446655440000",
  "errors": [
    {
      "id": "error_AISimulator_0",
      "elementId": "para_0",
      "elementType": "paragraph",
      "type": "format",
      "position": 0,
      "errorText": "CÔNG TY",
      "message": "Định dạng công ty không nhất quán",
      "suggestion": "Công ty",
      "severity": "info"
    },
    {
      "id": "error_AISimulator_1",
      "elementId": "table_0_row_0_cell_0",
      "elementType": "table_cell",
      "type": "date_format",
      "message": "Ngày tháng năm không đúng định dạng",
      "suggestion": "Sử dụng định dạng DD/MM/YYYY",
      "severity": "warning",
      "errorText": "mẫu lỗi",
      "position": 0
    }
  ]
}
```

**Error Responses**:
- 404: Document not found
- 500: Internal server error

---

### 3. Apply Suggestions

**Endpoint**: `POST /api/apply-suggestions/<session_id>`

**Description**: Apply accepted corrections to the document

**Request**:
- **Method**: POST
- **Content-Type**: application/json
- **URL Parameters**:
  - `session_id`: Session ID from upload response
- **Body**:
```json
{
  "acceptedSuggestions": [
    {
      "elementId": "para_0",
      "newText": "Công ty ABC"
    },
    {
      "elementId": "table_0_row_0_cell_0",
      "newText": "08/04/2026"
    }
  ]
}
```

**Example**:
```bash
curl -X POST http://localhost:5000/api/apply-suggestions/550e8400-e29b-41d4-a716-446655440000 \
  -H "Content-Type: application/json" \
  -d '{
    "acceptedSuggestions": [
      {
        "elementId": "para_0",
        "newText": "Công ty ABC"
      }
    ]
  }'
```

**Response** (200 OK):
```json
{
  "message": "Corrections applied successfully",
  "downloadUrl": "/api/download/550e8400-e29b-41d4-a716-446655440000/main_corrected.docx"
}
```

**Error Responses**:
- 500: Internal server error

---

### 4. Download Corrected Document

**Endpoint**: `GET /api/download/<session_id>/<filename>`

**Description**: Download the corrected document with original formatting preserved

**Request**:
- **Method**: GET
- **URL Parameters**:
  - `session_id`: Session ID from upload response
  - `filename`: Target filename (e.g., "main_corrected.docx")

**Example**:
```bash
curl -O http://localhost:5000/api/download/550e8400-e29b-41d4-a716-446655440000/main_corrected.docx
```

**Response**: File download (application/vnd.openxmlformats-officedocument.wordprocessingml.document)

**Error Responses**:
- 404: File not found
- 500: Internal server error

---

### 5. Health Check

**Endpoint**: `GET /api/health`

**Description**: Check API server status

**Request**:
- **Method**: GET

**Example**:
```bash
curl http://localhost:5000/api/health
```

**Response** (200 OK):
```json
{
  "status": "ok"
}
```

---

## Error Code Reference

| Code | Meaning | Description |
|------|---------|-------------|
| 200 | OK | Request successful |
| 400 | Bad Request | Invalid request parameters |
| 404 | Not Found | Resource not found (document, session) |
| 500 | Internal Server Error | Server-side error |

---

## Session Management

- Each upload creates a unique session ID
- Sessions are stored in `backend/uploads/<session_id>/`
- Session includes:
  - `main.docx` - Main document
  - `ref_0.docx`, `ref_1.docx`, ... - Reference documents
  - `reg_0.docx`, `reg_1.docx`, ... - Regulation documents
  - `main_corrected.docx` - Corrected document (generated after applying suggestions)

---

## Error Format

All errors follow this structure:

```json
{
  "id": "error_<identifier>_<index>",
  "elementId": "para_0|table_0_row_0_cell_0",
  "elementType": "paragraph|table_cell",
  "type": "format|spacing|date_format|currency|number_mismatch|company_name",
  "message": "Human-readable error description",
  "suggestion": "Proposed correction",
  "severity": "error|warning|info",
  "errorText": "The actual error text",
  "position": 0
}
```

---

## Rate Limiting

Currently no rate limiting is applied. For production, consider implementing:
- Max 100 requests per minute per IP
- Max 10 concurrent uploads

---

## File Size Limits

- Maximum file size: **100 MB**
- Supported format: **DOCX only** (Microsoft Word 2007+)

---

## CORS Configuration

The API is configured to accept requests from:
- `http://localhost:3000` (development)
- Any origin (for development)

For production, update `app/__init__.py`:
```python
CORS(app, resources={r"/api/*": {"origins": ["https://yourdomain.com"]}})
```

---

## Examples

### Complete Workflow

```bash
# 1. Upload documents
SESSION=$(curl -s -X POST http://localhost:5000/api/upload \
  -F "mainDocument=@main.docx" \
  -F "regulations=@regulation.docx" \
  | jq -r '.sessionId')

# 2. Analyze document
curl -X POST http://localhost:5000/api/analyze/$SESSION

# 3. Apply corrections
curl -X POST http://localhost:5000/api/apply-suggestions/$SESSION \
  -H "Content-Type: application/json" \
  -d '{
    "acceptedSuggestions": [
      {"elementId": "para_0", "newText": "Công ty ABC"}
    ]
  }'

# 4. Download corrected file
curl -O http://localhost:5000/api/download/$SESSION/main_corrected.docx
```

---

## Technology Stack

- **Framework**: Flask 3.0.0
- **Document Processing**: python-docx 0.8.11
- **CORS**: Flask-CORS 4.0.0
- **Runtime**: Python 3.8+

---

**Last Updated**: April 2026
**Version**: 1.0
