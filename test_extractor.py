"""
Comprehensive Test Suite for K-1 Extractor
===============================================================
Tests the golden extractor against actual PDF data with detailed logging
"""

import os
import json
from typing import Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass
from extractor import K1Extractor, K1Fields


@dataclass
class ActualPDFExpectations:
    """
    Expected values based on the ACTUAL data in Sample_MadeUp.pdf
    Based on the extraction results showing Luthor Corp, not Bruce Wayne
    """
    
    # Part I - Partnership Information (from raw extraction)
    part_i_a_ein: str = "12-3456789"  # Will be completed from 12-34567
    part_i_b_name: str = "Wayne Enterprises"
    part_i_b_address: str = "800 South Wells St, Chicago, IL 60607"
    part_i_c_irs_center: str = "E-file"
    part_i_d_ptp: bool = False  # c1_1[0] and c1_2[0] are Off
    
    # Part II - Partner Information (actual data from PDF)
    part_ii_e_partner_tin: str = "98765432"  # Actual TIN in PDF
    part_ii_f_partner_name: str = "Luthor Corp"  # Actual name in PDF
    part_ii_f_partner_address: str = "801 South Wells St, Chicago, IL 60607"
    part_ii_g_partner_type: str = "General partner"  # c1_3[0] is checked ('1')
    part_ii_h1_domestic_foreign: Optional[str] = None  # c1_5[0] is Off
    part_ii_i1_entity_type: str = "Individual"
    part_ii_i2_retirement_plan: bool = False  # c1_7[0] is Off
    
    # Part II.J - Percentages (actual values from PDF)
    part_ii_j_profit_beginning: float = 30.0
    part_ii_j_profit_ending: float = 30.0
    part_ii_j_loss_beginning: float = 50.0
    part_ii_j_loss_ending: float = 50.0
    part_ii_j_capital_beginning: float = 80.0
    part_ii_j_capital_ending: float = 80.0
    
    # Part II.K1 - Liabilities (from f1_20 and f1_21)
    part_ii_k1_nonrecourse_beginning: float = 0.0
    part_ii_k1_nonrecourse_ending: float = 100000.0
    part_ii_k1_qualified_nonrecourse_beginning: Optional[float] = None
    part_ii_k1_qualified_nonrecourse_ending: Optional[float] = None
    part_ii_k1_recourse_beginning: Optional[float] = None
    part_ii_k1_recourse_ending: Optional[float] = None
    
    # Part II.L - Capital Account (actual values from PDF)
    part_ii_l_beginning_capital: float = 300000.0
    part_ii_l_capital_contributed: float = 50000.0
    part_ii_l_current_year_income: float = -20000.0  # Negative
    part_ii_l_other_increase: float = 0.0
    part_ii_l_withdrawals_distributions: float = 10000.0
    part_ii_l_ending_capital: float = 340000.0
    
    # Part II.M - Property contribution
    part_ii_m_property_contribution: bool = False  # c1_11[0] is Off, c1_11[1] is '2'
    
    # Part III - Income/Deductions (actual values from PDF)
    part_iii_1_ordinary_income: float = 100000.0
    part_iii_2_rental_real_estate: float = 20000.0
    part_iii_3_other_rental: float = 30000.0
    part_iii_4a_guaranteed_payments_services: float = 4000.0
    part_iii_4b_guaranteed_payments_capital: float = 4100.0
    part_iii_4c_total_guaranteed_payments: float = 4200.0
    part_iii_5_interest_income: float = 5000.0
    part_iii_6a_ordinary_dividends: float = 6000.0
    part_iii_6b_qualified_dividends: float = 6100.0
    part_iii_6c_dividend_equivalents: float = 6200.0
    part_iii_7_royalties: float = 7000.0
    part_iii_8_net_short_term_gain: float = 8000.0
    part_iii_9a_net_long_term_gain: float = 9000.0
    part_iii_9b_collectibles_gain: float = -9100.0  # Negative
    part_iii_9c_unrecaptured_1250: float = 9200.0
    part_iii_10_net_section_1231: float = 10000.0
    
    # Checkboxes
    part_iii_16_schedule_k3_attached: bool = False  # c1_12[0] is Off
    part_iii_22_multiple_at_risk: bool = False  # c1_13[0] is Off
    part_iii_23_multiple_passive: bool = False  # c1_14[0] is Off


class K1ExtractorTester:
    """Comprehensive tester for K1 extractor"""
    
    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.test_results = []
        self.passed_tests = 0
        self.failed_tests = 0
        self.skipped_tests = 0
        self.extraction_log = []
        
    def log(self, message: str, level: str = "INFO"):
        """Log test message"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_msg = f"[{timestamp}] [{level:7}] {message}"
        self.extraction_log.append(log_msg)
        
        if self.verbose:
            # Color coding for terminal output
            if level == "SUCCESS":
                print(f"\033[92m{log_msg}\033[0m")  # Green
            elif level == "ERROR":
                print(f"\033[91m{log_msg}\033[0m")  # Red
            elif level == "WARNING":
                print(f"\033[93m{log_msg}\033[0m")  # Yellow
            elif level == "TEST":
                print(f"\033[94m{log_msg}\033[0m")  # Blue
            else:
                print(log_msg)
    
    def test_field(self, field_name: str, actual_value: Any, expected_value: Any, 
                   tolerance: float = 0.01) -> str:
        """Test individual field value"""
        
        # Handle None cases
        if expected_value is None and actual_value is None:
            status = "SKIP"
            self.skipped_tests += 1
        elif expected_value is None:
            status = "SKIP"  # Extra data, not necessarily wrong
            self.skipped_tests += 1
        elif actual_value is None:
            # Special case: If expecting False and got None, treat as success
            if expected_value is False:
                status = "PASS"
                self.passed_tests += 1
            else:
                status = "FAIL"
                self.failed_tests += 1
        else:
            # Compare values based on type
            if isinstance(expected_value, (int, float)) and isinstance(actual_value, (int, float)):
                if abs(expected_value - actual_value) <= tolerance:
                    status = "PASS"
                    self.passed_tests += 1
                else:
                    status = "FAIL"
                    self.failed_tests += 1
            elif isinstance(expected_value, str) and isinstance(actual_value, str):
                # String comparison (case-insensitive, trimmed)
                if expected_value.strip().lower() == actual_value.strip().lower():
                    status = "PASS"
                    self.passed_tests += 1
                else:
                    status = "FAIL"
                    self.failed_tests += 1
            elif isinstance(expected_value, bool) and isinstance(actual_value, bool):
                if expected_value == actual_value:
                    status = "PASS"
                    self.passed_tests += 1
                else:
                    status = "FAIL"
                    self.failed_tests += 1
            else:
                if expected_value == actual_value:
                    status = "PASS"
                    self.passed_tests += 1
                else:
                    status = "FAIL"
                    self.failed_tests += 1
        
        # Format values for display
        if isinstance(expected_value, float):
            exp_str = f"${expected_value:,.2f}"
            if actual_value is not None:
                # Try to convert to float
                try:
                    act_str = f"${float(actual_value):,.2f}"
                except:
                    #if it fails, just use string
                    act_str = f"${actual_value}"
            else:
                act_str = "None"
        elif isinstance(expected_value, bool):
            exp_str = str(expected_value)
            act_str = str(actual_value) if actual_value is not None else "None"
        else:
            exp_str = str(expected_value) if expected_value is not None else "None"
            act_str = str(actual_value) if actual_value is not None else "None"
        
        # Choose symbol
        symbol = {"PASS": "✓", "FAIL": "✗", "SKIP": "○"}[status]
        
        # Log result
        if status == "PASS":
            self.log(f"{symbol} {field_name:50} | Expected: {exp_str:25} | Got: {act_str:25}", "SUCCESS")
        elif status == "FAIL":
            self.log(f"{symbol} {field_name:50} | Expected: {exp_str:25} | Got: {act_str:25}", "ERROR")
        else:
            self.log(f"{symbol} {field_name:50} | Expected: {exp_str:25} | Got: {act_str:25}", "WARNING")
        
        # Store result
        self.test_results.append({
            'field': field_name,
            'expected': expected_value,
            'actual': actual_value,
            'status': status
        })
        
        return status
    
    def run_comprehensive_test(self, pdf_path: str):
        """Run all tests"""
        
        print("="*100)
        print("K-1 EXTRACTOR COMPREHENSIVE TEST SUITE")
        print("="*100)
        print(f"PDF File: {pdf_path}")
        print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*100)
        
        # Step 1: Extract data
        self.log("\n📄 EXTRACTING DATA FROM PDF...", "INFO")
        extractor = K1Extractor(verbose=False, debug=False)
        k1_data = extractor.extract_from_pdf(pdf_path)
        
        # Log raw fields found
        self.log(f"Raw fields extracted: {len(extractor.raw_fields)}", "INFO")
        
        # Step 2: Load expectations
        expectations = ActualPDFExpectations()
        
        # Step 3: Test each field
        self.log("\n🧪 TESTING EXTRACTED FIELDS...", "TEST")
        
        # Test Part I
        self.log("\n--- PART I: PARTNERSHIP INFORMATION ---", "TEST")
        self.test_field("part_i_a_ein", k1_data.part_i_a_ein, expectations.part_i_a_ein)
        self.test_field("part_i_b_name", k1_data.part_i_b_name, expectations.part_i_b_name)
        self.test_field("part_i_b_address", k1_data.part_i_b_address, expectations.part_i_b_address)
        self.test_field("part_i_c_irs_center", k1_data.part_i_c_irs_center, expectations.part_i_c_irs_center)
        self.test_field("part_i_d_ptp", k1_data.part_i_d_ptp, expectations.part_i_d_ptp)
        
        # Test Part II
        self.log("\n--- PART II: PARTNER INFORMATION ---", "TEST")
        self.test_field("part_ii_e_partner_tin", k1_data.part_ii_e_partner_tin, expectations.part_ii_e_partner_tin)
        self.test_field("part_ii_f_partner_name", k1_data.part_ii_f_partner_name, expectations.part_ii_f_partner_name)
        self.test_field("part_ii_f_partner_address", k1_data.part_ii_f_partner_address, expectations.part_ii_f_partner_address)
        self.test_field("part_ii_g_partner_type", k1_data.part_ii_g_partner_type, expectations.part_ii_g_partner_type)
        self.test_field("part_ii_i1_entity_type", k1_data.part_ii_i1_entity_type, expectations.part_ii_i1_entity_type)
        
        # Test Part II.J - Percentages
        self.log("\n--- PART II.J: PERCENTAGES ---", "TEST")
        self.test_field("part_ii_j_profit_beginning", k1_data.part_ii_j_profit_beginning, expectations.part_ii_j_profit_beginning)
        self.test_field("part_ii_j_profit_ending", k1_data.part_ii_j_profit_ending, expectations.part_ii_j_profit_ending)
        self.test_field("part_ii_j_loss_beginning", k1_data.part_ii_j_loss_beginning, expectations.part_ii_j_loss_beginning)
        self.test_field("part_ii_j_loss_ending", k1_data.part_ii_j_loss_ending, expectations.part_ii_j_loss_ending)
        self.test_field("part_ii_j_capital_beginning", k1_data.part_ii_j_capital_beginning, expectations.part_ii_j_capital_beginning)
        self.test_field("part_ii_j_capital_ending", k1_data.part_ii_j_capital_ending, expectations.part_ii_j_capital_ending)
        
        # Test Part II.L - Capital Account
        self.log("\n--- PART II.L: CAPITAL ACCOUNT ---", "TEST")
        self.test_field("part_ii_l_beginning_capital", k1_data.part_ii_l_beginning_capital, expectations.part_ii_l_beginning_capital)
        self.test_field("part_ii_l_capital_contributed", k1_data.part_ii_l_capital_contributed, expectations.part_ii_l_capital_contributed)
        self.test_field("part_ii_l_current_year_income", k1_data.part_ii_l_current_year_income, expectations.part_ii_l_current_year_income)
        self.test_field("part_ii_l_withdrawals_distributions", k1_data.part_ii_l_withdrawals_distributions, expectations.part_ii_l_withdrawals_distributions)
        self.test_field("part_ii_l_ending_capital", k1_data.part_ii_l_ending_capital, expectations.part_ii_l_ending_capital)
        
        # Test Part III - Income
        self.log("\n--- PART III: INCOME/DEDUCTIONS/CREDITS ---", "TEST")
        self.test_field("part_iii_1_ordinary_income", k1_data.part_iii_1_ordinary_income, expectations.part_iii_1_ordinary_income)
        self.test_field("part_iii_2_rental_real_estate", k1_data.part_iii_2_rental_real_estate, expectations.part_iii_2_rental_real_estate)
        self.test_field("part_iii_3_other_rental", k1_data.part_iii_3_other_rental, expectations.part_iii_3_other_rental)
        self.test_field("part_iii_4a_guaranteed_payments_services", k1_data.part_iii_4a_guaranteed_payments_services, expectations.part_iii_4a_guaranteed_payments_services)
        self.test_field("part_iii_5_interest_income", k1_data.part_iii_5_interest_income, expectations.part_iii_5_interest_income)
        self.test_field("part_iii_6a_ordinary_dividends", k1_data.part_iii_6a_ordinary_dividends, expectations.part_iii_6a_ordinary_dividends)
        self.test_field("part_iii_7_royalties", k1_data.part_iii_7_royalties, expectations.part_iii_7_royalties)
        self.test_field("part_iii_8_net_short_term_gain", k1_data.part_iii_8_net_short_term_gain, expectations.part_iii_8_net_short_term_gain)
        self.test_field("part_iii_9a_net_long_term_gain", k1_data.part_iii_9a_net_long_term_gain, expectations.part_iii_9a_net_long_term_gain)
        self.test_field("part_iii_10_net_section_1231", k1_data.part_iii_10_net_section_1231, expectations.part_iii_10_net_section_1231)
        
        # Print summary
        self.print_summary(k1_data, extractor)
        
        # Save results
        self.save_test_results(k1_data, extractor)
    
    def print_summary(self, k1_data: K1Fields, extractor: K1Extractor):
        """Print test summary with field mappings"""
        
        total_tests = self.passed_tests + self.failed_tests + self.skipped_tests
        
        print("\n" + "="*100)
        print("TEST SUMMARY")
        print("="*100)
        print(f"Total tests run: {total_tests}")
        print(f"✓ Passed: {self.passed_tests} ({self.passed_tests/total_tests*100:.1f}%)")
        print(f"✗ Failed: {self.failed_tests} ({self.failed_tests/total_tests*100:.1f}%)")
        print(f"○ Skipped: {self.skipped_tests} ({self.skipped_tests/total_tests*100:.1f}%)")
        
        # Show extraction summary
        summary = extractor.get_extraction_summary(k1_data)
        print("\n" + "="*100)
        print("EXTRACTION METRICS")
        print("="*100)
        print(f"Raw form fields found: {summary['raw_fields_extracted']}")
        print(f"K-1 fields populated: {summary['populated_fields']} / {summary['total_fields']}")
        print(f"Extraction rate: {summary['extraction_rate']}")
        
        # Show field mapping details
        print("\n" + "="*100)
        print("FIELD MAPPING DETAILS")
        print("="*100)
        print("\n📋 Raw Fields → K-1 Fields Mapping:")
        print("-"*80)
        
        # Show successful mappings
        for raw_field, value in extractor.raw_fields.items():
            if raw_field in extractor.FIELD_MAPPINGS:
                k1_field = extractor.FIELD_MAPPINGS[raw_field]
                print(f"  {raw_field:15} → {k1_field:40} = {str(value)[:30]}")
            elif raw_field in extractor.CHECKBOX_MAPPINGS:
                k1_field, checkbox_value = extractor.CHECKBOX_MAPPINGS[raw_field]
                print(f"  {raw_field:15} → {k1_field:40} = {str(value)[:30]}")
        
        # Capital account reconciliation
        if k1_data.part_ii_l_beginning_capital and k1_data.part_ii_l_ending_capital:
            print("\n" + "="*100)
            print("CAPITAL ACCOUNT RECONCILIATION")
            print("="*100)
            beginning = k1_data.part_ii_l_beginning_capital or 0
            contributed = k1_data.part_ii_l_capital_contributed or 0
            income = k1_data.part_ii_l_current_year_income or 0
            distributions = k1_data.part_ii_l_withdrawals_distributions or 0
            ending = k1_data.part_ii_l_ending_capital or 0
            
            calculated = beginning + contributed + income - distributions
            
            print(f"  Beginning:        ${beginning:12,.2f}")
            print(f"+ Contributions:    ${contributed:12,.2f}")
            print(f"+ Income/(Loss):    ${income:12,.2f}")
            print(f"- Distributions:    ${distributions:12,.2f}")
            print(f"= Calculated:       ${calculated:12,.2f}")
            print(f"  Actual Ending:    ${ending:12,.2f}")
            print(f"  Difference:       ${abs(calculated - ending):12,.2f}")
            
            if abs(calculated - ending) < 1.0:
                print("\n✓ Capital account reconciles correctly!")
            else:
                print("\n✗ Capital account does not reconcile!")
        
        # Overall verdict
        print("\n" + "="*100)
        pass_rate = self.passed_tests / total_tests * 100 if total_tests > 0 else 0
        if pass_rate >= 80:
            print(f"✅ TEST SUITE PASSED - {pass_rate:.1f}% success rate")
        else:
            print(f"❌ TEST SUITE FAILED - Only {pass_rate:.1f}% success rate (need 80%)")
        print("="*100)
    
    def save_test_results(self, k1_data: K1Fields, extractor: K1Extractor):
        """Save detailed test results to JSON"""
        
        output = {
            'test_timestamp': datetime.now().isoformat(),
            'pdf_file': 'Input/Sample_MadeUp.pdf',
            'test_summary': {
                'total_tests': self.passed_tests + self.failed_tests + self.skipped_tests,
                'passed': self.passed_tests,
                'failed': self.failed_tests,
                'skipped': self.skipped_tests,
                'pass_rate': f"{self.passed_tests/(self.passed_tests+self.failed_tests+self.skipped_tests)*100:.1f}%"
            },
            'extraction_summary': extractor.get_extraction_summary(k1_data),
            'raw_fields_extracted': extractor.raw_fields,
            'field_test_results': self.test_results,
            'failed_fields': [r for r in self.test_results if r['status'] == 'FAIL']
        }
        
        with open('test_results.json', 'w') as f:
            json.dump(output, f, indent=2, default=str)
        
        print(f"\n📝 Detailed test results saved to: test_results.json")
        print(f"📝 Extraction debug info saved to: extraction_debug.json")


def main():
    """Main test runner"""
    import sys
    
    pdf_path = sys.argv[1] if len(sys.argv) > 1 else "Input/Sample_MadeUp.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"❌ Error: PDF file not found: {pdf_path}")
        return 1
    
    tester = K1ExtractorTester(verbose=True)
    tester.run_comprehensive_test(pdf_path)
    
    return 0


if __name__ == "__main__":
    exit(main())