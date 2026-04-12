# AI_PROVIDERS_COMPARISON.md

## 🔍 So Sánh 3 AI Providers cho RAG Document Analysis

### 1. **Claude** (Anthropic) - ✅ KHUYÊN DÙNG

#### Ưu Điểm
| Tiêu Chí | Chi Tiết |
|----------|--------|
| **Giá cả** | Rẻ nhất - $3/1M input tokens, $15/1M output |
| **Độ chính xác** | Cao - Hiểu context tốt, đặc biệt với tiếng Việt |
| **Context window** | 200K tokens - Có thể phân tích tài liệu dài |
| **Latency** | 2-5s trung bình |
| **API stability** | Rất ổn định |
| **Docs** | Rất chi tiết, dễ dùng |
| **Rate limit** | Hợp lý cho production |

#### Nhược Điểm
| Tiêu Chí | Chi Tiết |
|----------|--------|
| **Setup** | Cần API key từ console.anthropic.com |
| **Monitoring** | Ít dashboard detail hơn competitors |

#### Installation
```bash
pip install anthropic
```

#### Code Example
```python
from anthropic import Anthropic

client = Anthropic(api_key="sk-ant-...")
message = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1024,
    messages=[{"role": "user", "content": "..."}]
)
response = message.content[0].text
```

#### Pricing Estimate (Vietnamese Regulations Analysis)
- Average document: ~200 paragraphs
- Tokens per paragraph: ~100
- Total tokens: ~20,000
- **Cost per document: ~$0.06**

---

### 2. **OpenAI GPT-4** - Alternative #1

#### Ưu Điểm
| Tiêu Chí | Chi Tiết |
|----------|--------|
| **Độ chính xác** | Rất cao - Mạnh nhất trong 3 |
| **Ecosystem** | Có nhiều tools & integrations |
| **Popularity** | Phổ biến nhất, cộng đồng lớn |
| **Reliability** | Rất ổn định |
| **API** | Robust, well-tested |

#### Nhược Điểm
| Tiêu Chí | Chi Tiết |
|----------|--------|
| **Giá cả** | Đắt nhất - $0.01/1K input, $0.03/1K output (GPT-4) |
| **Context** | 128K tokens (nhỏ hơn Claude) |
| **Latency** | 3-7s trung bình |
| **Rate limit** | Thấp nếu không có usage tier |

#### Installation
```bash
pip install openai
```

#### Code Example
```python
from openai import OpenAI

client = OpenAI(api_key="sk-...")
response = client.chat.completions.create(
    model="gpt-4",
    temperature=0,
    max_tokens=1024,
    messages=[{"role": "user", "content": "..."}]
)
result = response.choices[0].message.content
```

#### Pricing Estimate
- Average document: ~200 paragraphs
- Tokens per paragraph: ~120
- Total tokens: ~24,000 input, ~12,000 output
- **Cost per document: ~$0.48** (GPT-4) / $0.05 (GPT-4 turbo)

---

### 3. **Google Gemini** - Alternative #2

#### Ưu Điểm
| Tiêu Chí | Chi Tiết |
|----------|--------|
| **Giá cả** | Miễn phí tier có sẵn (15 requests/min) |
| **Free tier** | Tốt cho testing/prototyping |
| **Context** | 200K tokens (bằng Claude) |
| **Integration** | Tốt với Google services (Sheets, Docs) |

#### Nhược Điểm
| Tiêu Chí | Chi Tiết |
|----------|--------|
| **Giá cả tier** | Paid tier đắt ($0.075/1M input) |
| **Latency** | 4-8s trung bình |
| **Accuracy** | Tốt nhưng không bằng GPT-4 |
| **Rate limit** | Thấp ở free tier |
| **Stability** | Ít ổn định hơn Claude/GPT-4 |

#### Installation
```bash
pip install google-generativeai
```

#### Code Example
```python
import google.generativeai as genai

genai.configure(api_key="...")
model = genai.GenerativeModel('gemini-pro')
response = model.generate_content("...")
result = response.text
```

#### Pricing Estimate
- **Free tier: Miễn phí** (15 req/min, tối đa 1M tokens/tháng)
- **Paid tier: ~$0.30** per document

---

## 📊 Bảng So Sánh Chi Tiết

| Tiêu Chí | Claude | GPT-4 | Gemini |
|----------|--------|-------|--------|
| **Giá** | 💚💚💚 | 🟡🟡🟡 | 💚💚💚 |
| **Accuracy** | 💚💚💚 | 💚💚💚💚 | 💚💚 |
| **Context** | 200K | 128K | 200K |
| **Speed** | 💚💚💚 | 🟡🟡 | 🟡 |
| **Stability** | 💚💚💚 | 💚💚💚 | 🟡🟡 |
| **Ease of Use** | 💚💚💚 | 💚💚 | 💚💚 |
| **Docs** | 💚💚💚 | 💚💚💚 | 🟡 |
| **Support** | 💚💚 | 💚💚💚 | 🟡 |

**Legend**: 💚💚💚 = Excellent, 🟡🟡 = Good, 🟡 = Fair

---

## 🎯 Khuyến Khích

### **Chọn Claude nếu**:
- ✅ Muốn balance giữa cost & performance
- ✅ App sẽ deploy production
- ✅ Cần phân tích tiếng Việt mạnh
- ✅ Tài liệu dài (>100K words)
- ✅ Budget hạn chế

### **Chọn GPT-4 nếu**:
- ✅ Accuracy là priority #1
- ✅ Đã dùng OpenAI API trước
- ✅ Budget không eo hẹp
- ✅ Cộng đồng lớn & cần support

### **Chọn Gemini nếu**:
- ✅ Prototyping / testing phase
- ✅ Don't have budget yet
- ✅ Using Google Workspace already
- ✅ Low volume requirements

---

## 📈 Cost Analysis for Document Checker

**Giả sử**: 100 documents/month, ~200 paragraphs/document

| Provider | Per Doc | Total/Month | Annual |
|----------|---------|------------|--------|
| **Claude** | $0.06 | $6 | $72 |
| **GPT-4** | $0.48 | $48 | $576 |
| **GPT-4 Turbo** | $0.05 | $5 | $60 |
| **Gemini Free** | $0 | $0 | $0 |
| **Gemini Paid** | $0.30 | $30 | $360 |

**Kết luận**: Claude cho **SẢN XUẤT**, Gemini cho **TESTING**

---

## 🔄 Chuyển Đổi Providers

Nhờ có interface chung, chuyển đổi rất dễ:

### Từ Claude → GPT-4
```python
# File: backend/app/openai_analyzer.py
from openai import OpenAI

class OpenAIAnalyzer(BaseAnalyzer):  # Inherit interface
    def analyze_document(self, content):
        # Same input/output format
        # Just use different client
        ...

# Update api.py
from app.openai_analyzer import OpenAIAnalyzer
ai = OpenAIAnalyzer()  # Drop-in replacement
```

### Setup Multiple Providers
```python
# backend/app/ai_factory.py
def get_analyzer(provider: str):
    if provider == 'claude':
        from app.claude_analyzer import ClaudeAnalyzer
        return ClaudeAnalyzer()
    elif provider == 'openai':
        from app.openai_analyzer import OpenAIAnalyzer
        return OpenAIAnalyzer()
    elif provider == 'gemini':
        from app.gemini_analyzer import GeminiAnalyzer
        return GeminiAnalyzer()

# api.py
provider = os.getenv('AI_PROVIDER', 'claude')
ai = get_analyzer(provider)
```

---

## 🧪 Testing Multiple Providers

```python
# test_all_providers.py
import os
from pathlib import Path

providers_to_test = ['claude', 'openai', 'gemini']

for provider in providers_to_test:
    print(f"\n{'='*50}")
    print(f"Testing {provider.upper()}")
    print('='*50)
    
    # Set environment
    os.environ['AI_PROVIDER'] = provider
    
    # Initialize analyzer
    from app.ai_factory import get_analyzer
    analyzer = get_analyzer(provider)
    
    # Run test
    test_content = {
        'paragraphs': [
            {'id': 'p1', 'text': 'Áp lực: 0.5Mpa'}
        ],
        'tables': []
    }
    
    errors = analyzer.analyze_document(test_content)
    print(f"✓ {provider}: Found {len(errors)} errors")
```

---

## 📋 Migration Checklist

Nếu muốn chuyển provider:

- [ ] Copy new analyzer file (e.g., openai_analyzer.py)
- [ ] Create API key từ provider
- [ ] Add key vào .env
- [ ] Update ai_factory.py hoặc api.py
- [ ] Run test suite
- [ ] Monitor cost for 1 week
- [ ] Production deployment

---

## 🚨 Important Notes

### Rate Limits

```python
# Rate limiting by provider
RATE_LIMITS = {
    'claude': 
        100_000,      # tokens/minute
        10,            # requests/minute
    'openai': 
        90_000,        # tokens/minute (tier-dependent)
        3_000,         # requests/minute
    'gemini': 
        60,            # requests/minute (free)
        1_000_000,     # tokens/month (free)
}
```

### Error Handling

```python
def analyze_with_fallback(content):
    """Try Claude first, fallback to pattern-based"""
    try:
        ai = ClaudeAnalyzer()
        return ai.analyze_document(content)
    except Exception as e:
        logger.error(f"Claude failed: {e}")
        logger.info("Falling back to pattern-based analyzer")
        from app.ai_simulator import AISimulator
        return AISimulator().analyze_document(content)
```

### Monitoring by Provider

```python
import logging

class ProviderMonitor:
    def __init__(self, provider: str):
        self.provider = provider
        self.costs = 0
        self.errors = 0
        self.latency = []
        self.logger = logging.getLogger(f"provider.{provider}")
    
    def log_request(self, input_tokens, output_tokens, latency, success):
        if success:
            self.costs += self._calculate_cost(input_tokens, output_tokens)
            self.latency.append(latency)
        else:
            self.errors += 1
    
    def daily_report(self):
        avg_latency = sum(self.latency) / len(self.latency) if self.latency else 0
        self.logger.info(
            f"{self.provider} daily: "
            f"Cost=${self.costs:.2f}, "
            f"Errors={self.errors}, "
            f"Avg latency={avg_latency:.2f}s"
        )
```

---

## 🎓 Recommendation Summary

**Tóm tắt**:

1. **Start with Claude** - Giá tốt, performance tốt
2. **Monitor costs** - Track usage từ tháng đầu
3. **Setup fallback** - Auto fallback nếu API fail
4. **Keep flexibility** - Dùng ai_factory để dễ chuyển đổi
5. **Test all 3** - Xem cái nào best fit với data của bạn

**Vietnam Reg Doc Analyzer**:
- Use **Claude** for production
- Use **Gemini** free tier for testing
- GPT-4 chỉ nếu cần accuracy tuyệt đối

