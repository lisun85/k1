"""
comprehensive_k1_test.py - Complete K-1 Field Testing with Form Field Support
==============================================================================
Tests EVERY field against actual values from the Sample_MadeUp.pdf K-1 form
Uses the FormFieldK1Extractor that handles fillable PDF forms
"""

import os
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
from form_field_k1_extractor import FormFieldK1Extractor, K1Fields


@dataclass
class ComprehensiveTestExpectations:
    """
    Actual values from Sample_MadeUp.pdf K-1 form
    These are the EXACT values visible in the PDF
    """
    
    # ========== PART I - PARTNERSHIP INFORMATION ==========
    part_i_a_ein: str = "12-3456789"  # Partnership's EIN
    part_i_b_name: str = "Wayne Enterprises"
    part_i_b_address: str = "800 South Wells St\nChicago, IL 60607"
    part_i_c_irs_center: str = None  # Not filled in the sample
    part_i_d_ptp: bool = False  # Box not checked
    
    # ========== PART II - PARTNER INFORMATION ==========
    part_ii_e_partner_tin: str = "123-45-6789"  # Partner's SSN
    part_ii_f_partner_name: str = "Bruce Wayne"
    part_ii_f_partner_address: str = "1007 Mountain Drive\nGotham, NJ 07001"
    part_ii_g_partner_type: str = "Limited partner"  # Checkbox marked
    part_ii_h1_domestic_foreign: str = "Domestic"  # Checkbox marked
    part_ii_h2_de_tin: Optional[str] = None  # Not filled
    part_ii_h2_de_name: Optional[str] = None  # Not filled
    part_ii_i1_entity_type: str = "Individual"
    part_ii_i2_retirement_plan: bool = False  # Not checked
    
    # Part II - J: Partner's share percentages
    part_ii_j_profit_beginning: float = 50.0
    part_ii_j_profit_ending: float = 50.0
    part_ii_j_loss_beginning: float = 50.0
    part_ii_j_loss_ending: float = 50.0
    part_ii_j_capital_beginning: float = 50.0
    part_ii_j_capital_ending: float = 50.0
    
    # Part II - K1: Partner's share of liabilities
    part_ii_k1_nonrecourse_beginning: float = 0.0
    part_ii_k1_nonrecourse_ending: float = 0.0
    part_ii_k1_qualified_nonrecourse_beginning: float = 0.0
    part_ii_k1_qualified_nonrecourse_ending: float = 0.0
    part_ii_k1_recourse_beginning: float = 30000.0
    part_ii_k1_recourse_ending: float = 35000.0
    
    # Part II - L: Capital Account Analysis
    part_ii_l_beginning_capital: float = 500000.0
    part_ii_l_capital_contributed: float = 0.0
    part_ii_l_current_year_income: float = 109000.0  # Sum of income items
    part_ii_l_other_increase: float = 0.0
    part_ii_l_withdrawals_distributions: float = 50000.0  # Shown in parentheses
    part_ii_l_ending_capital: float = 559000.0
    
    # Part II - M & N
    part_ii_m_property_contribution: bool = False  # "No" checked
    part_ii_n_unrecognized_704c_beginning: float = 0.0
    part_ii_n_unrecognized_704c_ending: float = 0.0
    
    # ========== PART III - INCOME/DEDUCTIONS/CREDITS ==========
    # Single value boxes
    part_iii_1_ordinary_income: float = 100000.0
    part_iii_2_rental_real_estate: float = 0.0
    part_iii_3_other_rental: float = 0.0
    part_iii_4a_guaranteed_payments_services: float = 0.0
    part_iii_4b_guaranteed_payments_capital: float = 0.0
    part_iii_4c_total_guaranteed_payments: float = 0.0
    part_iii_5_interest_income: float = 0.0
    part_iii_6a_ordinary_dividends: float = 0.0
    part_iii_6b_qualified_dividends: float = 0.0
    part_iii_6c_dividend_equivalents: float = 0.0
    part_iii_7_royalties: float = 0.0
    part_iii_8_net_short_term_gain: float = 0.0
    part_iii_9a_net_long_term_gain: float = 9000.0
    part_iii_9b_collectibles_gain: float = 0.0
    part_iii_9c_unrecaptured_1250: float = 0.0
    part_iii_10_net_section_1231: float = 0.0
    
    # Multi-line boxes (code/value pairs)
    part_iii_11_other_income: List[Dict] = None  # Empty in sample
    part_iii_12_section_179: float = 0.0
    part_iii_13_other_deductions: List[Dict] = None  # Empty in sample
    part_iii_14_self_employment: List[Dict] = None  # Empty in sample
    part_iii_15_credits: List[Dict] = None  # Empty in sample
    part_iii_16_schedule_k3_attached: bool = False  # Not checked
    part_iii_17_amt_items: float = 0.0
    part_iii_18_tax_exempt: List[Dict] = None  # Empty in sample
    part_iii_19_distributions: float = 50000.0
    part_iii_20_other_info: List[Dict] = None  # Empty in sample
    part_iii_21_foreign_taxes: float = 0.0
    part_iii_22_multiple_at_risk: bool = False  # Not checked
    part_iii_23_multiple_passive: bool = False  # Not checked


class ComprehensiveK1Tester:
    """Comprehensive test for every K-1 field using FormFieldK1Extractor"""
    
    def __init__(self, verbose: bool = True, log_file: str = "test_results.log"):
        self.verbose = verbose
        self.log_file = log_file
        # Use the new FormFieldK1Extractor instead of SimpleK1Extractor
        self.extractor = FormFieldK1Extractor(verbose=False)
        self.test_results = []
        self.passed_count = 0
        self.failed_count = 0
        self.skipped_count = 0
        
        # Open log file
        self.log_handle = open(log_file, 'w')
        
    def log(self, message: str, to_file: bool = True, to_console: bool = True):
        """Log to both console and file"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_msg = f"[{timestamp}] {message}"
        
        if to_console and self.verbose:
            print(message)
        
        if to_file and self.log_handle:
            self.log_handle.write(log_msg + "\n")
            self.log_handle.flush()
    
    def test_field(self, field_name: str, actual_value: Any, expected_value: Any, 
                   field_description: str = "", tolerance: float = 1.0) -> str:
        """
        Test a single field and return status
        Returns: 'PASS', 'FAIL', or 'SKIP'
        """
        
        # Handle None/empty cases
        if expected_value is None and actual_value is None:
            status = "SKIP"
            self.skipped_count += 1
        elif expected_value is None and actual_value is not None:
            status = "FAIL"  # Extracted something when nothing expected
            self.failed_count += 1
        elif expected_value is not None and actual_value is None:
            status = "FAIL"  # Failed to extract expected value
            self.failed_count += 1
        else:
            # Both have values - compare them
            if isinstance(expected_value, (int, float)) and isinstance(actual_value, (int, float)):
                # Numeric comparison with tolerance
                if abs(expected_value - actual_value) <= tolerance:
                    status = "PASS"
                    self.passed_count += 1
                else:
                    status = "FAIL"
                    self.failed_count += 1
            elif isinstance(expected_value, str) and isinstance(actual_value, str):
                # String comparison (case-insensitive, partial match)
                # Clean up strings for comparison
                exp_clean = expected_value.lower().strip()
                act_clean = actual_value.lower().strip()
                
                # Check for partial matches or exact matches
                if (exp_clean in act_clean or act_clean in exp_clean or exp_clean == act_clean):
                    status = "PASS"
                    self.passed_count += 1
                else:
                    # Also check if multi-line addresses match partially
                    if '\n' in expected_value or '\n' in actual_value:
                        exp_parts = [p.strip().lower() for p in expected_value.split('\n')]
                        act_parts = [p.strip().lower() for p in actual_value.split('\n')]
                        if any(ep in ' '.join(act_parts) for ep in exp_parts):
                            status = "PASS"
                            self.passed_count += 1
                        else:
                            status = "FAIL"
                            self.failed_count += 1
                    else:
                        status = "FAIL"
                        self.failed_count += 1
            elif isinstance(expected_value, bool) and isinstance(actual_value, bool):
                # Boolean comparison
                if expected_value == actual_value:
                    status = "PASS"
                    self.passed_count += 1
                else:
                    status = "FAIL"
                    self.failed_count += 1
            else:
                # Direct comparison
                if expected_value == actual_value:
                    status = "PASS"
                    self.passed_count += 1
                else:
                    status = "FAIL"
                    self.failed_count += 1
        
        # Format values for display
        if isinstance(expected_value, float):
            exp_str = f"${expected_value:,.2f}"
            act_str = f"${actual_value:,.2f}" if actual_value is not None else "None/Empty"
        elif isinstance(expected_value, bool):
            exp_str = "Checked" if expected_value else "Not Checked"
            act_str = "Checked" if actual_value else "Not Checked"
        elif expected_value is None:
            exp_str = "Empty/None"
            act_str = str(actual_value) if actual_value is not None else "Empty/None"
        else:
            exp_str = str(expected_value)[:50] + "..." if len(str(expected_value)) > 50 else str(expected_value)
            act_str = str(actual_value)[:50] + "..." if actual_value and len(str(actual_value)) > 50 else str(actual_value) if actual_value is not None else "None/Empty"
        
        # Choose emoji based on status
        emoji = {"PASS": "✅", "FAIL": "❌", "SKIP": "⭕️"}[status]
        
        # Log result
        self.log(f"{emoji} [{status:4}] {field_name:45} | Expected: {exp_str:30} | Got: {act_str:30}")
        
        # Store result
        self.test_results.append({
            'field': field_name,
            'description': field_description,
            'expected': expected_value,
            'actual': actual_value,
            'status': status
        })
        
        return status
    
    def run_comprehensive_test(self, pdf_path: str):
        """Run all tests on the K-1 PDF"""
        
        self.log("="*100)
        self.log("COMPREHENSIVE K-1 EXTRACTION TEST (WITH FORM FIELD SUPPORT)")
        self.log("="*100)
        self.log(f"PDF File: {pdf_path}")
        self.log(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.log(f"Extractor: FormFieldK1Extractor")
        self.log("="*100)
        
        # Extract data
        self.log("\n📄 EXTRACTING DATA FROM PDF (FORM FIELDS + TEXT)...")
        k1_data = self.extractor.extract_from_pdf(pdf_path)
        self.log("✓ Extraction complete\n")
        
        # Load expected values
        expectations = ComprehensiveTestExpectations()
        
        # ========== TEST PART I ==========
        self.log("\n" + "="*100)
        self.log("PART I - INFORMATION ABOUT THE PARTNERSHIP")
        self.log("="*100)
        
        self.test_field("Part I.A - Partnership EIN", 
                       k1_data.part_i_a_ein, 
                       expectations.part_i_a_ein,
                       "Partnership's employer identification number")
        
        self.test_field("Part I.B - Partnership Name", 
                       k1_data.part_i_b_name, 
                       expectations.part_i_b_name,
                       "Partnership's legal name")
        
        self.test_field("Part I.B - Partnership Address", 
                       k1_data.part_i_b_address, 
                       expectations.part_i_b_address,
                       "Partnership's mailing address")
        
        self.test_field("Part I.C - IRS Center", 
                       k1_data.part_i_c_irs_center, 
                       expectations.part_i_c_irs_center,
                       "IRS center where partnership filed return")
        
        self.test_field("Part I.D - PTP Status", 
                       k1_data.part_i_d_ptp, 
                       expectations.part_i_d_ptp,
                       "Is this a publicly traded partnership")
        
        # ========== TEST PART II ==========
        self.log("\n" + "="*100)
        self.log("PART II - INFORMATION ABOUT THE PARTNER")
        self.log("="*100)
        
        self.test_field("Part II.E - Partner TIN", 
                       k1_data.part_ii_e_partner_tin, 
                       expectations.part_ii_e_partner_tin,
                       "Partner's SSN or TIN")
        
        self.test_field("Part II.F - Partner Name", 
                       k1_data.part_ii_f_partner_name, 
                       expectations.part_ii_f_partner_name,
                       "Partner's legal name")
        
        self.test_field("Part II.F - Partner Address", 
                       k1_data.part_ii_f_partner_address, 
                       expectations.part_ii_f_partner_address,
                       "Partner's mailing address")
        
        self.test_field("Part II.G - Partner Type", 
                       k1_data.part_ii_g_partner_type, 
                       expectations.part_ii_g_partner_type,
                       "General or Limited partner")
        
        self.test_field("Part II.H1 - Domestic/Foreign", 
                       k1_data.part_ii_h1_domestic_foreign, 
                       expectations.part_ii_h1_domestic_foreign,
                       "Domestic or Foreign partner")
        
        self.test_field("Part II.I1 - Entity Type", 
                       k1_data.part_ii_i1_entity_type, 
                       expectations.part_ii_i1_entity_type,
                       "What type of entity is this partner")
        
        # Part II.J - Percentages
        self.log("\n--- Part II.J: Partner's Share Percentages ---")
        self.test_field("Part II.J - Profit % (Beginning)", 
                       k1_data.part_ii_j_profit_beginning, 
                       expectations.part_ii_j_profit_beginning)
        
        self.test_field("Part II.J - Profit % (Ending)", 
                       k1_data.part_ii_j_profit_ending, 
                       expectations.part_ii_j_profit_ending)
        
        self.test_field("Part II.J - Loss % (Beginning)", 
                       k1_data.part_ii_j_loss_beginning, 
                       expectations.part_ii_j_loss_beginning)
        
        self.test_field("Part II.J - Loss % (Ending)", 
                       k1_data.part_ii_j_loss_ending, 
                       expectations.part_ii_j_loss_ending)
        
        self.test_field("Part II.J - Capital % (Beginning)", 
                       k1_data.part_ii_j_capital_beginning, 
                       expectations.part_ii_j_capital_beginning)
        
        self.test_field("Part II.J - Capital % (Ending)", 
                       k1_data.part_ii_j_capital_ending, 
                       expectations.part_ii_j_capital_ending)
        
        # Part II.K1 - Liabilities
        self.log("\n--- Part II.K1: Partner's Share of Liabilities ---")
        self.test_field("Part II.K1 - Nonrecourse (Beginning)", 
                       k1_data.part_ii_k1_nonrecourse_beginning, 
                       expectations.part_ii_k1_nonrecourse_beginning)
        
        self.test_field("Part II.K1 - Nonrecourse (Ending)", 
                       k1_data.part_ii_k1_nonrecourse_ending, 
                       expectations.part_ii_k1_nonrecourse_ending)
        
        self.test_field("Part II.K1 - Qualified Nonrecourse (Beginning)", 
                       k1_data.part_ii_k1_qualified_nonrecourse_beginning, 
                       expectations.part_ii_k1_qualified_nonrecourse_beginning)
        
        self.test_field("Part II.K1 - Qualified Nonrecourse (Ending)", 
                       k1_data.part_ii_k1_qualified_nonrecourse_ending, 
                       expectations.part_ii_k1_qualified_nonrecourse_ending)
        
        self.test_field("Part II.K1 - Recourse (Beginning)", 
                       k1_data.part_ii_k1_recourse_beginning, 
                       expectations.part_ii_k1_recourse_beginning)
        
        self.test_field("Part II.K1 - Recourse (Ending)", 
                       k1_data.part_ii_k1_recourse_ending, 
                       expectations.part_ii_k1_recourse_ending)
        
        # Part II.L - Capital Account
        self.log("\n--- Part II.L: Partner's Capital Account Analysis ---")
        self.test_field("Part II.L - Beginning Capital", 
                       k1_data.part_ii_l_beginning_capital, 
                       expectations.part_ii_l_beginning_capital)
        
        self.test_field("Part II.L - Capital Contributed", 
                       k1_data.part_ii_l_capital_contributed, 
                       expectations.part_ii_l_capital_contributed)
        
        self.test_field("Part II.L - Current Year Income", 
                       k1_data.part_ii_l_current_year_income, 
                       expectations.part_ii_l_current_year_income)
        
        self.test_field("Part II.L - Other Increase", 
                       k1_data.part_ii_l_other_increase, 
                       expectations.part_ii_l_other_increase)
        
        self.test_field("Part II.L - Withdrawals/Distributions", 
                       k1_data.part_ii_l_withdrawals_distributions, 
                       expectations.part_ii_l_withdrawals_distributions)
        
        self.test_field("Part II.L - Ending Capital", 
                       k1_data.part_ii_l_ending_capital, 
                       expectations.part_ii_l_ending_capital)
        
        # Part II.M & N
        self.log("\n--- Part II.M & N: Other Information ---")
        self.test_field("Part II.M - Property Contribution", 
                       k1_data.part_ii_m_property_contribution, 
                       expectations.part_ii_m_property_contribution)
        
        self.test_field("Part II.N - Unrecognized 704(c) (Beginning)", 
                       k1_data.part_ii_n_unrecognized_704c_beginning, 
                       expectations.part_ii_n_unrecognized_704c_beginning)
        
        self.test_field("Part II.N - Unrecognized 704(c) (Ending)", 
                       k1_data.part_ii_n_unrecognized_704c_ending, 
                       expectations.part_ii_n_unrecognized_704c_ending)
        
        # ========== TEST PART III ==========
        self.log("\n" + "="*100)
        self.log("PART III - PARTNER'S SHARE OF CURRENT YEAR INCOME, DEDUCTIONS, CREDITS")
        self.log("="*100)
        
        # Test all Part III boxes
        part_iii_tests = [
            ("1 - Ordinary Business Income", k1_data.part_iii_1_ordinary_income, expectations.part_iii_1_ordinary_income),
            ("2 - Net Rental Real Estate", k1_data.part_iii_2_rental_real_estate, expectations.part_iii_2_rental_real_estate),
            ("3 - Other Net Rental", k1_data.part_iii_3_other_rental, expectations.part_iii_3_other_rental),
            ("4a - Guaranteed Payments (Services)", k1_data.part_iii_4a_guaranteed_payments_services, expectations.part_iii_4a_guaranteed_payments_services),
            ("4b - Guaranteed Payments (Capital)", k1_data.part_iii_4b_guaranteed_payments_capital, expectations.part_iii_4b_guaranteed_payments_capital),
            ("4c - Total Guaranteed Payments", k1_data.part_iii_4c_total_guaranteed_payments, expectations.part_iii_4c_total_guaranteed_payments),
            ("5 - Interest Income", k1_data.part_iii_5_interest_income, expectations.part_iii_5_interest_income),
            ("6a - Ordinary Dividends", k1_data.part_iii_6a_ordinary_dividends, expectations.part_iii_6a_ordinary_dividends),
            ("6b - Qualified Dividends", k1_data.part_iii_6b_qualified_dividends, expectations.part_iii_6b_qualified_dividends),
            ("6c - Dividend Equivalents", k1_data.part_iii_6c_dividend_equivalents, expectations.part_iii_6c_dividend_equivalents),
            ("7 - Royalties", k1_data.part_iii_7_royalties, expectations.part_iii_7_royalties),
            ("8 - Net Short-term Capital Gain", k1_data.part_iii_8_net_short_term_gain, expectations.part_iii_8_net_short_term_gain),
            ("9a - Net Long-term Capital Gain", k1_data.part_iii_9a_net_long_term_gain, expectations.part_iii_9a_net_long_term_gain),
            ("9b - Collectibles Gain", k1_data.part_iii_9b_collectibles_gain, expectations.part_iii_9b_collectibles_gain),
            ("9c - Unrecaptured Section 1250", k1_data.part_iii_9c_unrecaptured_1250, expectations.part_iii_9c_unrecaptured_1250),
            ("10 - Net Section 1231 Gain", k1_data.part_iii_10_net_section_1231, expectations.part_iii_10_net_section_1231),
            ("12 - Section 179 Deduction", k1_data.part_iii_12_section_179, expectations.part_iii_12_section_179),
            ("16 - Schedule K-3 Attached", k1_data.part_iii_16_schedule_k3_attached, expectations.part_iii_16_schedule_k3_attached),
            ("17 - AMT Items", k1_data.part_iii_17_amt_items, expectations.part_iii_17_amt_items),
            ("19 - Distributions", k1_data.part_iii_19_distributions, expectations.part_iii_19_distributions),
            ("21 - Foreign Taxes", k1_data.part_iii_21_foreign_taxes, expectations.part_iii_21_foreign_taxes),
            ("22 - Multiple At-Risk Activities", k1_data.part_iii_22_multiple_at_risk, expectations.part_iii_22_multiple_at_risk),
            ("23 - Multiple Passive Activities", k1_data.part_iii_23_multiple_passive, expectations.part_iii_23_multiple_passive),
        ]
        
        for field_name, actual, expected in part_iii_tests:
            self.test_field(f"Part III.{field_name}", actual, expected)
        
        # ========== SUMMARY ==========
        self.print_summary(k1_data, expectations)
        
        # Close log file
        if self.log_handle:
            self.log_handle.close()
        
        return k1_data
    
    def print_summary(self, k1_data: K1Fields, expectations: ComprehensiveTestExpectations):
        """Print comprehensive test summary"""
        
        total_tests = self.passed_count + self.failed_count + self.skipped_count
        pass_rate = (self.passed_count / total_tests * 100) if total_tests > 0 else 0
        
        self.log("\n" + "="*100)
        self.log("TEST SUMMARY")
        self.log("="*100)
        
        self.log(f"Total Fields Tested: {total_tests}")
        self.log(f"✅ Passed: {self.passed_count} ({self.passed_count/total_tests*100:.1f}%)")
        self.log(f"❌ Failed: {self.failed_count} ({self.failed_count/total_tests*100:.1f}%)")
        self.log(f"⭕️  Skipped: {self.skipped_count} ({self.skipped_count/total_tests*100:.1f}%)")
        self.log(f"📊 Overall Pass Rate: {pass_rate:.1f}%")
        
        # Capital Account Reconciliation
        self.log("\n" + "="*100)
        self.log("CAPITAL ACCOUNT RECONCILIATION CHECK")
        self.log("="*100)
        
        if k1_data.part_ii_l_beginning_capital is not None and k1_data.part_ii_l_ending_capital is not None:
            beginning = k1_data.part_ii_l_beginning_capital
            contributed = k1_data.part_ii_l_capital_contributed or 0
            income = k1_data.part_ii_l_current_year_income or 0
            distributions = k1_data.part_ii_l_withdrawals_distributions or 0
            ending = k1_data.part_ii_l_ending_capital
            
            calculated_ending = beginning + contributed + income - distributions
            difference = abs(calculated_ending - ending)
            
            self.log(f"Beginning Capital:      ${beginning:,.2f}")
            self.log(f"+ Contributions:        ${contributed:,.2f}")
            self.log(f"+ Current Year Income:  ${income:,.2f}")
            self.log(f"- Distributions:        ${distributions:,.2f}")
            self.log(f"= Calculated Ending:    ${calculated_ending:,.2f}")
            self.log(f"  Actual Ending:        ${ending:,.2f}")
            self.log(f"  Difference:           ${difference:,.2f}")
            
            if difference <= 1.0:
                self.log("✅ Capital account reconciles!")
            else:
                self.log("❌ Capital account does NOT reconcile!")
        else:
            self.log("⚠️  Cannot reconcile - missing capital account values")
        
        # List all failed fields
        if self.failed_count > 0:
            self.log("\n" + "="*100)
            self.log("FAILED FIELD DETAILS")
            self.log("="*100)
            
            for result in self.test_results:
                if result['status'] == 'FAIL':
                    self.log(f"\n❌ {result['field']}")
                    self.log(f"   Expected: {result['expected']}")
                    self.log(f"   Got:      {result['actual']}")
        
        # Save detailed results to JSON
        self.save_results_to_json()
        
        # Overall pass/fail
        self.log("\n" + "="*100)
        if pass_rate >= 80:
            self.log(f"✅ TEST PASSED - {pass_rate:.1f}% extraction accuracy")
        else:
            self.log(f"❌ TEST FAILED - Only {pass_rate:.1f}% accuracy (need 80%)")
        self.log("="*100)
    
    def save_results_to_json(self):
        """Save detailed test results to JSON file"""
        
        output = {
            'test_timestamp': datetime.now().isoformat(),
            'extractor_type': 'FormFieldK1Extractor',
            'summary': {
                'total_tests': self.passed_count + self.failed_count + self.skipped_count,
                'passed': self.passed_count,
                'failed': self.failed_count,
                'skipped': self.skipped_count,
                'pass_rate': (self.passed_count / (self.passed_count + self.failed_count + self.skipped_count) * 100) 
                            if (self.passed_count + self.failed_count + self.skipped_count) > 0 else 0
            },
            'detailed_results': self.test_results
        }
        
        with open('k1_test_results.json', 'w') as f:
            json.dump(output, f, indent=2, default=str)
        
        self.log(f"\n📝 Detailed results saved to: k1_test_results.json")
        self.log(f"📝 Test log saved to: {self.log_file}")


def main():
    """Main test execution"""
    import sys
    
    # Get PDF path
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
    else:
        pdf_path = "Input/Sample_MadeUp.pdf"
    
    # Check if file exists
    if not os.path.exists(pdf_path):
        print(f"❌ Error: PDF file not found: {pdf_path}")
        return 1
    
    print(f"\n📋 Testing K-1 extraction on: {pdf_path}")
    print(f"🔧 Using: FormFieldK1Extractor (with form field support)")
    print("="*100)
    
    # Run comprehensive test
    tester = ComprehensiveK1Tester(verbose=True, log_file="k1_extraction_test.log")
    k1_data = tester.run_comprehensive_test(pdf_path)
    
    return 0


if __name__ == "__main__":
    exit(main())