"""
test_extraction2.py - Comprehensive K-1 Field Extraction Test
=============================================================
Tests all fields that are extracted versus expected values.
Provides detailed reporting on extraction accuracy.
"""

import os
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass
from extractor import K1Extractor
from models import K1Data, ExtractionResult
import json


@dataclass
class FieldTest:
    """Represents a single field test case"""
    field_name: str
    expected_value: Any
    actual_value: Any
    passed: bool
    notes: str = ""


class K1ExtractionTester:
    """
    Comprehensive testing class for K-1 extraction.
    Tests all fields and provides detailed reporting.
    """
    
    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.extractor = K1Extractor(verbose=False)  # Less verbose for testing
        
    def print_header(self, text: str):
        """Print a formatted header"""
        print("\n" + "="*70)
        print(text.center(70))
        print("="*70)
    
    def print_section(self, text: str):
        """Print a section header"""
        print(f"\n{'─'*50}")
        print(f"  {text}")
        print(f"{'─'*50}")
    
    def get_expected_values(self) -> Dict:
        """
        Define expected values for the Enviva sample K-1.
        
        These are the actual values from the PDF that should be extracted.
        Update these based on your specific test PDF.
        """
        return {
            # Entity Information
            'form_type': '1065',  # Partnership K-1
            'tax_year': '2023',
            'ein': '56-2178030',  # Enviva's EIN
            'entity_name': 'Enviva Partners, LP',
            
            # Box Values (Part III)
            'box_1_ordinary_income': -27942.0,  # Loss shown as negative
            'box_2_rental_real_estate': 0.0,
            'box_3_other_rental': 0.0,
            'box_4_guaranteed_payments': 0.0,
            'box_5_interest_income': 0.0,
            'box_6a_ordinary_dividends': 0.0,
            'box_6b_qualified_dividends': 0.0,
            'box_7_royalties': 0.0,
            'box_8_net_short_term_gain': 0.0,
            'box_9a_net_long_term_gain': 0.0,
            'box_10_net_1231_gain': 0.0,
            'box_11_other_income': 0.0,
            'box_12_section_179': 0.0,
            'box_19_distributions': 25100.0,  # Cash distributions
            
            # Capital Account (Part L)
            'capital_beginning': 1076588.0,
            'capital_ending': 1024146.0,
            'capital_contributions': 0.0,
            'capital_distributions': 25100.0,  # Should match box 19
            
            # Ownership Percentages
            # These might not be directly shown, so they're optional
            'profit_sharing_percent': None,
            'loss_sharing_percent': None,
            'capital_percent': None,
        }
    
    def compare_values(self, expected: Any, actual: Any, tolerance: float = 1.0) -> bool:
        """
        Compare expected and actual values with tolerance for floats.
        
        Args:
            expected: Expected value
            actual: Actual extracted value
            tolerance: Acceptable difference for float comparisons
        """
        # Handle None cases
        if expected is None and actual is None:
            return True
        if expected is None or actual is None:
            return False
            
        # Handle string comparisons
        if isinstance(expected, str) and isinstance(actual, str):
            # Case-insensitive comparison for strings
            return expected.lower().strip() in actual.lower().strip() or \
                   actual.lower().strip() in expected.lower().strip()
        
        # Handle numeric comparisons with tolerance
        if isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
            return abs(expected - actual) <= tolerance
            
        # Direct comparison for other types
        return expected == actual
    
    def test_extraction(self, pdf_path: str) -> Tuple[List[FieldTest], ExtractionResult]:
        """
        Test extraction on a PDF file.
        
        Returns:
            Tuple of (test results, extraction result)
        """
        # Extract the PDF
        result = self.extractor.extract_from_pdf(pdf_path)
        
        if not result.success or not result.data:
            return [], result
        
        # Get expected values
        expected = self.get_expected_values()
        
        # Test each field
        test_results = []
        k1_data = result.data
        
        # Test entity fields
        entity_fields = [
            ('form_type', k1_data.form_type.value if k1_data.form_type else None),
            ('tax_year', k1_data.tax_year),
            ('ein', k1_data.ein),
            ('entity_name', k1_data.entity_name),
        ]
        
        for field_name, actual_value in entity_fields:
            expected_value = expected.get(field_name)
            passed = self.compare_values(expected_value, actual_value)
            
            test = FieldTest(
                field_name=field_name,
                expected_value=expected_value,
                actual_value=actual_value,
                passed=passed,
                notes="Entity information"
            )
            test_results.append(test)
        
        # Test box values
        box_fields = [
            'box_1_ordinary_income',
            'box_2_rental_real_estate',
            'box_3_other_rental',
            'box_4_guaranteed_payments',
            'box_5_interest_income',
            'box_6a_ordinary_dividends',
            'box_6b_qualified_dividends',
            'box_7_royalties',
            'box_8_net_short_term_gain',
            'box_9a_net_long_term_gain',
            'box_10_net_1231_gain',
            'box_11_other_income',
            'box_12_section_179',
            'box_19_distributions',
        ]
        
        for field_name in box_fields:
            actual_value = getattr(k1_data, field_name, None)
            expected_value = expected.get(field_name)
            
            # Special handling for fields that might not be present
            if expected_value == 0.0 and actual_value is None:
                actual_value = 0.0  # Treat None as 0 for zero-value boxes
            
            passed = self.compare_values(expected_value, actual_value)
            
            test = FieldTest(
                field_name=field_name,
                expected_value=expected_value,
                actual_value=actual_value,
                passed=passed,
                notes="Box value from Part III"
            )
            test_results.append(test)
        
        # Test capital account fields
        capital_fields = [
            'capital_beginning',
            'capital_ending',
            'capital_contributions',
            'capital_distributions',
        ]
        
        for field_name in capital_fields:
            actual_value = getattr(k1_data, field_name, None)
            expected_value = expected.get(field_name)
            passed = self.compare_values(expected_value, actual_value)
            
            test = FieldTest(
                field_name=field_name,
                expected_value=expected_value,
                actual_value=actual_value,
                passed=passed,
                notes="Capital account from Part L"
            )
            test_results.append(test)
        
        # Test percentage fields (if available)
        percentage_fields = [
            'profit_sharing_percent',
            'loss_sharing_percent',
            'capital_percent',
        ]
        
        for field_name in percentage_fields:
            actual_value = getattr(k1_data, field_name, None)
            expected_value = expected.get(field_name)
            
            # Skip if expected is None (not shown in PDF)
            if expected_value is None:
                continue
                
            passed = self.compare_values(expected_value, actual_value)
            
            test = FieldTest(
                field_name=field_name,
                expected_value=expected_value,
                actual_value=actual_value,
                passed=passed,
                notes="Ownership percentage"
            )
            test_results.append(test)
        
        return test_results, result
    
    def print_results(self, test_results: List[FieldTest], extraction_result: ExtractionResult):
        """
        Print detailed test results.
        """
        self.print_header("K-1 EXTRACTION TEST RESULTS")
        
        # Summary statistics
        total_tests = len(test_results)
        passed_tests = sum(1 for t in test_results if t.passed)
        failed_tests = total_tests - passed_tests
        pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"\n📊 Summary:")
        print(f"  Total Fields Tested: {total_tests}")
        print(f"  ✅ Passed: {passed_tests}")
        print(f"  ❌ Failed: {failed_tests}")
        print(f"  📈 Pass Rate: {pass_rate:.1f}%")
        print(f"  ⏱️  Processing Time: {extraction_result.processing_time:.2f}s")
        print(f"  🔍 Extraction Method: {extraction_result.extraction_method.value}")
        
        # Group results by category
        entity_tests = [t for t in test_results if 'Entity' in t.notes]
        box_tests = [t for t in test_results if 'Box' in t.notes]
        capital_tests = [t for t in test_results if 'Capital' in t.notes]
        percentage_tests = [t for t in test_results if 'percentage' in t.notes]
        
        # Print entity information results
        if entity_tests:
            self.print_section("Entity Information")
            for test in entity_tests:
                status = "✅" if test.passed else "❌"
                print(f"  {status} {test.field_name:25} Expected: {test.expected_value!r:20} Got: {test.actual_value!r}")
        
        # Print box value results
        if box_tests:
            self.print_section("Box Values (Part III)")
            for test in box_tests:
                status = "✅" if test.passed else "❌"
                expected_str = f"${test.expected_value:,.2f}" if test.expected_value is not None else "None"
                actual_str = f"${test.actual_value:,.2f}" if test.actual_value is not None else "None"
                print(f"  {status} {test.field_name:25} Expected: {expected_str:15} Got: {actual_str}")
        
        # Print capital account results
        if capital_tests:
            self.print_section("Capital Account (Part L)")
            for test in capital_tests:
                status = "✅" if test.passed else "❌"
                expected_str = f"${test.expected_value:,.2f}" if test.expected_value is not None else "None"
                actual_str = f"${test.actual_value:,.2f}" if test.actual_value is not None else "None"
                print(f"  {status} {test.field_name:25} Expected: {expected_str:15} Got: {actual_str}")
        
        # Print percentage results (if any)
        if percentage_tests:
            self.print_section("Ownership Percentages")
            for test in percentage_tests:
                status = "✅" if test.passed else "❌"
                expected_str = f"{test.expected_value:.2f}%" if test.expected_value is not None else "None"
                actual_str = f"{test.actual_value:.2f}%" if test.actual_value is not None else "None"
                print(f"  {status} {test.field_name:25} Expected: {expected_str:10} Got: {actual_str}")
        
        # Print failed tests details
        failed = [t for t in test_results if not t.passed]
        if failed:
            self.print_section("❌ Failed Extractions - Details")
            for test in failed:
                print(f"\n  Field: {test.field_name}")
                print(f"    Expected: {test.expected_value!r}")
                print(f"    Got:      {test.actual_value!r}")
                print(f"    Notes:    {test.notes}")
        
        # Capital account reconciliation check
        if extraction_result.data:
            self.print_section("Validation Checks")
            
            # Check capital account reconciliation
            k1_data = extraction_result.data
            if all([k1_data.capital_beginning is not None,
                   k1_data.capital_ending is not None,
                   k1_data.capital_distributions is not None]):
                
                expected_ending = k1_data.capital_beginning
                if k1_data.capital_contributions:
                    expected_ending += k1_data.capital_contributions
                if k1_data.box_1_ordinary_income:
                    expected_ending += k1_data.box_1_ordinary_income
                if k1_data.capital_distributions:
                    expected_ending -= k1_data.capital_distributions
                
                reconciles = abs(expected_ending - k1_data.capital_ending) <= 1.0
                status = "✅" if reconciles else "⚠️"
                
                print(f"  {status} Capital Account Reconciliation:")
                print(f"      Beginning:     ${k1_data.capital_beginning:,.2f}")
                print(f"      + Income/Loss: ${k1_data.box_1_ordinary_income:,.2f}" if k1_data.box_1_ordinary_income else "      + Income/Loss: $0.00")
                print(f"      - Distributions: ${k1_data.capital_distributions:,.2f}" if k1_data.capital_distributions else "      - Distributions: $0.00")
                print(f"      = Expected:    ${expected_ending:,.2f}")
                print(f"      Actual Ending: ${k1_data.capital_ending:,.2f}")
                print(f"      Difference:    ${abs(expected_ending - k1_data.capital_ending):,.2f}")
        
        # Print warnings if any
        if extraction_result.data and extraction_result.data.warnings:
            self.print_section("⚠️ Extraction Warnings")
            for warning in extraction_result.data.warnings:
                print(f"  • {warning}")
    
    def export_results(self, test_results: List[FieldTest], extraction_result: ExtractionResult, 
                      output_file: str = "test_results.json"):
        """
        Export test results to JSON for further analysis.
        """
        export_data = {
            'summary': {
                'total_tests': len(test_results),
                'passed': sum(1 for t in test_results if t.passed),
                'failed': sum(1 for t in test_results if not t.passed),
                'pass_rate': sum(1 for t in test_results if t.passed) / len(test_results) * 100 if test_results else 0,
                'processing_time': extraction_result.processing_time,
                'extraction_method': extraction_result.extraction_method.value
            },
            'tests': [
                {
                    'field': t.field_name,
                    'expected': t.expected_value,
                    'actual': t.actual_value,
                    'passed': t.passed,
                    'notes': t.notes
                }
                for t in test_results
            ],
            'failed_fields': [
                t.field_name for t in test_results if not t.passed
            ]
        }
        
        with open(output_file, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
        
        print(f"\n📁 Results exported to: {output_file}")


def main():
    """
    Main test execution function.
    """
    # Initialize tester
    tester = K1ExtractionTester(verbose=True)
    
    # Test file path
    pdf_path = "Input/Input_Enviva_Sample_Tax_Package_10000_units-2.pdf"
    
    # Check if file exists
    if not os.path.exists(pdf_path):
        print(f"❌ Error: Test file not found: {pdf_path}")
        print("Please ensure the test PDF is in the correct location.")
        return
    
    print(f"📄 Testing extraction on: {os.path.basename(pdf_path)}")
    
    # Run the test
    test_results, extraction_result = tester.test_extraction(pdf_path)
    
    # Print results
    tester.print_results(test_results, extraction_result)
    
    # Export results to JSON
    tester.export_results(test_results, extraction_result)
    
    # Return success/failure for CI/CD integration
    if test_results:
        pass_rate = sum(1 for t in test_results if t.passed) / len(test_results) * 100
        if pass_rate >= 80:  # 80% pass rate threshold
            print(f"\n✅ TEST PASSED: {pass_rate:.1f}% fields extracted correctly")
            return 0
        else:
            print(f"\n❌ TEST FAILED: Only {pass_rate:.1f}% fields extracted correctly (need 80%)")
            return 1
    else:
        print("\n❌ TEST FAILED: No extraction results")
        return 1


if __name__ == "__main__":
    exit(main())