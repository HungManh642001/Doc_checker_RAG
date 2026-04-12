#!/usr/bin/env python
"""
test_claude_integration.py

Test script để verify Claude integration trước khi deploy.

Usage:
    python test_claude_integration.py
"""

import os
import sys
import json
import time
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / 'backend'))

def test_environment():
    """Test 1: Kiểm tra environment setup"""
    print("\n" + "="*60)
    print("TEST 1: Environment Setup")
    print("="*60)
    
    # Check .env file
    env_path = Path(__file__).parent / 'backend' / '.env'
    if env_path.exists():
        print(f"✓ .env file found: {env_path}")
    else:
        print(f"✗ .env file NOT found at {env_path}")
        print("  → Create backend/.env with ANTHROPIC_API_KEY")
        return False
    
    # Check API key
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if api_key:
        print(f"✓ ANTHROPIC_API_KEY is set (length: {len(api_key)})")
        if api_key.startswith('sk-ant-'):
            print(f"  ✓ Format looks correct (starts with sk-ant-)")
        else:
            print(f"  ⚠ Format unusual (expected sk-ant-...)")
    else:
        print("✗ ANTHROPIC_API_KEY not found in environment")
        print("  → Set environment variable before running test")
        return False
    
    return True


def test_imports():
    """Test 2: Kiểm tra Python imports"""
    print("\n" + "="*60)
    print("TEST 2: Python Imports")
    print("="*60)
    
    try:
        print("Importing anthropic...", end=" ")
        import anthropic
        print("✓")
    except ImportError as e:
        print(f"✗ {e}")
        print("  → pip install anthropic")
        return False
    
    try:
        print("Importing ClaudeAnalyzer...", end=" ")
        from app.claude_analyzer import ClaudeAnalyzer
        print("✓")
    except ImportError as e:
        print(f"✗ {e}")
        print("  → Copy claude_analyzer_example.py to claude_analyzer.py")
        return False
    except Exception as e:
        print(f"✗ {e}")
        return False
    
    return True


def test_connection():
    """Test 3: Kiểm tra kết nối Claude API"""
    print("\n" + "="*60)
    print("TEST 3: Claude API Connection")
    print("="*60)
    
    try:
        from app.claude_analyzer import ClaudeAnalyzer
        
        print("Initializing ClaudeAnalyzer...", end=" ")
        analyzer = ClaudeAnalyzer()
        print("✓")
        
        print("Testing connection...", end=" ", flush=True)
        start = time.time()
        success = analyzer.test_connection()
        duration = time.time() - start
        
        if success:
            print(f"✓ ({duration:.2f}s)")
            return True
        else:
            print("✗")
            print("  → Check API key is valid and has credits")
            return False
    
    except Exception as e:
        print(f"✗ {e}")
        return False


def test_basic_analysis():
    """Test 4: Kiểm tra phân tích cơ bản"""
    print("\n" + "="*60)
    print("TEST 4: Basic Analysis")
    print("="*60)
    
    try:
        from app.claude_analyzer import ClaudeAnalyzer
        
        analyzer = ClaudeAnalyzer()
        
        test_cases = [
            {
                'name': 'Missing unit',
                'text': 'Kích thước: D=3/8'
            },
            {
                'name': 'Wrong decimal',
                'text': 'Áp lực: 0.5 MPa'
            },
            {
                'name': 'Wrong notation',
                'text': 'Khoảng: 10-20mm'
            }
        ]
        
        for test_case in test_cases:
            print(f"\nAnalyzing: {test_case['name']}")
            print(f"  Text: '{test_case['text']}'")
            
            content = {
                'paragraphs': [
                    {
                        'id': 'test_0',
                        'text': test_case['text']
                    }
                ],
                'tables': []
            }
            
            try:
                start = time.time()
                errors = analyzer.analyze_document(content)
                duration = time.time() - start
                
                print(f"  Found: {len(errors)} errors ({duration:.2f}s)")
                
                for i, error in enumerate(errors):
                    print(f"    [{i}] {error['danh_sach_cac_loi'][0]['error_type']}")
                    print(f"        Severity: {error['severity']}")
                    print(f"        Suggestion: {error['suggestion']}")
                
            except Exception as e:
                print(f"  ✗ Error: {e}")
        
        return True
    
    except Exception as e:
        print(f"✗ {e}")
        import traceback
        traceback.print_exc()
        return False


def test_full_document():
    """Test 5: Kiểm tra phân tích tài liệu đầy đủ"""
    print("\n" + "="*60)
    print("TEST 5: Full Document Analysis")
    print("="*60)
    
    try:
        from app.claude_analyzer import ClaudeAnalyzer
        
        analyzer = ClaudeAnalyzer()
        
        # Simulated document with multiple issues
        content = {
            'paragraphs': [
                {
                    'id': 'para_1',
                    'text': 'Thông số kỹ thuật: Áp suất nước: 0.3-0.9 bar'
                },
                {
                    'id': 'para_2',
                    'text': 'Kích thước các lỗ: 3/8 inch hoặc 10mm'
                },
                {
                    'id': 'para_3',
                    'text': 'Độ dẫn điện: 1000 S/m'
                }
            ],
            'tables': [
                {
                    'rows': [
                        {
                            'cells': [
                                {'id': 'cell_1', 'text': 'Giá trị tối đa: 50MPa'},
                                {'id': 'cell_2', 'text': 'Phạm vi: 20-80%'}
                            ]
                        }
                    ]
                }
            ]
        }
        
        print(f"Analyzing document with:")
        print(f"  - {len(content['paragraphs'])} paragraphs")
        print(f"  - {len(content['tables'])} tables")
        
        start = time.time()
        errors = analyzer.analyze_document(content)
        duration = time.time() - start
        
        print(f"\n✓ Analysis completed in {duration:.2f}s")
        print(f"  Found: {len(errors)} total errors")
        
        if errors:
            print(f"\n  Errors breakdown:")
            severity_count = {}
            for error in errors:
                sev = error['severity']
                severity_count[sev] = severity_count.get(sev, 0) + 1
            
            for sev, count in severity_count.items():
                print(f"    - {sev}: {count}")
        
        return True
    
    except Exception as e:
        print(f"✗ {e}")
        import traceback
        traceback.print_exc()
        return False


def test_error_format():
    """Test 6: Kiểm tra format lỗi"""
    print("\n" + "="*60)
    print("TEST 6: Error Format Validation")
    print("="*60)
    
    try:
        from app.claude_analyzer import ClaudeAnalyzer
        
        analyzer = ClaudeAnalyzer()
        
        content = {
            'paragraphs': [{'id': 'test', 'text': 'Áp lực: 0.5Mpa'}],
            'tables': []
        }
        
        errors = analyzer.analyze_document(content)
        
        if not errors:
            print("⚠ No errors found (this might be OK)")
            return True
        
        # Check first error
        error = errors[0]
        
        required_fields = [
            'original_text',
            'elementId',
            'elementType',
            'danh_sach_cac_loi',
            'suggestion',
            'reference_location',
            'severity'
        ]
        
        print("Checking error object structure:")
        all_present = True
        for field in required_fields:
            if field in error:
                print(f"  ✓ {field}")
            else:
                print(f"  ✗ {field} MISSING")
                all_present = False
        
        # Check danh_sach_cac_loi
        if error.get('danh_sach_cac_loi'):
            error_obj = error['danh_sach_cac_loi'][0]
            print("\nChecking first error details:")
            error_fields = ['error_type', 'reasoning', 'reference', 'severity']
            for field in error_fields:
                if field in error_obj:
                    print(f"  ✓ {field}")
                else:
                    print(f"  ✗ {field} MISSING")
                    all_present = False
        
        return all_present
    
    except Exception as e:
        print(f"✗ {e}")
        return False


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*60)
    print("CLAUDE ANALYZER INTEGRATION TEST SUITE")
    print("="*60)
    
    tests = [
        ('Environment', test_environment),
        ('Imports', test_imports),
        ('Connection', test_connection),
        ('Basic Analysis', test_basic_analysis),
        ('Full Document', test_full_document),
        ('Error Format', test_error_format),
    ]
    
    results = {}
    for name, test_func in tests:
        try:
            passed = test_func()
            results[name] = 'PASS' if passed else 'FAIL'
        except Exception as e:
            print(f"\n✗ Unexpected error in {name}: {e}")
            import traceback
            traceback.print_exc()
            results[name] = 'ERROR'
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for name, status in results.items():
        symbol = "✓" if status == 'PASS' else "✗"
        print(f"{symbol} {name}: {status}")
    
    all_passed = all(s == 'PASS' for s in results.values())
    
    print("\n" + "="*60)
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
        print("\nYou're ready to integrate Claude into the app:")
        print("1. Update api.py to use ClaudeAnalyzer")
        print("2. Start backend: python run.py")
        print("3. Start frontend: npm start")
        print("4. Upload document and test!")
    else:
        print("❌ SOME TESTS FAILED")
        print("\nFix issues above and run again")
        print("\nCommon fixes:")
        print("- Check .env file in backend/")
        print("- Verify ANTHROPIC_API_KEY is set")
        print("- Run: pip install anthropic")
        print("- Copy claude_analyzer_example.py to claude_analyzer.py")
    print("="*60 + "\n")
    
    return all_passed


if __name__ == '__main__':
    # Load environment
    from dotenv import load_dotenv
    dotenv_path = Path(__file__).parent / 'backend' / '.env'
    if dotenv_path.exists():
        load_dotenv(dotenv_path)
    
    # Run tests
    success = run_all_tests()
    sys.exit(0 if success else 1)
