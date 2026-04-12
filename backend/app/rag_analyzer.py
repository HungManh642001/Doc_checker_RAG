"""
RAG Analyzer - Adapter giữa hiện tại Doc_checker và Doc_checker_RAG system
Tích hợp Qdrant vector store + Ollama LLM để thẩm định tài liệu
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Optional
import html2text
from docx import Document


# Import RAG components
from rag.knowledge_base.vector_db import get_or_build_index
from rag.knowledge_base.rules import load_rules
from rag.document_processing.chunker import chunk_html_table
from rag.audit_logic.audit_engine import run_audit
from rag.audit_logic.audit_models import KetQuaThamDinh, LoiThamDinh


class RAGAnalyzer:
    """
    RAG-based document analyzer wrapping Doc_checker_RAG system
    """
    
    def __init__(self):
        self.qdrant_index = None
        self.qdrant_client = None
        self.rules = None
        self.is_initialized = False
    
    def initialize_rag_system(self, reference_docs: List[str]) -> bool:
        """
        Initialize Qdrant index from reference documents
        
        Args:
            reference_docs: List of file paths to reference documents (DOCX)
        
        Returns:
            True if successful, False otherwise
        """
        try:
            print("[RAG] Initializing Qdrant index with reference documents...")
            
            # Load rules
            self.rules = load_rules()
            print(f"[RAG] Loaded rules")
            
            # Convert reference docs to HTML and build index
            all_html = ""
            for ref_doc in reference_docs:
                if os.path.exists(ref_doc):
                    html_content = self._docx_to_html(ref_doc)
                    all_html += f"\n\n<!-- Document: {os.path.basename(ref_doc)} -->\n"
                    all_html += html_content
                    print(f"[RAG] Added reference: {os.path.basename(ref_doc)}")
            
            # Build/get Qdrant index
            self.qdrant_index, self.qdrant_client = get_or_build_index()
            print(f"[RAG] Qdrant index initialized/loaded")
            
            self.is_initialized = True
            return True
            
        except Exception as e:
            print(f"[RAG] Error initializing: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def analyze_document(self, main_doc_path: str, top_k: int = 6) -> List[Dict]:
        """
        Analyze main document using RAG
        
        Args:
            main_doc_path: Path to DOCX document
            top_k: Number of similar documents to retrieve
        
        Returns:
            List of error objects
        """
        if not self.is_initialized:
            raise RuntimeError("RAG system not initialized. Call initialize_rag_system first")
        
        try:
            print("[RAG] Converting document to HTML...")
            html_content = self._docx_to_html(main_doc_path)
            
            print("[RAG] Chunking document...")
            chunks = chunk_html_table(html_content, chunk_size=1, header_rows_count=2)
            print(f"[RAG] Document split into {len(chunks)} chunks")
            
            all_errors = []
            
            # Process each chunk
            for idx, chunk in enumerate(chunks[:20]):  # Limit to first 20 chunks
                try:
                    print(f"[RAG] Analyzing chunk {idx + 1}/{min(20, len(chunks))}...")
                    
                    ket_qua = run_audit(
                        self.qdrant_index,
                        chunk,
                        self.rules,
                        top_k=top_k
                    )
                    
                    if ket_qua.danh_sach_loi:
                        # Transform results to app format
                        for error in ket_qua.danh_sach_loi:
                            app_error = self._transform_error(error, chunk, idx)
                            if app_error:
                                all_errors.append(app_error)
                        
                        print(f"[RAG] Chunk {idx + 1}: Found {len(ket_qua.danh_sach_loi)} errors")
                    else:
                        print(f"[RAG] Chunk {idx + 1}: No errors")
                
                except Exception as e:
                    print(f"[RAG] Error analyzing chunk {idx + 1}: {e}")
                    continue
            
            print(f"[RAG] Analysis complete: {len(all_errors)} total errors")
            return all_errors
        
        except Exception as e:
            print(f"[RAG] Analysis error: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _docx_to_html(self, docx_path: str) -> str:
        """Convert DOCX to HTML"""
        try:
            doc = Document(docx_path)
            html_parts = ['<html><body>']
            
            for element in doc.element.body:
                # Convert paragraphs
                if element.tag.endswith('p'):
                    text = ''.join([t.text for t in element.findall('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t')])
                    if text.strip():
                        html_parts.append(f'<p>{text}</p>')
                
                # Convert tables
                elif element.tag.endswith('tbl'):
                    html_parts.append(self._convert_table_to_html(element))
            
            html_parts.append('</body></html>')
            return '\n'.join(html_parts)
        
        except Exception as e:
            print(f"[RAG] Error converting DOCX: {e}")
            # Fallback: return plain text
            doc = Document(docx_path)
            text = '\n'.join([p.text for p in doc.paragraphs if p.text.strip()])
            return f"<html><body><p>{text.replace(chr(10), '</p><p>')}</p></body></html>"
    
    def _convert_table_to_html(self, table_element) -> str:
        """Convert Word table element to HTML"""
        html = '<table>'
        
        for row in table_element.findall('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tr'):
            html += '<tr>'
            for cell in row.findall('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tc'):
                cell_text = ''.join([
                    t.text for t in cell.findall('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t')
                ])
                html += f'<td>{cell_text}</td>'
            html += '</tr>'
        
        html += '</table>'
        return html
    
    def _transform_error(self, rag_error: LoiThamDinh, chunk: str, chunk_idx: int) -> Optional[Dict]:
        """
        Transform RAG error to app format
        
        Args:
            rag_error: Error from RAG (LoiThamDinh model)
            chunk: The HTML chunk analyzed
            chunk_idx: Index of chunk
        
        Returns:
            Error object in app format or None
        """
        try:
            # Build error details
            danh_sach_cac_loi = []
            for chi_tiet in rag_error.danh_sach_cac_loi:
                danh_sach_cac_loi.append({
                    'error_type': chi_tiet.error_type,
                    'reasoning': chi_tiet.reasoning,
                    'reference': rag_error.reference_location,
                    'severity': 'error'  # Default severity
                })
            
            return {
                'id': f'error_chunk{chunk_idx}_{len(danh_sach_cac_loi)}',
                'original_text': rag_error.original_text[:200],  # Truncate for display
                'elementId': f'chunk_{chunk_idx}',
                'elementType': 'chunk',
                'danh_sach_cac_loi': danh_sach_cac_loi,
                'suggestion': rag_error.suggestion,
                'reference_location': rag_error.reference_location,
                'reference_quote': rag_error.reference_quote,
                'severity': 'error'
            }
        
        except Exception as e:
            print(f"[RAG] Error transforming error: {e}")
            return None
    
    def cleanup(self):
        """Clean up resources"""
        if self.qdrant_client:
            try:
                self.qdrant_client.close()
                print("[RAG] Qdrant client closed")
            except:
                pass


# Global analyzer instance
_analyzer = None


def get_rag_analyzer() -> RAGAnalyzer:
    """Get or create global RAG analyzer"""
    global _analyzer
    if _analyzer is None:
        _analyzer = RAGAnalyzer()
    return _analyzer


def reset_rag_analyzer():
    """Reset global analyzer"""
    global _analyzer
    if _analyzer:
        _analyzer.cleanup()
    _analyzer = None
