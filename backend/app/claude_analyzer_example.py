# claude_analyzer_example.py
"""
Ví dụ Integration Claude vào Doc_checker
Copy file này vào: backend/app/claude_analyzer.py

Sau đó update api.py:
    from app.claude_analyzer import ClaudeAnalyzer
    ai = ClaudeAnalyzer()  # Thay vì AISimulator()
"""

import os
import json
import re
import time
from anthropic import Anthropic
from typing import List, Dict

class ClaudeAnalyzer:
    """
    RAG-based document analyzer using Claude
    
    Setup:
    1. pip install anthropic
    2. Set ANTHROPIC_API_KEY in .env
    3. From app.claude_analyzer import ClaudeAnalyzer
    """
    
    def __init__(self, api_key: str = None):
        """Initialize Claude client"""
        api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment")
        
        self.client = Anthropic(api_key=api_key)
        self.model = "claude-3-5-sonnet-20241022"
        self.regulations = self._load_regulations()
    
    def _load_regulations(self) -> str:
        """Load Vietnamese regulations for context"""
        return """
═══════════════════════════════════════════════════════════════
QUYẾT ĐỊNH QUY ĐỊNH TIÊU CHUẨN TRÌNH BÀY TÀI LIỆU HỢP ĐỒNG
═══════════════════════════════════════════════════════════════

PHỤLỤC II - Thiết lập bội thập phân, ước thập phân của đơn vị đo
───────────────────────────────────────────────────────────────
Quy định về ký hiệu tiền tố và ký hiệu đơn vị:

Tiền tố "mega":
  ✓ Ký hiệu chính xác: M (chữ cái in hoa)
  ✗ Sai: m, mega, M_

Đơn vị "pascal":
  ✓ Ký hiệu chính xác: Pa (P in hoa, a thường)
  ✗ Sai: pa, Pa (nếu là lowercase), pA

Ví dụ ĐÚNG:
  ✓ 1 MPa (1 megapascal)
  ✓ 0,5 MPa
  ✓ 10 - 20 MPa

Ví dụ SAI:
  ✗ 1 Mpa (M nhiều hơn, pa thường)
  ✗ 1 mpa (m thường)
  ✗ 1 MPA (tất cả in hoa)


PHỤLỤC III - ĐƠN VỊ ĐO THEO THÔNG LỆ QUỐC TẾ
──────────────────────────────────────────────
Danh sách các đơn vị được phép sử dụng:

Độ dài:        mm, cm, m, km
Diện tích:     mm², cm², m², km²
Thể tích:      ml, l, cm³, m³
Khối lượng:    mg, g, kg
Thời gian:     s, min, h, day
Nhiệt độ:      K, °C, °F
Áp lực:        Pa, kPa, MPa, bar
Lực:           N, kN
Năng lượng:    J, kJ, MJ
Công suất:     W, kW, MW
Điện:          V, A, Ω, W, Hz

KHÔNG ĐƯỢC DÙNG:
  ✗ D, in, inch (không phải tiêu chuẩn)
  ✗ Mpa, mpa (ký hiệu sai)
  ✗ Các ký hiệu bất quy ước


PHỤLỤC V - TRÌNH BÀY ĐƠN VỊ ĐO PHÁP ĐỊNH
──────────────────────────────────────────
Cách thể hiện chính xác giá trị đại lượng đo:

Quy tắc 1: PHẢI CÓ ĐƠN VỊ ĐO
  ✓ "Kích thước: 3/8 mm" 
  ✓ "Áp lực: 10 bar"
  ✗ "Kích thước: D=3/8" (thiếu đơn vị)
  ✗ "Áp lực: 10" (thiếu đơn vị)

Quy tắc 2: KHOẢNG CÁCH GIỮA SỐ VÀ ĐƠN VỊ
  ✓ "10 mm" (có dấu cách)
  ✗ "10mm" (không dấu cách)
  ✗ "10 mm" (dấu cách to)

Quy tắc 3: DẤU PHẨY THẬP PHÂN
  ✓ "0,5 MPa" (dấu phẩy)
  ✗ "0.5 MPa" (dấu chấm)
  ✓ "1,25 m" (dấu phẩy)
  ✗ "1.25 m" (dấu chấm)

Quy tắc 4: RANGE VÀ KHOẢNG
  ✓ "3 - 9 mm" (có dấu cách trước sau dấu)
  ✓ "0,3 – 0,9 MPa" (dùng dấu ngắn hoặc dài)
  ✗ "3-9mm" (không dấu cách, không ĩ)
  ✗ "0.3-0.9Mpa" (sai format hoàn toàn)

Quy tắc 5: PHÂN SỐ
  ✓ "3/8 inch" (phân số + đơn vị)
  ✓ "0,375 inch" (dạng thập phân + đơn vị)
  ✗ "D=3/8" (thiếu đơn vị)
  ✗ "3/8" (không có đơn vị)
"""
    
    def analyze_document(self, content: Dict) -> List[Dict]:
        """
        Phân tích toàn bộ tài liệu
        
        Args:
            content: {paragraphs: [...], tables: [...]}
        
        Returns:
            List[error_objects]
        """
        all_errors = []
        error_counter = 0
        
        # Analyze paragraphs
        print("[Claude Analyzer] Processing paragraphs...")
        for para in content.get('paragraphs', []):
            if len(para['text'].strip()) > 5:
                para_errors = self._analyze_text(
                    para['text'],
                    para['id'],
                    'paragraph'
                )
                for error in para_errors:
                    error['id'] = f'error_{error_counter}'
                    error_counter += 1
                all_errors.extend(para_errors)
        
        # Analyze tables
        print("[Claude Analyzer] Processing tables...")
        for table in content.get('tables', []):
            for row in table.get('rows', []):
                for cell in row.get('cells', []):
                    if len(cell['text'].strip()) > 5:
                        cell_errors = self._analyze_text(
                            cell['text'],
                            cell['id'],
                            'table_cell'
                        )
                        for error in cell_errors:
                            error['id'] = f'error_{error_counter}'
                            error_counter += 1
                        all_errors.extend(cell_errors)
        
        print(f"[Claude Analyzer] Found {len(all_errors)} errors")
        return all_errors
    
    def _analyze_text(self, text: str, element_id: str, element_type: str) -> List[Dict]:
        """
        Phân tích 1 đoạn text với Claude
        
        Gọi Claude API để:
        1. Kiểm tra lỗi quy định
        2. Tạo đề xuất sửa chữa
        3. Trích dẫn quy định liên quan
        """
        
        # Tạo prompt
        prompt = self._create_analysis_prompt(text)
        
        print(f"[Claude] Analyzing: {text[:60]}...")
        
        try:
            # Gọi Claude
            message = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                system=f"""Bạn là chuyên gia kiểm tra tuân thủ quy định tài liệu hợp đồng Việt Nam.
                
Quy định hiện hành:
{self.regulations}

HƯỚNG DẪN PHÂN TÍCH:
1. Kiểm tra CHÍNH XÁC từng yêu cầu trong quy định
2. Chỉ báo lỗi nếu CHẮC CHẮN vi phạm
3. Trích dẫn cụ thể phần quy định
4. Đề xuất sửa chữa rõ ràng
5. Xếp mức độ: error (vi phạm), warning (cảnh báo), info (thông tin)

CHỈ TRẢ VỀ JSON, KHÔNG CÓ TEXT KHÁC.""",
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            # Extract response
            response_text = message.content[0].text
            print(f"[Claude] Response received")
            
            # Parse JSON
            errors = self._parse_claude_response(
                response_text,
                text,
                element_id,
                element_type
            )
            
            return errors
        
        except Exception as e:
            print(f"[Claude] Error: {e}")
            return []
    
    def _create_analysis_prompt(self, text: str) -> str:
        """Tạo prompt chi tiết cho Claude"""
        return f"""
PHÂN TÍCH TEXT SAU:
"{text}"

TRẢ VỀ JSON CÓ CẤU TRÚC NHƯ SAU:
{{
    "has_errors": true/false,
    "analysis": "Mô tả quá trình phân tích",
    "errors": [
        {{
            "error_type": "vi_pham_ky_hieu_don_vi",
            "description": "Mô tả chi tiết lỗi",
            "original": "Đoạn text có lỗi",
            "suggestion": "Cách sửa chính xác",
            "reference": "Phụ lục II - Thiết lập bội thập phân...",
            "quote": "Trích dẫn cụ thể từ quy định",
            "severity": "error"
        }},
        {{
            "error_type": "sai_dau_thap_phan",
            "description": "Dùng dấu chấm thay dấu phẩy",
            "original": "0.3",
            "suggestion": "0,3",
            "reference": "Phụ lục V - Trình bày đơn vị...",
            "quote": "...phải sử dụng dấu phẩy (,)",
            "severity": "error"
        }}
    ]
}}

LƯỚI ỤỨ:
- KHÔNG có text ngoài JSON
- Kiểm kỹ từng quy tắc
- Trích dẫn chính xác từ quy định
"""
    
    def _parse_claude_response(self, response_text: str, original_text: str, 
                               element_id: str, element_type: str) -> List[Dict]:
        """
        Parse Claude response và transform sang format của app
        """
        try:
            # Extract JSON từ response
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if not json_match:
                print("[Parse] No JSON found in response")
                return []
            
            json_str = json_match.group()
            data = json.loads(json_str)
            
            # Transform errors
            errors = []
            for err in data.get('errors', []):
                error_obj = {
                    'original_text': original_text[:100],
                    'elementId': element_id,
                    'elementType': element_type,
                    'danh_sach_cac_loi': [
                        {
                            'error_type': err.get('error_type', 'unknown'),
                            'reasoning': err.get('description', ''),
                            'reference': err.get('reference', ''),
                            'severity': err.get('severity', 'warning')
                        }
                    ],
                    'suggestion': err.get('suggestion', ''),
                    'reference_location': err.get('reference', ''),
                    'reference_quote': err.get('quote', ''),
                    'severity': err.get('severity', 'warning')
                }
                errors.append(error_obj)
            
            return errors
        
        except json.JSONDecodeError as e:
            print(f"[Parse] JSON decode error: {e}")
            print(f"[Parse] Raw response: {response_text[:200]}")
            return []
    
    def test_connection(self) -> bool:
        """Test Claude connection"""
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=100,
                messages=[
                    {"role": "user", "content": "Say 'connected'"}
                ]
            )
            print("✓ Claude connected successfully")
            return True
        except Exception as e:
            print(f"✗ Claude connection failed: {e}")
            return False


# ============================================
# TEST SCRIPT
# ============================================

if __name__ == '__main__':
    print("Testing Claude Analyzer")
    print("=" * 50)
    
    # Initialize
    analyzer = ClaudeAnalyzer()
    
    # Test connection
    if not analyzer.test_connection():
        print("Please check ANTHROPIC_API_KEY")
        exit(1)
    
    # Test analyze
    test_content = {
        'paragraphs': [
            {
                'id': 'para_0',
                'text': 'Kích thước: D=3/8'
            },
            {
                'id': 'para_1',
                'text': 'Áp suất: Bao dải 0.3 - 0.95 Mpa'
            }
        ],
        'tables': []
    }
    
    print("\nAnalyzing sample content...")
    errors = analyzer.analyze_document(test_content)
    
    print(f"\nFound {len(errors)} errors:")
    for error in errors:
        print(f"\n  Original: {error['original_text']}")
        print(f"  Suggestion: {error['suggestion']}")
        print(f"  Reference: {error['reference_location'][:50]}...")
