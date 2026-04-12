"""
Testing utilities - Simulate different error scenarios
"""

import json
from typing import List, Dict


class TestScenarioManager:
    """Manage test scenarios for different document types"""
    
    @staticmethod
    def get_legal_contract_errors() -> List[Dict]:
        """Simulate errors for legal contract documents"""
        return [
            {
                "id": "test_1",
                "elementId": "para_0",
                "elementType": "paragraph",
                "type": "format",
                "message": "Tên công ty không tuân thủ quy định",
                "suggestion": "Công ty tnhh ABC",
                "severity": "error",
                "errorText": "CÔNG TY TNHH ABC"
            },
            {
                "id": "test_2",
                "elementId": "para_2",
                "elementType": "paragraph",
                "type": "spacing",
                "message": "Khoảng trắng thừa",
                "suggestion": "Ông Nguyễn Văn A",
                "severity": "warning",
                "errorText": "Ông  Nguyễn  Văn  A"
            },
            {
                "id": "test_3",
                "elementId": "table_0_row_1_cell_0",
                "elementType": "table_cell",
                "type": "currency",
                "message": "Ký hiệu tiền tệ không nhất quán",
                "suggestion": "1.000.000 VND",
                "severity": "info",
                "errorText": "$1000000"
            }
        ]
    
    @staticmethod
    def get_report_errors() -> List[Dict]:
        """Simulate errors for report documents"""
        return [
            {
                "id": "test_1",
                "elementId": "para_5",
                "elementType": "paragraph",
                "type": "date_format",
                "message": "Định dạng ngày không chuẩn",
                "suggestion": "08/04/2026",
                "severity": "warning",
                "errorText": "2026-04-08"
            },
            {
                "id": "test_2",
                "elementId": "table_0_row_2_cell_2",
                "elementType": "table_cell",
                "type": "number_mismatch",
                "message": "Số tiền chữ và số không khớp",
                "suggestion": "Một triệu",
                "severity": "error",
                "errorText": "một tỷ"
            }
        ]
    
    @staticmethod
    def save_test_scenario(scenario_name: str, errors: List[Dict]):
        """Save test scenario to JSON file"""
        filename = f"test_scenario_{scenario_name}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(errors, f, ensure_ascii=False, indent=2)
        print(f"Saved test scenario: {filename}")


if __name__ == '__main__':
    manager = TestScenarioManager()
    
    print("=" * 50)
    print("Document Validation System - Test Scenarios")
    print("=" * 50)
    
    # Example: Get legal contract errors
    contract_errors = manager.get_legal_contract_errors()
    print("\nLegal Contract Errors:")
    print(json.dumps(contract_errors[:1], ensure_ascii=False, indent=2))
    
    # Save scenarios
    manager.save_test_scenario("legal_contract", contract_errors)
    manager.save_test_scenario("report", manager.get_report_errors())
    
    print("\n✓ Test scenarios created successfully!")
