# INTEGRATION_STEPS.md

## 🚀 Hướng Dẫn Tích Hợp Claude vào App (Step-by-Step)

### Bước 0: Chuẩn Bị

#### 0.1 Lấy API Key

**Claude (KHUYÊN DÙNG)**:
1. Truy cập: https://console.anthropic.com
2. Đăng nhập hoặc tạo tài khoản
3. Navigate: Billing → Plans
4. Chọn plan (Pay-as-you-go hoặc Pro)
5. Navigate: API Keys
6. Click "Create Key"
7. Copy key (lưu an toàn, không chia sẻ)

**OpenAI (Alternative)**:
1. https://platform.openai.com
2. Login → API keys
3. "Create new secret key"

**Google Gemini (Alternative)**:
1. https://aistudio.google.com/app/apikey
2. "Create API key"

#### 0.2 Tạo File `.env`

```bash
# Tại folder: d:\Workspace\VTX\Doc_checker\backend\

# Claude
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxxx

# OpenAI (optional)
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxx

# Google Gemini (optional)
GOOGLE_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxx

# Flask
FLASK_ENV=development
FLASK_DEBUG=1
```

⚠️ **QUAN TRỌNG**: Thêm `.env` vào `.gitignore`:
```
# .gitignore
.env
*.pyc
__pycache__/
```

#### 0.3 Install Dependencies

```bash
cd backend

# Install Claude SDK
pip install anthropic

# Nếu dùng OpenAI
pip install openai

# Nếu dùng Gemini
pip install google-generativeai

# Load environment variables
pip install python-dotenv
```

---

### Bước 1: Copy Claude Analyzer

```bash
# File: backend/app/claude_analyzer_example.py
# Copy as: backend/app/claude_analyzer.py

cp backend/app/claude_analyzer_example.py backend/app/claude_analyzer.py
```

**Hoặc** rename trong VS Code:
- Click chuột phải `claude_analyzer_example.py`
- Rename → `claude_analyzer.py`

---

### Bước 2: Update api.py

**Thay thế import**:
```python
# OLD (hiện tại)
from app.ai_simulator import AISimulator, RAGKnowledgeBase

# NEW (Claude)
from app.claude_analyzer import ClaudeAnalyzer

# Hoặc sử dụng environment variable để chọn
import os
if os.getenv('USE_CLAUDE') == '1':
    from app.claude_analyzer import ClaudeAnalyzer as AIAnalyzer
else:
    from app.ai_simulator import AISimulator as AIAnalyzer
```

**Update endpoint `/analyze/<session_id>`**:

```python
# BEFORE:
@app.route('/api/analyze/<session_id>', methods=['POST'])
def analyze(session_id):
    try:
        # ... validation code ...
        
        # OLD
        ai = AISimulator()
        errors = ai.analyze_document(content)
        
        # ... rest of code ...

# AFTER:
@app.route('/api/analyze/<session_id>', methods=['POST'])
def analyze(session_id):
    try:
        # ... validation code ...
        
        # NEW - Claude
        try:
            ai = ClaudeAnalyzer()
            errors = ai.analyze_document(content)
        except ValueError:
            # Fallback nếu không có API key
            print("Claude API key not found, using pattern-based analyzer")
            from app.ai_simulator import AISimulator
            ai = AISimulator()
            errors = ai.analyze_document(content)
        
        # ... rest of code ...
```

---

### Bước 3: Update `.env` trong .flaskenv

```
# backend/.flaskenv
FLASK_APP=run.py
FLASK_ENV=development

# Kích hoạt Claude
USE_CLAUDE=1

# Hoặc để trống để dùng pattern
USE_CLAUDE=0
```

---

### Bước 4: Kiểm Tra Configuration

```bash
cd backend

# Test import
python -c "from app.claude_analyzer import ClaudeAnalyzer; print('✓ Import success')"

# Test connection
python -c "
from app.claude_analyzer import ClaudeAnalyzer
analyzer = ClaudeAnalyzer()
analyzer.test_connection()
"
```

**Output nếu thành công**:
```
✓ Claude connected successfully
```

**Output nếu sai**:
```
✗ Claude connection failed: 401 Client Error: Unauthorized
→ Check ANTHROPIC_API_KEY in .env
```

---

### Bước 5: Test End-to-End

#### 5.1 Start Server

```bash
cd backend
python run.py

# Output:
# WARNING in __main__: This is a development server. Do not use it in production.
# Running on http://127.0.0.1:5000
```

#### 5.2 Start Frontend

```bash
cd frontend
npm start

# Output:
# Compiled successfully!
# You can now view App in the browser at: http://localhost:3000
```

#### 5.3 Upload Test Document

1. Mở http://localhost:3000
2. Upload `sample_main.docx` (tài liệu chính)
3. Upload `sample_regulations.docx` (quy định)
4. Click "Tiếp Tục"

#### 5.4 Watch API Logs

Server logs sẽ hiển thị:
```
[Claude Analyzer] Processing paragraphs...
[Claude] Analyzing: Áp suất nước chứa: 0.3MPa...
[Claude] Response received
[Claude Analyzer] Found 3 errors
```

#### 5.5 Verify Results

- Lỗi được hiển thị trong UI
- Format JSON đúng
- Suggestions rõ ràng

---

### Bước 6: Optimization (Optional)

#### 6.1 Thêm Caching

```python
# backend/app/claude_analyzer.py

import hashlib
import json

class CachedClaudeAnalyzer(ClaudeAnalyzer):
    """Claude analyzer with caching"""
    
    def __init__(self):
        super().__init__()
        self.cache = {}  # In-memory cache
    
    def _analyze_text(self, text, element_id, element_type):
        # Create cache key
        cache_key = hashlib.md5(text.encode()).hexdigest()
        
        # Check cache
        if cache_key in self.cache:
            print(f"[Cache] Hit: {text[:40]}...")
            return self.cache[cache_key]
        
        # Analyze with Claude
        errors = super()._analyze_text(text, element_id, element_type)
        
        # Store in cache
        self.cache[cache_key] = errors
        print(f"[Cache] Miss: {text[:40]}...")
        
        return errors
```

#### 6.2 Thêm Rate Limiting

```python
import time

class RateLimitedClaudeAnalyzer(ClaudeAnalyzer):
    """Claude analyzer with rate limiting"""
    
    def __init__(self, requests_per_minute=10):
        super().__init__()
        self.requests_per_minute = requests_per_minute
        self.request_times = []
    
    def _analyze_text(self, text, element_id, element_type):
        # Limit requests
        now = time.time()
        self.request_times = [t for t in self.request_times if now - t < 60]
        
        if len(self.request_times) >= self.requests_per_minute:
            wait_time = 60 - (now - self.request_times[0])
            print(f"[RateLimit] Waiting {wait_time:.1f}s...")
            time.sleep(wait_time)
        
        self.request_times.append(now)
        return super()._analyze_text(text, element_id, element_type)
```

#### 6.3 Thêm Logging

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# In analyze_document:
logger.info(f"Started analyzing {len(content['paragraphs'])} paragraphs")
logger.debug(f"Regulations loaded: {len(self.regulations)} chars")
```

---

### Bước 7: Troubleshooting

#### 7.1 "ANTHROPIC_API_KEY not found"

```bash
# Check .env file exists
ls -la backend/.env

# Check key is set
echo $ANTHROPIC_API_KEY  # Linux/Mac
echo %ANTHROPIC_API_KEY%  # Windows

# If not set:
# Windows PowerShell:
$env:ANTHROPIC_API_KEY = "sk-ant-xxx"

# Windows CMD:
set ANTHROPIC_API_KEY=sk-ant-xxx

# Linux/Mac:
export ANTHROPIC_API_KEY=sk-ant-xxx
```

#### 7.2 "401 Unauthorized"

- API key sai hoặc expired
- Check: https://console.anthropic.com/account/keys
- Tạo key mới

#### 7.3 "Connection timeout"

- Check internet connection
- Check firewall blocking Anthropic API
- Test: `ping api.anthropic.com`

#### 7.4 JSON parsing error

Claude response format sai:
```python
# Add debugging:
print(f"[DEBUG] Response: {response_text[:500]}")

# Kiểm tra prompt format
# Ensure system prompt có "CHỈ TRẢ VỀ JSON"
```

---

### Bước 8: Production Deployment

#### 8.1 Environment Variables

```bash
# Trên server (e.g., Heroku, AWS EC2):
heroku config:set ANTHROPIC_API_KEY=sk-ant-xxx

# Hoặc trên AWS Lambda:
# Environment variables → Add ANTHROPIC_API_KEY

# Hoặc trên Docker:
# docker run -e ANTHROPIC_API_KEY=sk-ant-xxx myapp
```

#### 8.2 Error Handling

```python
try:
    ai = ClaudeAnalyzer()
    errors = ai.analyze_document(content)
except ValueError as e:
    logger.error(f"API key error: {e}")
    return {"error": "API configuration error"}, 500
except Exception as e:
    logger.error(f"Analysis failed: {e}")
    return {"error": "Analysis failed temporarily"}, 503
```

#### 8.3 Monitoring

```python
import time

start_time = time.time()
errors = ai.analyze_document(content)
duration = time.time() - start_time

logger.info(f"Analysis completed in {duration:.2f}s, {len(errors)} errors found")

# Alert if too slow
if duration > 60:
    logger.warning(f"Analysis took {duration:.2f}s (threshold: 60s)")
```

---

### Summary Integration

| Step | Action | Status |
|------|--------|--------|
| 0 | Get API key + Install SDK | Setup Phase |
| 1 | Copy claude_analyzer.py | Copy Phase |
| 2 | Update api.py imports | Code Phase |
| 3 | Configure .env | Config Phase |
| 4 | Test import | Validation Phase |
| 5 | Test end-to-end | Testing Phase |
| 6 | Add optimization | Optimization Phase (optional) |
| 7 | Troubleshoot issues | Debugging Phase |
| 8 | Deploy to production | Production Phase |

---

### Next: Alternative AI Providers

Sau khi Claude chạy được, bạn có thể dễ dàng:

**OpenAI (OpenAI_analyzer.py)**:
```python
from openai import OpenAI

class OpenAIAnalyzer:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    def analyze_document(self, content):
        # Similar to ClaudeAnalyzer, using GPT-4
        ...
```

**Google Gemini (gemini_analyzer.py)**:
```python
import google.generativeai as genai

class GeminiAnalyzer:
    def __init__(self):
        genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
        self.model = genai.GenerativeModel('gemini-pro')
    
    def analyze_document(self, content):
        # Similar to ClaudeAnalyzer, using Gemini
        ...
```

Rồi chỉ cần update import trong api.py - Frontend không cần sửa gì!

---

### Performance Notes

**Claude Pricing** (as of 2024):
- Input: $3 per 1M tokens
- Output: $15 per 1M tokens
- Typical document: ~2,000 tokens = $0.01 estimated

**Speed**:
- Average response: 2-5 seconds per paragraph
- 10 paragraphs ≈ 30 seconds

**Optimization**:
- Batch similar paragraphs
- Use caching for duplicate paragraphs
- Set `max_tokens=1024` để tránh response dài

