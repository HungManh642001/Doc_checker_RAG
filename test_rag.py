#!/usr/bin/env python3
"""
Test script for RAG-based analysis system
"""

from backend.app.document_processor import DocumentProcessor
from backend.app.ai_simulator import AISimulator
import json

def test_rag_analysis():
    """Test the RAG-like analysis pipeline"""
    
    print("=" * 70)
    print("RAG-BASED DOCUMENT ANALYSIS TEST")
    print("=" * 70)
    
    # Extract content from test document
    print("\n[1] Extracting content from sample document...")
    processor = DocumentProcessor()
    content = processor.extract_text_with_positions('samples/sample_main.docx')
    
    print(f"✓ Extracted {len(content.get('paragraphs', []))} paragraphs")
    print(f"✓ Extracted {len(content.get('tables', []))} tables")
    
    # Show extracted paragraphs
    print("\n[2] Extracted Paragraphs:")
    print("-" * 70)
    text_items = []
    for i, para in enumerate(content.get('paragraphs', [])[:8]):
        text = para['text']
        text_items.append(text)
        print(f"  Para {i}: {text[:70]}")
        if len(text) > 70:
            print(f"           {text[70:]}")
    
    # Perform RAG analysis
    print("\n[3] Running RAG-based Analysis...")
    print("-" * 70)
    ai = AISimulator()
    errors = ai.analyze_document(content)
    
    print(f"✓ Analysis complete: {len(errors)} issues found\n")
    
    # Display errors in detail
    if errors:
        for idx, error in enumerate(errors, 1):
            print(f"\n📋 ERROR #{idx}")
            print("-" * 70)
            print(f"Original Text: {error.get('original_text', 'N/A')}")
            print(f"Element Type: {error.get('elementType', 'unknown')}")
            print(f"Severity: {error.get('severity', 'unknown').upper()}")
            
            # Show all issues for this text
            print(f"\nIssues Found ({len(error.get('danh_sach_cac_loi', []))}):")
            for i, err in enumerate(error.get('danh_sach_cac_loi', []), 1):
                print(f"  {i}. {err.get('error_type', 'Unknown Error')}")
                print(f"     Reasoning: {err.get('reasoning', 'N/A')}")
                print(f"     Reference: {err.get('reference', 'N/A')[:70]}...")
            
            print(f"\nSuggestion: {error.get('suggestion', 'N/A')}")
            print(f"References: {error.get('reference_location', 'N/A')[:100]}...")
    else:
        print("✓ No errors found! Document complies with regulations.")
    
    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)
    
    return errors

if __name__ == '__main__':
    errors = test_rag_analysis()
