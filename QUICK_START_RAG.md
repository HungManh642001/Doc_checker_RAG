# 🚀 QUICK START - RAG Integration (5 Minutes)

## ⚡ TL;DR - Just Run These Commands

### Terminal 1: Ollama
```bash
ollama serve
```

### Terminal 2: Backend
```bash
cd D:\Workspace\VTX\Doc_checker\backend
pip install llama-index qdrant-client python-docx html2text -q
python run.py
```

### Terminal 3: Frontend
```bash
cd D:\Workspace\VTX\Doc_checker\frontend
npm start
```

### Terminal 4: Test
```bash
# Open browser
http://localhost:3000

# Upload DOCX file
# Click "Bắt Đầu Thẩm Định"
# Wait for results
```

---

## ✅ What Was Changed

**Backend:**
- ✅ `app/rag_analyzer.py` - Connects to your RAG system
- ✅ `app/api_simplified.py` - Simpler API endpoints
- ✅ `app/__init__.py` - Updated Flask config

**Frontend:**
- ✅ Changed `App.js` to simplified version (no preview page)
- ✅ New `DocumentUploadSimplified.js` component
- ✅ Keeps `ErrorViewer.js` for displaying errors

---

## 📊 What Happens Now

```
User uploads DOCX + Reference docs
         ↓
RAG system analyzes document
         ↓
Shows errors with ErrorViewer
         ↓
User accepts/rejects suggestions
         ↓
Done!
```

---

## 🎯 Files to Know

| File | What It Does |
|------|-------------|
| `backend/app/rag_analyzer.py` | Talks to your RAG system |
| `backend/app/api_simplified.py` | Simple API: just upload & analyze |
| `frontend/src/App.js` | Upload page → Results page |
| `frontend/src/components/ErrorViewer.js` | Shows errors (unchanged) |
| `Doc_checker_RAG/` | Your RAG system (unchanged) |

---

## 🔧 If Something Breaks

| Error | Fix |
|-------|-----|
| `ImportError: rag_analyzer` | File not created - check `app/` folder |
| `Ollama connection error` | Run `ollama serve` in terminal 1 |
| `Model not found` | Run `ollama pull qwen3:4b` |
| `Upload button does nothing` | Check backend logs for errors |
| `Blank page` | Check browser console (F12) |

---

## 📚 More Info

- **Detailed Guide:** `RAG_INTEGRATION_GUIDE.md`
- **Architecture:** `RAG_SYSTEM_INTEGRATION_SUMMARY.md`
- **Full Checklist:** `SETUP_CHECKLIST.md`

---

## 🎉 You're Done!

The system is now integrated. Keep terminal windows open and:

1. Go to http://localhost:3000
2. Upload a DOCX file
3. Wait for analysis
4. Review errors
5. Done! 🎊

---

## 💡 Key Differences from Before

| Aspect | Before | After |
|--------|--------|-------|
| Upload page | Has document preview | Just upload, no preview |
| Steps | Upload → Preview → Analyze → Review | Upload → Analyze → Review |
| Pages | 4 screens | 2-3 screens |
| Accuracy | Pattern matching | RAG + Ollama AI |
| Speed | Seconds | Minutes (but smarter) |

---

## 🔄 Reset to Original (If Needed)

```bash
# Restore old App.js
cd frontend/src
mv App.js.bak App.js
mv App.css.bak App.css

# Restart frontend
npm start
```

---

Questions? Check **`SETUP_CHECKLIST.md`** for troubleshooting.

