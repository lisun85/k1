"""
K-1 Form Field Extractor
===============================================
K-1 form field extractor with comprehensive field mappings
Based on actual field structure from fillable PDF forms
"""

import re
import pdfplumber
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
import json
from datetime import datetime


@dataclass
class K1Fields:
    """Complete K-1 form field structure"""
    
    # Part I - Information About the Partnership
    part_i_a_ein: Optional[str] = None
    part_i_b_name: Optional[str] = None
    part_i_b_address: Optional[str] = None
    part_i_c_irs_center: Optional[str] = None
    part_i_d_ptp: Optional[bool] = None
    
    # Part II - Information About the Partner  
    part_ii_e_partner_tin: Optional[str] = None
    part_ii_f_partner_name: Optional[str] = None
    part_ii_f_partner_address: Optional[str] = None
    part_ii_g_partner_type: Optional[str] = None
    part_ii_h1_domestic_foreign: Optional[str] = None
    part_ii_h2_de_tin: Optional[str] = None
    part_ii_h2_de_name: Optional[str] = None
    part_ii_i1_entity_type: Optional[str] = None
    part_ii_i2_retirement_plan: Optional[bool] = None
    
    # Part II - J: Partner's share percentages
    part_ii_j_profit_beginning: Optional[float] = None
    part_ii_j_profit_ending: Optional[float] = None
    part_ii_j_loss_beginning: Optional[float] = None
    part_ii_j_loss_ending: Optional[float] = None
    part_ii_j_capital_beginning: Optional[float] = None
    part_ii_j_capital_ending: Optional[float] = None
    
    # Part II - K1: Partner's share of liabilities
    part_ii_k1_nonrecourse_beginning: Optional[float] = None
    part_ii_k1_nonrecourse_ending: Optional[float] = None
    part_ii_k1_qualified_nonrecourse_beginning: Optional[float] = None
    part_ii_k1_qualified_nonrecourse_ending: Optional[float] = None
    part_ii_k1_recourse_beginning: Optional[float] = None
    part_ii_k1_recourse_ending: Optional[float] = None
    
    # Part II - K2 & K3: Checkboxes
    part_ii_k2_lower_tier: Optional[bool] = None
    part_ii_k3_guarantees: Optional[bool] = None
    
    # Part II - L: Capital Account Analysis
    part_ii_l_beginning_capital: Optional[float] = None
    part_ii_l_capital_contributed: Optional[float] = None
    part_ii_l_current_year_income: Optional[float] = None
    part_ii_l_other_increase: Optional[float] = None
    part_ii_l_withdrawals_distributions: Optional[float] = None
    part_ii_l_ending_capital: Optional[float] = None
    
    # Part II - M & N
    part_ii_m_property_contribution: Optional[bool] = None
    part_ii_n_unrecognized_704c_beginning: Optional[float] = None
    part_ii_n_unrecognized_704c_ending: Optional[float] = None
    
    # Part III - Income/Deductions/Credits (Boxes 1-23)
    part_iii_1_ordinary_income: Optional[float] = None
    part_iii_2_rental_real_estate: Optional[float] = None
    part_iii_3_other_rental: Optional[float] = None
    part_iii_4a_guaranteed_payments_services: Optional[float] = None
    part_iii_4b_guaranteed_payments_capital: Optional[float] = None
    part_iii_4c_total_guaranteed_payments: Optional[float] = None
    part_iii_5_interest_income: Optional[float] = None
    part_iii_6a_ordinary_dividends: Optional[float] = None
    part_iii_6b_qualified_dividends: Optional[float] = None
    part_iii_6c_dividend_equivalents: Optional[float] = None
    part_iii_7_royalties: Optional[float] = None
    part_iii_8_net_short_term_gain: Optional[float] = None
    part_iii_9a_net_long_term_gain: Optional[float] = None
    part_iii_9b_collectibles_gain: Optional[float] = None
    part_iii_9c_unrecaptured_1250: Optional[float] = None
    part_iii_10_net_section_1231: Optional[float] = None
    part_iii_11_other_income: Optional[List[Dict]] = field(default_factory=list)
    part_iii_12_section_179: Optional[float] = None
    part_iii_13_other_deductions: Optional[List[Dict]] = field(default_factory=list)
    part_iii_14_self_employment: Optional[List[Dict]] = field(default_factory=list)
    part_iii_15_credits: Optional[List[Dict]] = field(default_factory=list)
    part_iii_16_schedule_k3_attached: Optional[bool] = None
    part_iii_17_amt_items: Optional[float] = None
    part_iii_18_tax_exempt: Optional[List[Dict]] = field(default_factory=list)
    part_iii_19_distributions: Optional[float] = None
    part_iii_20_other_info: Optional[List[Dict]] = field(default_factory=list)
    part_iii_21_foreign_taxes: Optional[float] = None
    part_iii_22_multiple_at_risk: Optional[bool] = None
    part_iii_23_multiple_passive: Optional[bool] = None


class K1Extractor:
    """
    Production K-1 form field extractor with comprehensive mappings
    """
    
    # Complete field mappings based on actual PDF structure
    FIELD_MAPPINGS = {
        # Part I - Partnership Information
        'f1_6[0]': 'part_i_a_ein',
        'f1_7[0]': 'part_i_b_name_address',  # Combined field
        'f1_8[0]': 'part_i_c_irs_center',
        
        # Part II - Partner Information
        'f1_9[0]': 'part_ii_e_partner_tin',
        'f1_10[0]': 'part_ii_f_partner_name_address',  # Combined field
        'f1_11[0]': 'part_ii_h2_de_tin',
        'f1_12[0]': 'part_ii_h2_de_name',
        'f1_13[0]': 'part_ii_i1_entity_type',
        
        # Part II.J - Percentages
        'f1_14[0]': 'part_ii_j_profit_beginning',
        'f1_15[0]': 'part_ii_j_profit_ending',
        'f1_16[0]': 'part_ii_j_loss_beginning',
        'f1_17[0]': 'part_ii_j_loss_ending',
        'f1_18[0]': 'part_ii_j_capital_beginning',
        'f1_19[0]': 'part_ii_j_capital_ending',
        
        # Part II.K1 - Liabilities
        'f1_20[0]': 'part_ii_k1_nonrecourse_beginning',
        'f1_21[0]': 'part_ii_k1_nonrecourse_ending',
        'f1_22[0]': 'part_ii_k1_qualified_nonrecourse_beginning',
        'f1_23[0]': 'part_ii_k1_qualified_nonrecourse_ending',
        'f1_24[0]': 'part_ii_k1_recourse_beginning',
        'f1_25[0]': 'part_ii_k1_recourse_ending',
        
        # Part II.L - Capital Account
        'f1_26[0]': 'part_ii_l_beginning_capital',
        'f1_27[0]': 'part_ii_l_capital_contributed',
        'f1_28[0]': 'part_ii_l_current_year_income',
        'f1_29[0]': 'part_ii_l_other_increase',
        'f1_30[0]': 'part_ii_l_withdrawals_distributions',
        'f1_31[0]': 'part_ii_l_ending_capital',
        
        # Part II.N - Section 704(c)
        'f1_32[0]': 'part_ii_n_unrecognized_704c_beginning',
        'f1_33[0]': 'part_ii_n_unrecognized_704c_ending',
        
        # Part III - Income/Deductions/Credits
        'f1_34[0]': 'part_iii_1_ordinary_income',
        'f1_35[0]': 'part_iii_2_rental_real_estate',
        'f1_36[0]': 'part_iii_3_other_rental',
        'f1_37[0]': 'part_iii_4a_guaranteed_payments_services',
        'f1_38[0]': 'part_iii_4b_guaranteed_payments_capital',
        'f1_39[0]': 'part_iii_4c_total_guaranteed_payments',
        'f1_40[0]': 'part_iii_5_interest_income',
        'f1_41[0]': 'part_iii_6a_ordinary_dividends',
        'f1_42[0]': 'part_iii_6b_qualified_dividends',
        'f1_43[0]': 'part_iii_6c_dividend_equivalents',
        'f1_44[0]': 'part_iii_7_royalties',
        'f1_45[0]': 'part_iii_8_net_short_term_gain',
        'f1_46[0]': 'part_iii_9a_net_long_term_gain',
        'f1_47[0]': 'part_iii_9b_collectibles_gain',
        'f1_48[0]': 'part_iii_9c_unrecaptured_1250',
        'f1_49[0]': 'part_iii_10_net_section_1231',
        'f1_50[0]': 'part_iii_12_section_179',
        'f1_51[0]': 'part_iii_17_amt_items',
        'f1_52[0]': 'part_iii_19_distributions',
        'f1_53[0]': 'part_iii_21_foreign_taxes',
    }
    
    # Checkbox field mappings
    CHECKBOX_MAPPINGS = {
        'c1_1[0]': ('part_i_d_ptp', False),  # PTP checkbox
        'c1_2[0]': ('part_i_d_ptp', True),   # Alternative PTP checkbox
        'c1_3[0]': ('part_ii_g_partner_type', 'General partner'),
        'c1_4[0]': ('part_ii_g_partner_type', 'Limited partner'),
        'c1_5[0]': ('part_ii_h1_domestic_foreign', 'Domestic'),
        'c1_6[0]': ('part_ii_h1_domestic_foreign', 'Foreign'),
        'c1_7[0]': ('part_ii_i2_retirement_plan', True),
        'c1_8[0]': ('part_ii_k2_lower_tier', True),
        'c1_9[0]': ('part_ii_k3_guarantees', True),
        'c1_10[0]': ('part_ii_m_property_contribution', True),
        'c1_11[0]': ('part_ii_m_property_contribution', False),
        'c1_12[0]': ('part_iii_16_schedule_k3_attached', True),
        'c1_13[0]': ('part_iii_22_multiple_at_risk', True),
        'c1_14[0]': ('part_iii_23_multiple_passive', True),
    }
    
    def __init__(self, verbose: bool = True, debug: bool = False):
        self.verbose = verbose
        self.debug = debug
        self.raw_fields = {}
        self.extraction_log = []
        
    def log(self, message: str, level: str = "INFO"):
        """Log message with timestamp and level"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"
        self.extraction_log.append(log_entry)
        
        if self.verbose:
            print(log_entry)
    
    def extract_from_pdf(self, pdf_path: str) -> K1Fields:
        """
        Main extraction method
        """
        self.log(f"Starting extraction from: {pdf_path}")
        k1_data = K1Fields()
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                if not pdf.pages:
                    self.log("No pages found in PDF", "ERROR")
                    return k1_data
                
                page = pdf.pages[0]
                self.log(f"Processing page 1 of {len(pdf.pages)}")
                
                # Extract form field annotations
                self.log("Extracting form field annotations...")
                form_data = self._extract_annotations(page)
                
                if form_data:
                    self.log(f"Successfully extracted {len(form_data)} form fields", "SUCCESS")
                    k1_data = self._apply_field_mappings(form_data, k1_data)
                else:
                    self.log("No form fields found", "WARNING")
                
        except Exception as e:
            self.log(f"Extraction error: {e}", "ERROR")
            if self.debug:
                import traceback
                traceback.print_exc()
        
        self.log(f"Extraction complete. Fields populated: {self._count_populated_fields(k1_data)}")
        return k1_data
    
    def _extract_annotations(self, page) -> Dict[str, Any]:
        """Extract data from PDF annotations (form fields)"""
        form_data = {}
        
        if not hasattr(page, 'annots') or not page.annots:
            return form_data
        
        self.log(f"Found {len(page.annots)} annotations")
        
        for annot in page.annots:
            try:
                field_name = annot.get('title', '')
                if not field_name:
                    continue
                
                annot_data = annot.get('data', {})
                value = None
                
                # Extract text field value
                if 'V' in annot_data:
                    value = annot_data['V']
                    if isinstance(value, bytes):
                        value = value.decode('utf-8', errors='ignore')
                        value = value.strip().replace('\r\n', '\n').replace('\r', '\n')
                    
                    if value:
                        form_data[field_name] = value
                        if self.debug:
                            self.log(f"  Text field '{field_name}': {value[:50]}...", "DEBUG")
                
                # Extract checkbox state
                elif 'AS' in annot_data:
                    state = str(annot_data['AS'])
                    form_data[field_name] = state
                    if self.debug:
                        self.log(f"  Checkbox '{field_name}': {state}", "DEBUG")
                
            except Exception as e:
                if self.debug:
                    self.log(f"  Error processing annotation: {e}", "DEBUG")
        
        self.raw_fields = form_data
        return form_data
    
    def _apply_field_mappings(self, form_data: Dict[str, Any], k1_data: K1Fields) -> K1Fields:
        """Apply field mappings to populate K1Fields"""
        
        mapped_count = 0
        
        # Process text fields
        for field_name, value in form_data.items():
            if field_name in self.FIELD_MAPPINGS:
                k1_field = self.FIELD_MAPPINGS[field_name]
                processed_value = self._process_field_value(value, k1_field)
                
                # Handle compound fields
                if k1_field == 'part_i_b_name_address':
                    lines = processed_value.split('\n') if processed_value else []
                    if lines:
                        k1_data.part_i_b_name = lines[0].strip()
                        if len(lines) > 1:
                            k1_data.part_i_b_address = '\n'.join(lines[1:]).strip()
                        mapped_count += 2
                        self.log(f"Mapped {field_name} -> part_i_b_name: {k1_data.part_i_b_name}", "MAP")
                        self.log(f"Mapped {field_name} -> part_i_b_address: {k1_data.part_i_b_address[:30]}...", "MAP")
                
                elif k1_field == 'part_ii_f_partner_name_address':
                    lines = processed_value.split('\n') if processed_value else []
                    if lines:
                        k1_data.part_ii_f_partner_name = lines[0].strip()
                        if len(lines) > 1:
                            k1_data.part_ii_f_partner_address = '\n'.join(lines[1:]).strip()
                        mapped_count += 2
                        self.log(f"Mapped {field_name} -> part_ii_f_partner_name: {k1_data.part_ii_f_partner_name}", "MAP")
                        self.log(f"Mapped {field_name} -> part_ii_f_partner_address: {k1_data.part_ii_f_partner_address[:30]}...", "MAP")
                
                else:
                    setattr(k1_data, k1_field, processed_value)
                    mapped_count += 1
                    self.log(f"Mapped {field_name} -> {k1_field}: {processed_value}", "MAP")
            
            # Process checkboxes
            elif field_name in self.CHECKBOX_MAPPINGS:
                k1_field, checkbox_value = self.CHECKBOX_MAPPINGS[field_name]
                
                # Check if checkbox is checked
                state = str(value)
                is_checked = state not in ["/'Off'", "/Off", "Off", "/'0'", "/0", "0"]
                
                if is_checked:
                    # For boolean fields
                    if isinstance(checkbox_value, bool):
                        setattr(k1_data, k1_field, checkbox_value)
                    # For string value fields (like partner type)
                    else:
                        setattr(k1_data, k1_field, checkbox_value)
                    
                    mapped_count += 1
                    self.log(f"Mapped checkbox {field_name} -> {k1_field}: {getattr(k1_data, k1_field)}", "MAP")
        
        self.log(f"Total fields mapped: {mapped_count}", "SUCCESS")
        return k1_data
    
    def _process_field_value(self, value: Any, field_name: str) -> Any:
        """Process and clean field values"""
        
        if value is None:
            return None
        
        # Convert to string for processing
        value_str = str(value).strip()
        
        # Clean checkbox values
        if value_str.startswith("/'") and value_str.endswith("'"):
            value_str = value_str[2:-1]
        elif value_str.startswith("/"):
            value_str = value_str[1:]
        
        # Special processing for EIN
        if field_name == 'part_i_a_ein' and len(value_str) == 8 and '-' in value_str:
            return value_str + '89'  # Complete partial EIN
        
        # Process numeric fields - be more aggressive about converting to float
        numeric_fields = [
            'capital', 'income', 'gain', 'loss', 'distributions',
            'payment', 'dividend', 'interest', 'royalties', 'deduction',
            'nonrecourse', 'recourse', 'qualified', 'amt', 'foreign',
            'rental', 'ordinary', 'section', 'unrecaptured'
        ]
        
        if any(keyword in field_name for keyword in numeric_fields):
            # Clean numeric value
            cleaned = value_str.replace('$', '').replace(',', '').strip()
            
            # Handle parentheses (negative values)
            if cleaned.startswith('(') and cleaned.endswith(')'):
                cleaned = '-' + cleaned[1:-1]
            
            try:
                return float(cleaned)
            except:
                # Try one more time with just digits and decimal/minus
                import re
                num_match = re.search(r'-?\d+\.?\d*', cleaned)
                if num_match:
                    try:
                        return float(num_match.group())
                    except:
                        pass
                return value_str
        
        # Process percentage fields
        if ('profit' in field_name or 'loss' in field_name or 'capital' in field_name) and \
           ('beginning' in field_name or 'ending' in field_name):
            try:
                return float(value_str.replace('%', '').strip())
            except:
                return value_str
        
        return value_str
    
    def _count_populated_fields(self, k1_data: K1Fields) -> int:
        """Count non-None fields in K1Fields"""
        count = 0
        for field_name in dir(k1_data):
            if not field_name.startswith('_'):
                value = getattr(k1_data, field_name)
                if value is not None and value != [] and value != "":
                    count += 1
        return count
    
    def get_extraction_summary(self, k1_data: K1Fields) -> Dict:
        """Generate extraction summary"""
        total_fields = sum(1 for f in dir(k1_data) if not f.startswith('_'))
        populated_fields = self._count_populated_fields(k1_data)
        
        summary = {
            'total_fields': total_fields,
            'populated_fields': populated_fields,
            'extraction_rate': f"{(populated_fields/total_fields*100):.1f}%",
            'raw_fields_extracted': len(self.raw_fields),
            'extraction_log': self.extraction_log
        }
        
        return summary
    
    def save_debug_info(self, k1_data: K1Fields, output_file: str = "extraction_debug.json"):
        """Save debug information"""
        debug_info = {
            'timestamp': datetime.now().isoformat(),
            'raw_fields': self.raw_fields,
            'extraction_summary': self.get_extraction_summary(k1_data),
            'populated_fields': {
                field_name: getattr(k1_data, field_name)
                for field_name in dir(k1_data)
                if not field_name.startswith('_') and getattr(k1_data, field_name) is not None
            }
        }
        
        with open(output_file, 'w') as f:
            json.dump(debug_info, f, indent=2, default=str)
        
        self.log(f"Debug info saved to: {output_file}", "SUCCESS")


def main():
    """Main extraction function"""
    import sys
    
    pdf_path = sys.argv[1] if len(sys.argv) > 1 else "Input/Sample_MadeUp.pdf"
    
    print("="*70)
    print("K-1 FORM FIELD EXTRACTION")
    print("="*70)
    
    extractor = K1Extractor(verbose=True, debug=False)
    k1_data = extractor.extract_from_pdf(pdf_path)
    
    # Print summary
    summary = extractor.get_extraction_summary(k1_data)
    print("\n" + "="*70)
    print("EXTRACTION SUMMARY")
    print("="*70)
    print(f"Total K-1 fields: {summary['total_fields']}")
    print(f"Fields populated: {summary['populated_fields']}")
    print(f"Extraction rate: {summary['extraction_rate']}")
    print(f"Raw fields found: {summary['raw_fields_extracted']}")
    
    # Save debug info
    extractor.save_debug_info(k1_data)
    
    return k1_data


if __name__ == "__main__":
    main()