# ✅ SETUP CHECKLIST - RAG Integration

## Bước Chuẩn Bị (Preparation)

- [ ] **Kiểm tra Python version**
  ```bash
  python --version  # Should be 3.8+
  ```

- [ ] **Kiểm tra Ollama installed**
  ```bash
  ollama --version
  ```

- [ ] **Ollama server running**
  ```bash
  ollama serve
  # Should show: "Listening on 127.0.0.1:11434"
  ```

- [ ] **Ollama models pulled**
  ```bash
  ollama pull qwen3:4b
  ollama pull nomic-embed-text
  ```

- [ ] **Kiểm tra paths**
  ```bash
  # Doc_checker folder exists
  cd D:\Workspace\VTX\Doc_checker
  
  # Doc_checker_RAG folder exists  
  cd D:\Workspace\VTX\Doc_checker_RAG
  ```

---

## Backend Setup (Installation)

- [ ] **Install base dependencies**
  ```bash
  cd Doc_checker/backend
  pip install -r requirements.txt
  ```

- [ ] **Install RAG dependencies**
  ```bash
  pip install llama-index
  pip install llama-index-vector-stores-qdrant
  pip install llama-index-embeddings-ollama
  pip install llama-index-llms-ollama
  pip install qdrant-client
  pip install python-docx
  pip install html2text
  ```

- [ ] **Verify imports**
  ```bash
  python -c "from app.rag_analyzer import RAGAnalyzer; print('✓ OK')"
  ```

- [ ] **Verify Flask app**
  ```bash
  python -c "from app import create_app; app = create_app(); print('✓ OK')"
  ```

---

## File Structure (Files Created)

### Backend Files

- [ ] `backend/app/rag_analyzer.py` - RAG adapter
  ```bash
  ls -la backend/app/rag_analyzer.py
  # Should exist and show ✓
  ```

- [ ] `backend/app/api_simplified.py` - Simplified API
  ```bash
  ls -la backend/app/api_simplified.py
  # Should exist and show ✓
  ```

- [ ] `backend/app/__init__.py` - Updated Flask app
  ```bash
  # Check it uses api_simplified by default
  grep -i "api_simplified" backend/app/__init__.py
  ```

### Frontend Files

- [ ] `frontend/src/AppSimplified.js` - New main app
  ```bash
  ls -la frontend/src/AppSimplified.js
  # Should exist
  ```

- [ ] `frontend/src/AppSimplified.css` - Styling
  ```bash
  ls -la frontend/src/AppSimplified.css
  ```

- [ ] `frontend/src/components/DocumentUploadSimplified.js`
  ```bash
  ls -la frontend/src/components/DocumentUploadSimplified.js
  ```

- [ ] `frontend/src/components/DocumentUploadSimplified.css`
  ```bash
  ls -la frontend/src/components/DocumentUploadSimplified.css
  ```

---

## Configuration (Setup)

### Update App.js

- [ ] **Backup old App.js**
  ```bash
  cd frontend/src
  mv App.js App.js.bak
  mv App.css App.css.bak
  ```

- [ ] **Copy simplified version**
  ```bash
  cp AppSimplified.js App.js
  cp AppSimplified.css App.css
  ```

- [ ] **Verify Index.js imports**
  ```bash
  # Check: index.js imports from ./App (not AppSimplified)
  grep "from.*App" frontend/src/index.js
  # Should show: import App from './App'
  ```

### Verify RAG Path

- [ ] **Check rag_analyzer.py path**
  ```bash
  # Open backend/app/rag_analyzer.py
  # Line ~13 should have:
  # rag_path = Path(r"D:\Workspace\VTX\Doc_checker_RAG\src")
  # If different, update it
  ```

### Verify Ollama Config

- [ ] **Check Doc_checker_RAG/src/config.py**
  ```bash
  # Should have:
  MODEL = "qwen3:4b"
  EMBEDDING_MODEL = "nomic-embed-text"
  OLLAMA_URL = "http://127.0.0.1:11434"
  ```

---

## Test API Endpoints (Verify API)

- [ ] **Start backend**
  ```bash
  cd backend
  python run.py
  # Should show: "Running on http://127.0.0.1:5000"
  ```

- [ ] **Test health endpoint**
  ```bash
  curl http://127.0.0.1:5000/api/health
  # Should return: {"status":"ok","sessions":0}
  ```

- [ ] **Browser test**
  ```bash
  # Open: http://127.0.0.1:5000/api/health
  # Should show JSON response
  ```

---

## Test Frontend (UI)

- [ ] **Install frontend dependencies**
  ```bash
  cd frontend
  npm install
  ```

- [ ] **Start frontend**
  ```bash
  npm start
  # Should open: http://localhost:3000
  # Check console for errors (F12)
  ```

- [ ] **Verify upload form**
  - [ ] See "Thẩm Định Tài Liệu" title
  - [ ] See upload boxes for main document
  - [ ] See option to add reference documents
  - [ ] See option to add rule documents
  - [ ] See "Bắt Đầu Thẩm Định" button

---

## Test End-to-End (Full Test)

### Prepare Test Files

- [ ] **Create test DOCX files or use samples**
  ```bash
  # Option 1: Use existing samples
  cd backend/app
  
  # Option 2: Create test files in:
  # Doc_checker_RAG/data/input_documents/
  ```

- [ ] **Keep terminal windows open**
  - Terminal 1: `ollama serve` (Ollama)
  - Terminal 2: `python run.py` (Backend)
  - Terminal 3: `npm start` (Frontend)

### Run Full Test

1. **Upload Test**
   - [ ] Open http://localhost:3000
   - [ ] Click upload box for main document
   - [ ] Select DOCX file
   - [ ] (Optional) Add reference documents
   - [ ] (Optional) Add rule documents
   - [ ] Click "Bắt Đầu Thẩm Định"

2. **Watch Progress**
   - [ ] Should see loading spinner
   - [ ] Backend terminal should show:
     ```
     [RAG] Initializing Qdrant index...
     [RAG] Converting document to HTML...
     [RAG] Chunking document...
     [RAG] Analyzing chunk 1/N...
     ```

3. **View Results**
   - [ ] Should see "Kết Quả Thẩm Định"
   - [ ] See error count
   - [ ] See list of errors (if any)

4. **Test Error Interaction**
   - [ ] Can expand error details
   - [ ] Can mark as Accept/Reject/Edit
   - [ ] Can modify suggestion text
   - [ ] Can click "Ghi Lại Sửa Chữa"

5. **Cleanup**
   - [ ] Click "Thẩm Định Tài Liệu Khác"
   - [ ] Should return to upload screen

---

## Troubleshooting (Fix Issues)

### If Test Fails

**Backend won't start**
- [ ] Check Python version: `python --version`
- [ ] Check dependencies: `pip list | grep llama`
- [ ] Check error message for missing imports

**API returns 500 error**
- [ ] Check backend terminal logs
- [ ] Look for `[RAG]` or `[Error]` messages
- [ ] Check RAG path is correct

**Ollama connection error**
- [ ] Check Ollama running: `ollama serve`
- [ ] Check URL in config.py: `http://127.0.0.1:11434`
- [ ] Run: `curl http://127.0.0.1:11434/api/tags`

**Model not found error**
- [ ] Pull models: `ollama pull qwen3:4b`
- [ ] Pull embeddings: `ollama pull nomic-embed-text`
- [ ] Verify: `ollama list`

**Frontend shows blank page**
- [ ] Check browser console (F12)
- [ ] Check frontend terminal for errors
- [ ] Try reload: Ctrl+Shift+R

**Analysis timeout**
- [ ] Document too large - try smaller file
- [ ] Ollama too slow - check Ollama terminal
- [ ] Increase timeout in rag_analyzer.py if needed

---

## Documentation Files (Optional Reading)

- [ ] **RAG_INTEGRATION_GUIDE.md** - Full setup guide
  ```bash
  # Read for detailed steps
  cat RAG_INTEGRATION_GUIDE.md
  ```

- [ ] **RAG_SYSTEM_INTEGRATION_SUMMARY.md** - Architecture overview
  ```bash
  # Read for understanding system design
  cat RAG_SYSTEM_INTEGRATION_SUMMARY.md
  ```

---

## Performance Baseline (Expected Times)

Record baseline to compare later:

- [ ] **First analysis (cold start)**
  - RAG init: _____ seconds
  - First chunk: _____ seconds
  - Total for 10 chunks: _____ minutes

- [ ] **Second analysis (warm cache)**
  - RAG init: _____ seconds
  - Average per chunk: _____ seconds

- [ ] **Memory usage**
  - Ollama: _____ MB
  - Backend: _____ MB
  - Frontend: _____ MB

---

## Production Readiness (Before Deploy)

- [ ] **Code review**
  - [ ] rag_analyzer.py reviewed
  - [ ] api_simplified.py reviewed
  - [ ] Error handling sufficient

- [ ] **Security**
  - [ ] No API keys in code
  - [ ] File upload validation working
  - [ ] Max file size enforced (100MB)

- [ ] **Logging**
  - [ ] Backend logs include [RAG] prefix
  - [ ] Error logs are captured
  - [ ] Can filter by session ID

- [ ] **Testing**
  - [ ] Test with various file sizes
  - [ ] Test with different Ollama models
  - [ ] Test error handling (break something)

- [ ] **Documentation**
  - [ ] User guide written
  - [ ] API documented
  - [ ] Troubleshooting guide created

---

## Environment Setup (Final)

Create`.env` file in backend/ (optional):

```bash
# backend/.env
USE_RAG_API=true
FLASK_ENV=development
FLASK_DEBUG=1
```

---

## Success Criteria ✅

You've successfully integrated RAG if:

✓ Backend starts without errors
✓ Frontend loads at http://localhost:3000
✓ Health endpoint returns `{"status":"ok"}`
✓ Can upload DOCX file
✓ Analysis completes and shows results
✓ Errors display in ErrorViewer
✓ Can accept/reject/edit suggestions
✓ All logs show `[RAG]` prefix (not errors)

---

## Next Steps After Success

1. **Test with real data**
   ```bash
   # Use actual regulation documents
   # Upload real documents needing review
   # Compare results with manual review
   ```

2. **Optimize performance**
   - Fine-tune Ollama settings
   - Add caching layer
   - Monitor CPU/Memory usage

3. **Collect feedback**
   - Test with users
   - Gather accuracy feedback
   - Identify improvement areas

4. **Production deployment**
   - Setup on cloud/server
   - Configure CI/CD
   - Setup monitoring

---

## Quick Reference Commands

```bash
# Start Ollama
ollama serve

# Pull models
ollama pull qwen3:4b
ollama pull nomic-embed-text

# Backend
cd Doc_checker/backend
python run.py

# Frontend
cd Doc_checker/frontend
npm start

# Test endpoints
curl http://127.0.0.1:5000/api/health

# View logs
# Ollama: Check terminal running "ollama serve"
# Backend: Check terminal running "python run.py"
# Frontend: Check F12 console in browser
```

---

## Support

If stuck on any step:

1. Check the relevant section above
2. Read full guide: `RAG_INTEGRATION_GUIDE.md`
3. Check logs (Ollama/Backend/Frontend)
4. Review architecture: `RAG_SYSTEM_INTEGRATION_SUMMARY.md`

