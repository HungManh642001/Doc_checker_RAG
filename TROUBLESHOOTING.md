# Troubleshooting Guide

## Common Issues & Solutions

### 1. Backend Issues

#### Error: "ModuleNotFoundError: No module named 'flask'"

**Solution**:
```bash
cd backend
.\venv\Scripts\activate
pip install -r requirements.txt
```

#### Error: "Address already in use" (Port 5000)

**Solution**:
```bash
# Windows: Find and kill process on port 5000
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# macOS/Linux:
lsof -i :5000
kill -9 <PID>

# Or change Flask port in backend/run.py
port = 5001  # Change to different port
```

#### Error: "DOCX file corruption"

**Solution**:
- Ensure file is valid DOCX (can open in Word)
- Regenerate using `create_samples.py`
- Check file size (< 100MB)

---

### 2. Frontend Issues

#### Error: "npm install fails"

**Solution**:
```bash
cd frontend
# Clear cache
npm cache clean --force
# Delete dependencies
rm -rf node_modules package-lock.json
# Reinstall
npm install
```

#### Error: "Module not found in components"

**Solution**:
Check import paths:
```javascript
// Correct
import DocumentUpload from './components/DocumentUpload';

// Incorrect  
import DocumentUpload from './DocumentUpload';
```

#### Error: "React DevTools not working"

**Solution**:
```bash
# In frontend/.env
# Add:
SKIP_PREFLIGHT_CHECK=true
```

---

### 3. API Integration Issues

#### Error: "CORS policy - blocked"

**Solution**:
Verify CORS is enabled in `backend/app/__init__.py`:
```python
from flask_cors import CORS
CORS(app)  # Allow all origins in development
```

For production, restrict origins:
```python
CORS(app, resources={r"/api/*": {"origins": ["https://yourdomain.com"]}})
```

#### Error: "POST http://localhost:5000/api/upload 404"

**Solution**:
- Check backend is running on port 5000
- Verify no typos in API endpoint
- Test with: `curl http://localhost:5000/api/health`

#### Error: "File upload fails silently"

**Solution**:
1. Check browser console for errors (F12)
2. Check backend terminal for logs
3. Verify file size < 100MB
4. Ensure file is .docx format

---

### 4. Document Processing Issues

#### Error: "Table not recognized"

**Solution**:
```python
# In backend/app/document_processor.py
# Ensure table extraction handles nested elements:

for element in doc.element.body:
    if element.tag.endswith('tbl'):
        # Process table
```

#### Error: "Text formatting lost"

**Solution**:
```python
# Preserve run formatting when replacing text:
for run in paragraph.runs:
    run.text = new_text  # Keeps formatting (bold, italic, color)
    break  # Clear other runs
for run in paragraph.runs[1:]:
    run.text = ''
```

#### Error: "Special characters not displayed"

**Solution**:
Ensure UTF-8 encoding:
```python
# In backend files, use:
# -*- coding: utf-8 -*-
```

---

### 5. Performance Issues

#### Slow upload
- **Cause**: File too large or network slow
- **Solution**: 
  - Split large files
  - Compress before upload
  - Increase timeout

#### Slow analysis
- **Cause**: Large document with many patterns
- **Solution**:
  - Implement chunked processing
  - Cache analysis results
  - Optimize regex patterns

---

### 6. File Download Issues

#### Error: "File download fails"

**Solution**:
1. Check `main_corrected.docx` exists in session folder
2. Verify file permissions
3. Test with direct URL: `http://localhost:5000/api/download/<session_id>/main_corrected.docx`

#### Downloaded file is corrupted

**Solution**:
```python
# In backend/app/api.py
# Ensure proper headers for download:
return send_file(
    file_path,
    as_attachment=True,
    download_name='main_corrected.docx',
    mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
)
```

---

### 7. Session Management Issues

#### Error: "Session not found"

**Solution**:
- Session ID is case-sensitive
- Check session directory exists in `backend/uploads/`
- Session expires after browser close (implement persistence if needed)

#### Files left in /uploads

**Solution**:
Implement cleanup script:
```python
# cleanup.py
import os
import shutil
from datetime import datetime, timedelta

uploads_dir = 'backend/uploads'
max_age = timedelta(days=1)

for session_id in os.listdir(uploads_dir):
    path = os.path.join(uploads_dir, session_id)
    if os.path.isdir(path):
        age = datetime.now() - datetime.fromtimestamp(os.path.getctime(path))
        if age > max_age:
            shutil.rmtree(path)
```

---

## Debugging Tips

### Enable Verbose Logging

**Backend**:
```python
# In backend/run.py
import logging
logging.basicConfig(level=logging.DEBUG)
app.logger.setLevel(logging.DEBUG)
```

**Frontend**:
```javascript
// In src/App.js
axios.interceptors.request.use(config => {
  console.log('API Request:', config);
  return config;
});
```

### Use Browser DevTools

1. Open DevTools (F12)
2. Network tab: Monitor API requests
3. Console: View errors
4. Storage: Check localStorage/sessionStorage

### Test API Directly

```bash
# Using curl
curl -X POST http://localhost:5000/api/upload \
  -F "mainDocument=@sample.docx"

# Using Postman
# 1. Create new POST request
# 2. URL: http://localhost:5000/api/upload
# 3. Body: form-data
# 4. Add 'mainDocument' field with file
# 5. Send
```

---

## Getting Help

1. **Check documentation**:
   - [QUICKSTART.md](QUICKSTART.md)
   - [API_DOCUMENTATION.md](API_DOCUMENTATION.md)
   - [ARCHITECTURE.md](ARCHITECTURE.md)

2. **Search common issues**: Google error message

3. **Test with samples**: Run `create_samples.py`

4. **Check logs**: Review terminal output

5. **Isolate problem**: 
   - Test backend alone with curl
   - Test frontend with mock API
   - Test file processing separately

---

## Performance Checklist

- [ ] Backend running on port 5000
- [ ] Frontend running on port 3000
- [ ] CORS enabled
- [ ] Upload folder exists and is writable
- [ ] Python version 3.8+
- [ ] Node.js version 14+
- [ ] All dependencies installed
- [ ] No port conflicts
- [ ] Adequate disk space (for large files)
- [ ] Network connectivity between frontend and backend

---

## Still Having Issues?

1. **Check error message carefully** - Usually contains root cause
2. **Review recent changes** - What was modified last?
3. **Try minimal example** - Use `create_samples.py`
4. **Restart services** - Sometimes helps
5. **Check internet connection** - For API integrations
6. **Review logs** - Backend terminal and browser console (F12)

---

**Last Updated**: April 2026
**System Version**: 0.1.0
