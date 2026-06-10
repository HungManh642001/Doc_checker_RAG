from docx import Document
from docx.shared import RGBColor, Pt
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
import re


class DocumentProcessor:
    """Handle DOCX document processing"""
    
    def extract_text_with_positions(self, file_path):
        """
        Extract text from DOCX with position information (paragraph, run position)
        Returns structured content with formatting preserved
        """
        try:
            doc = Document(file_path)
        except Exception as e:
            raise Exception(f"Failed to open document: {e}")
        
        content = {
            'paragraphs': [],
            'tables': [],
            'file_path': file_path
        }
        
        try:
            # Process all paragraphs
            for para_idx, para in enumerate(doc.paragraphs):
                para_content = {
                    'id': f'para_{para_idx}',
                    'text': para.text,
                    'runs': []
                }
                
                for run_idx, run in enumerate(para.runs):
                    para_content['runs'].append({
                        'id': f'para_{para_idx}_run_{run_idx}',
                        'text': run.text,
                        'bold': run.bold,
                        'italic': run.italic,
                        'font_name': run.font.name if run.font.name else 'Calibri'
                    })
                
                content['paragraphs'].append(para_content)
            
            # Process all tables
            for table_idx, table in enumerate(doc.tables):
                table_content = {
                    'id': f'table_{table_idx}',
                    'rows': []
                }
                
                for row_idx, row in enumerate(table.rows):
                    row_content = {
                        'id': f'table_{table_idx}_row_{row_idx}',
                        'cells': []
                    }
                    
                    for cell_idx, cell in enumerate(row.cells):
                        row_content['cells'].append({
                            'id': f'table_{table_idx}_row_{row_idx}_cell_{cell_idx}',
                            'text': cell.text
                        })
                    
                    table_content['rows'].append(row_content)
                
                content['tables'].append(table_content)
        
        except Exception as e:
            raise Exception(f"Failed to extract document content: {e}")
        
        return content
    
    def apply_corrections(self, input_path, output_path, corrections):
        """
        Apply corrections to the document while preserving formatting
        corrections: list of {elementId, type('text'/'table'), oldText, newText}
        """
        doc = Document(input_path)
        
        for correction in corrections:
            element_id = correction.get('elementId')
            new_text = correction.get('newText')
            
            # Parse element ID to locate the element
            if element_id.startswith('para_'):
                parts = element_id.split('_')
                if len(parts) == 2:
                    # It's a paragraph
                    para_idx = int(parts[1])
                    if para_idx < len(doc.paragraphs):
                        # Replace entire paragraph text while preserving formatting
                        para = doc.paragraphs[para_idx]
                        if para.runs:
                            # Replace first run and clear others
                            para.runs[0].text = new_text
                            for run in para.runs[1:]:
                                run.text = ''
                
                elif len(parts) == 4 and parts[2] == 'run':
                    # It's a specific run
                    para_idx = int(parts[1])
                    run_idx = int(parts[3])
                    if para_idx < len(doc.paragraphs):
                        para = doc.paragraphs[para_idx]
                        if run_idx < len(para.runs):
                            para.runs[run_idx].text = new_text
            
            elif element_id.startswith('table_'):
                parts = element_id.split('_')
                table_idx = int(parts[1])
                if len(parts) >= 4:
                    row_idx = int(parts[3])
                    cell_idx = int(parts[5]) if len(parts) > 5 else 0
                    
                    if table_idx < len(doc.tables):
                        table = doc.tables[table_idx]
                        if row_idx < len(table.rows):
                            row = table.rows[row_idx]
                            if cell_idx < len(row.cells):
                                cell = row.cells[cell_idx]
                                # Clear existing content
                                cell.text = new_text
        
        doc.save(output_path)
    
    def apply_text_corrections(
        self,
        input_path: str,
        output_path: str,
        text_corrections: list,
    ) -> int:
        """
        Áp dụng danh sách sửa lỗi dựa trên nội dung text (không cần element ID).
        Dùng cho kết quả từ RAG vì RAG trả về original_text, không trả về vị trí cấu trúc.

        Args:
            text_corrections: list of {'original_text': str, 'new_text': str}

        Returns:
            số lượng thay thế thực sự được thực hiện
        """
        doc = Document(input_path)
        applied = 0

        for corr in text_corrections:
            old = (corr.get('original_text') or '').strip()
            new = (corr.get('new_text') or '').strip()
            if not old or not new or old == new:
                continue

            # Duyệt paragraphs cấp cao nhất
            for para in doc.paragraphs:
                if old in para.text:
                    if self._replace_in_paragraph(para, old, new):
                        applied += 1

            # Duyệt tất cả các cell trong tất cả bảng
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        for para in cell.paragraphs:
                            if old in para.text:
                                if self._replace_in_paragraph(para, old, new):
                                    applied += 1

        doc.save(output_path)
        return applied

    def _replace_in_paragraph(self, para, old_text: str, new_text: str) -> bool:
        """
        Thay old_text bằng new_text trong paragraph.
        Thử thay trong từng run đơn (giữ định dạng), fallback sang merge toàn bộ runs.
        """
        # Ưu tiên: nếu old_text nằm gọn trong một run, chỉ sửa run đó
        for run in para.runs:
            if old_text in run.text:
                run.text = run.text.replace(old_text, new_text, 1)
                return True

        # Fallback: text rải rác nhiều runs — merge về run đầu, xoá phần còn lại
        full_text = para.text
        if old_text in full_text:
            replaced = full_text.replace(old_text, new_text, 1)
            if para.runs:
                para.runs[0].text = replaced
                for run in para.runs[1:]:
                    run.text = ''
            else:
                para.add_run(replaced)
            return True

        return False

    def highlight_error(self, doc, element_id, error_type='error'):
        """
        Highlight error in the document (for display purposes)
        error_type: 'error', 'warning', 'info'
        """
        color_map = {
            'error': RGBColor(255, 0, 0),      # Red
            'warning': RGBColor(255, 165, 0),  # Orange
            'info': RGBColor(0, 0, 255)        # Blue
        }
        
        color = color_map.get(error_type, RGBColor(255, 0, 0))
        
        # Parse element ID and highlight it
        # This would modify the document in memory for preview
        pass
