"""
RAG-like AI module for document analysis.
Simulates Retrieval-Augmented Generation by building a knowledge base from regulations
and analyzing documents against these regulations.
"""

import re
from typing import List, Dict


class RAGKnowledgeBase:
    """Simulates a vector database built from regulations"""
    
    def __init__(self):
        """Initialize with standard regulatory knowledge"""
        self.regulations = {
            'unit_notation': {
                'reference': 'Phụ lục II - Thiết lập bội thập phân, ước thập phân của đơn vị đo',
                'description': 'Quy định về ký hiệu đơn vị đo theo chuẩn quốc tế',
                'rules': [
                    {
                        'type': 'vi_pham_ky_hieu_don_vi',
                        'pattern': r'\b[A-Z]pa\b',
                        'description': 'Ký hiệu đơn vị pascal phải là "Pa" không phải "pa"',
                        'correct_form': 'MPa (Megapascal)',
                        'quote': 'Tiền tố "mega" được ký hiệu là "M", đơn vị "pascal" là "Pa"'
                    },
                    {
                        'type': 'vi_pham_ky_hieu_don_vi_khac',
                        'pattern': r'\b[a-z]+pa\b|\bMpa\b',
                        'description': 'Ký hiệu đơn vị phải tuân thủ chuẩn quốc tế',
                        'quote': 'Ký hiệu đơn vị phải viết đúng theo chuẩn SI'
                    }
                ]
            },
            'unit_display': {
                'reference': 'Phụ lục V - TRÌNH BÀY ĐƠN VỊ ĐO PHÁP ĐỊNH',
                'description': 'Quy định cách trình bày giá trị đại lượng đo',
                'rules': [
                    {
                        'type': 'thieu_don_vi_do',
                        'pattern': r'\d+(?:[,\.]\d+)?\s*(?:–|-)\s*\d+(?:[,\.]\d+)?(?!\s*(?:mm|cm|m|mm2|cm2|m2|bar|Pa|MPa|K|°C|°F|inch|in|mm/s|V|A|W|Hz|Ω))',
                        'description': 'Giá trị đại lượng đo phải kèm theo đơn vị đo',
                        'quote': 'Khi thể hiện giá trị đại lượng đo, ký hiệu đơn vị đo phải đặt sau trị số, giữa hai thành phần này phải cách nhau một dấu cách'
                    },
                    {
                        'type': 'sai_dau_thap_phan',
                        'pattern': r'\d+\.\d+',
                        'description': 'Dấu thập phân phải dùng dấu phẩy (,) không dùng dấu chấm (.)',
                        'quote': 'Biểu thị dấu thập phân của giá trị đại lượng đo phải sử dụng dấu phẩy (,) không sử dụng dấu chấm (.)'
                    }
                ]
            },
            'unit_format': {
                'reference': 'Phụ lục III - ĐƠN VỊ ĐO THEO THÔNG LỆ QUỐC TẾ',
                'description': 'Danh sách các đơn vị đo tiêu chuẩn được cho phép',
                'allowed_units': ['mm', 'cm', 'm', 'km', 'mm2', 'cm2', 'm2', 'mm3', 'cm3', 'ml', 'l', 
                                 'bar', 'Pa', 'MPa', 'K', '°C', '°F', 'kg', 'g', 'mg', 's', 'min', 'h',
                                 'V', 'A', 'W', 'Hz', 'Ω', 'inch', 'in'],
                'rules': [
                    {
                        'type': 'vi_pham_don_vi_tieu_chuan',
                        'description': 'Chỉ được sử dụng các đơn vị đo trong danh sách tiêu chuẩn',
                        'quote': 'Phụ lục III quy định các đơn vị đo tiêu chuẩn được phép sử dụng'
                    }
                ]
            }
        }
    
    def query_regulations(self, text: str) -> List[Dict]:
        """Query knowledge base for applicable regulations"""
        applicable_rules = []
        
        # Check against all regulation rules
        for reg_category, reg_info in self.regulations.items():
            for rule in reg_info.get('rules', []):
                pattern = rule.get('pattern')
                if pattern:
                    matches = re.finditer(pattern, text, re.IGNORECASE)
                    for match in matches:
                        applicable_rules.append({
                            'category': reg_category,
                            'rule_type': rule.get('type'),
                            'reference': reg_info.get('reference'),
                            'description': rule.get('description'),
                            'quote': rule.get('quote'),
                            'matched_text': match.group(),
                            'position': match.start()
                        })
        
        return applicable_rules


class AISimulator:
    """Simulate AI analysis for document errors using RAG architecture"""
    
    def __init__(self):
        self.knowledge_base = RAGKnowledgeBase()
        self.error_counter = 0
        self.analyzed_texts = {}
    
    def analyze_document(self, content: Dict) -> List[Dict]:
        """
        Analyze document content using RAG-like approach.
        Returns detailed error analysis with reasoning and references.
        """
        errors = []
        self.error_counter = 0
        self.analyzed_texts = {}
        
        # Analyze paragraphs
        for para in content.get('paragraphs', []):
            para_errors = self._analyze_text_with_rag(
                para['text'], para['id'], 'paragraph'
            )
            errors.extend(para_errors)
        
        # Analyze tables
        for table in content.get('tables', []):
            for row in table.get('rows', []):
                for cell in row.get('cells', []):
                    cell_errors = self._analyze_text_with_rag(
                        cell['text'], cell['id'], 'table_cell'
                    )
                    errors.extend(cell_errors)
        
        return errors
    
    def _analyze_text_with_rag(self, text: str, element_id: str, element_type: str) -> List[Dict]:
        """Analyze text using RAG knowledge base"""
        if not text or len(text.strip()) == 0:
            return []
        
        detailed_errors = []
        
        # Query knowledge base
        regulations = self.knowledge_base.query_regulations(text)
        
        if not regulations:
            return []
        
        # Group errors by the original text that matches
        error_groups = {}
        
        for reg in regulations:
            matched_text = reg['matched_text']
            
            if matched_text not in error_groups:
                error_groups[matched_text] = {
                    'original_text': matched_text,
                    'element_id': element_id,
                    'element_type': element_type,
                    'errors': [],
                    'references': []
                }
            
            # Add this error to the group
            error_item = {
                'error_type': reg['rule_type'],
                'reasoning': reg['description'],
                'reference': reg['reference'],
                'severity': self._determine_severity(reg['rule_type'])
            }
            
            error_group = error_groups[matched_text]
            error_group['errors'].append(error_item)
            
            if reg['reference'] not in error_group['references']:
                error_group['references'].append(reg['reference'])
        
        # Create detailed error entries
        for matched_text, group in error_groups.items():
            detailed_error = {
                'id': f'error_{self.error_counter}',
                'original_text': group['original_text'],
                'elementId': group['element_id'],
                'elementType': group['element_type'],
                'danh_sach_cac_loi': group['errors'],
                'suggestion': self._generate_suggestion(group['original_text'], group['errors']),
                'reference_location': '; '.join(group['references']),
                'reference_quote': self._extract_quotes(group['errors']),
                'severity': max([e['severity'] for e in group['errors']], 
                              key=lambda x: ['info', 'warning', 'error'].index(x))
            }
            
            detailed_errors.append(detailed_error)
            self.error_counter += 1
        
        return detailed_errors
    
    def _determine_severity(self, error_type: str) -> str:
        """Determine error severity based on type"""
        if 'vi_pham' in error_type or 'sai' in error_type:
            return 'error'
        elif 'thieu' in error_type:
            return 'warning'
        else:
            return 'info'
    
    def _generate_suggestion(self, text: str, errors: List[Dict]) -> str:
        """Generate correction suggestion based on errors"""
        suggestions = []
        
        for error in errors:
            error_type = error['error_type']
            
            if 'ky_hieu' in error_type and 'Mpa' in text:
                suggestions.append(f"Sửa thành: {text.replace('Mpa', 'MPa')}")
            elif 'dau_thap_phan' in error_type:
                fixed = text.replace('.', ',')
                suggestions.append(f"Sửa thành: {fixed} (dùng dấu phẩy thay dấu chấm)")
            elif 'thieu_don_vi' in error_type:
                suggestions.append(f"Thêm đơn vị đo phù hợp, ví dụ: {text} mm, {text} bar, v.v.")
        
        if suggestions:
            return suggestions[0]
        return f"Kiểm tra lại định dạng của '{text}'"
    
    def _extract_quotes(self, errors: List[Dict]) -> str:
        """Extract quotes from references"""
        quotes = []
        for error in errors:
            if 'reference' in error and error['reference']:
                quotes.append(error['reference'])
        return '; '.join(set(quotes)) if quotes else "Xem các quy định liên quan"
