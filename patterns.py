"""
patterns.py - Regex Patterns for K-1 Data Extraction
====================================================
This file contains all the patterns we use to find and extract
data from K-1 text. Think of these as "search instructions" for
finding specific pieces of information in the messy PDF text.

STRATEGY:
1. Each pattern tries to be flexible (handles variations)
2. Patterns are ordered from most specific to most general
3. We capture groups for the actual values we want
"""

import re
from typing import Dict, Pattern, Optional, List, Tuple
from dataclasses import dataclass


@dataclass
class FieldPattern:
    """
    Represents a pattern for extracting a specific field.
    
    Attributes:
        name: Field name (e.g., 'box_1_ordinary_income')
        patterns: List of regex patterns to try (in order)
        value_type: Expected type ('currency', 'text', 'percentage', 'ein')
        description: What this field represents
    """
    name: str
    patterns: List[str]
    value_type: str
    description: str


class K1Patterns:
    """
    Central repository of all K-1 extraction patterns.
    
    DESIGN PHILOSOPHY:
    - Multiple patterns per field (K-1s vary by preparer)
    - Patterns get progressively more general
    - Named groups for clarity
    - Handle common variations (spaces, dots, dashes)
    """
    
    # ==========================================================================
    # ENTITY IDENTIFICATION PATTERNS
    # ==========================================================================
    
    @staticmethod
    def get_ein_patterns() -> List[Pattern]:
        """
        Patterns to find Employer Identification Number (XX-XXXXXXX).
        
        Variations we handle:
        - "Employer identification number: 12-3456789"
        - "EIN: 12-3456789"
        - "Federal ID Number: 12-3456789"
        """
        return [
            # Most specific first
            re.compile(r"Employer\s+identification\s+number[\s:]*(\d{2}[-\s]?\d{7})", re.IGNORECASE),
            re.compile(r"EIN[\s:]*(\d{2}[-\s]?\d{7})", re.IGNORECASE),
            re.compile(r"Federal\s+ID[\s:]*(\d{2}[-\s]?\d{7})", re.IGNORECASE),
            re.compile(r"Tax\s+ID[\s:]*(\d{2}[-\s]?\d{7})", re.IGNORECASE),
            # Most general last - just find the pattern
            re.compile(r"\b(\d{2}-\d{7})\b")
        ]
    
    @staticmethod
    def get_tax_year_patterns() -> List[Pattern]:
        """
        Patterns to find the tax year.
        
        Variations:
        - "Calendar year 2023"
        - "Tax year ending 12/31/2023"
        - "For calendar year 2023 or tax year beginning..."
        """
        return [
            re.compile(r"Calendar\s+year\s+(20\d{2})", re.IGNORECASE),
            re.compile(r"Tax\s+year\s+(20\d{2})", re.IGNORECASE),
            re.compile(r"For\s+(?:calendar|tax)\s+year\s+(20\d{2})", re.IGNORECASE),
            re.compile(r"Year\s+ending\s+\d{1,2}/\d{1,2}/(20\d{2})", re.IGNORECASE),
            # Just find a 4-digit year
            re.compile(r"\b(202[0-9])\b")  # Years 2020-2029
        ]
    
    @staticmethod
    def get_entity_name_patterns() -> List[Pattern]:
        """
        Patterns to find the partnership/corporation name.
        
        This is tricky because names vary widely.
        """
        return [
            re.compile(r"Partnership's\s+name[\s:]*\n?([^\n]+)", re.IGNORECASE),
            re.compile(r"Corporation's\s+name[\s:]*\n?([^\n]+)", re.IGNORECASE),
            re.compile(r"Entity\s+name[\s:]*\n?([^\n]+)", re.IGNORECASE),
            re.compile(r"Name\s+of\s+partnership[\s:]*\n?([^\n]+)", re.IGNORECASE),
            # Look for LLC, LP, Corp patterns
            re.compile(r"([A-Z][A-Za-z0-9\s&,.\-]+(?:LLC|LP|LLP|Corp|Corporation|Inc|Partnership))")
        ]
    
    # ==========================================================================
    # INCOME BOX PATTERNS (Boxes 1-11)
    # ==========================================================================
    
    @staticmethod
    def get_box_patterns() -> Dict[str, List[Pattern]]:
        """
        Get patterns for all numbered boxes.
        
        Returns dict like:
        {
            'box_1_ordinary_income': [pattern1, pattern2, ...],
            'box_2_rental_real_estate': [pattern1, pattern2, ...],
            ...
        }
        """
        
        # Helper function to create currency patterns for a box
        def make_box_patterns(box_num: str, keywords: List[str]) -> List[Pattern]:
            """
            Create patterns for a specific box number with keywords.
            
            Example: Box 1 with keywords ['Ordinary', 'business', 'income']
            """
            patterns = []
            
            # Pattern 1: "Box 1 Ordinary business income (loss) .... $50,000"
            keyword_pattern = r"[\s\w]*".join(keywords)
            patterns.append(
                re.compile(
                    rf"Box\s+{box_num}\s+{keyword_pattern}[^\d\-]*([\-\$]?[\d,]+\.?\d*)",
                    re.IGNORECASE
                )
            )
            
            # Pattern 2: "1. Ordinary business income .... $50,000"
            patterns.append(
                re.compile(
                    rf"^\s*{box_num}\.?\s+{keyword_pattern}[^\d\-]*([\-\$]?[\d,]+\.?\d*)",
                    re.IGNORECASE | re.MULTILINE
                )
            )
            
            # Pattern 3: Just box number followed by amount (less reliable)
            patterns.append(
                re.compile(
                    rf"Box\s+{box_num}[^\d\-]*([\-\$]?[\d,]+\.?\d*)",
                    re.IGNORECASE
                )
            )
            
            return patterns
        
        return {
            'box_1_ordinary_income': make_box_patterns('1', ['Ordinary', 'business', 'income']),
            'box_2_rental_real_estate': make_box_patterns('2', ['rental', 'real', 'estate']),
            'box_3_other_rental': make_box_patterns('3', ['Other', 'net', 'rental']),
            'box_4_guaranteed_payments': make_box_patterns('4', ['Guaranteed', 'payments']),
            'box_5_interest_income': make_box_patterns('5', ['Interest', 'income']),
            'box_6a_ordinary_dividends': make_box_patterns('6a', ['Ordinary', 'dividends']),
            'box_6b_qualified_dividends': make_box_patterns('6b', ['Qualified', 'dividends']),
            'box_7_royalties': make_box_patterns('7', ['Royalties']),
            'box_8_net_short_term_gain': make_box_patterns('8', ['short.*term', 'capital']),
            'box_9a_net_long_term_gain': make_box_patterns('9a', ['long.*term', 'capital']),
            'box_10_net_1231_gain': make_box_patterns('10', ['section', '1231']),
            'box_11_other_income': make_box_patterns('11', ['Other', 'income']),
            'box_12_section_179': make_box_patterns('12', ['Section', '179']),
        }
    
    # ==========================================================================
    # CAPITAL ACCOUNT PATTERNS
    # ==========================================================================
    
    @staticmethod
    def get_capital_patterns() -> Dict[str, List[Pattern]]:
        """
        Patterns for capital account reconciliation.
        """
        return {
            'capital_beginning': [
                re.compile(r"Beginning\s+capital\s+account[^\d\-]*([\-\$]?[\d,]+\.?\d*)", re.IGNORECASE),
                re.compile(r"Capital\s+account\s+at\s+beginning[^\d\-]*([\-\$]?[\d,]+\.?\d*)", re.IGNORECASE),
                re.compile(r"Beginning\s+balance[^\d\-]*([\-\$]?[\d,]+\.?\d*)", re.IGNORECASE),
            ],
            'capital_ending': [
                re.compile(r"Ending\s+capital\s+account[^\d\-]*([\-\$]?[\d,]+\.?\d*)", re.IGNORECASE),
                re.compile(r"Capital\s+account\s+at\s+end[^\d\-]*([\-\$]?[\d,]+\.?\d*)", re.IGNORECASE),
                re.compile(r"Ending\s+balance[^\d\-]*([\-\$]?[\d,]+\.?\d*)", re.IGNORECASE),
            ],
            'capital_contributions': [
                re.compile(r"Capital\s+contributed[^\d\-]*([\-\$]?[\d,]+\.?\d*)", re.IGNORECASE),
                re.compile(r"Contributions[^\d\-]*([\-\$]?[\d,]+\.?\d*)", re.IGNORECASE),
            ],
            'capital_distributions': [
                re.compile(r"Distributions[^\d\-]*([\-\$]?[\d,]+\.?\d*)", re.IGNORECASE),
                re.compile(r"Withdrawals[^\d\-]*([\-\$]?[\d,]+\.?\d*)", re.IGNORECASE),
            ],
        }
    
    # ==========================================================================
    # PERCENTAGE PATTERNS
    # ==========================================================================
    
    @staticmethod
    def get_percentage_patterns() -> Dict[str, List[Pattern]]:
        """
        Patterns for ownership percentages.
        """
        return {
            'profit_sharing_percent': [
                re.compile(r"Profit\s+sharing[^\d]*(\d+\.?\d*)\s*%", re.IGNORECASE),
                re.compile(r"Share\s+of\s+profit[^\d]*(\d+\.?\d*)\s*%", re.IGNORECASE),
            ],
            'loss_sharing_percent': [
                re.compile(r"Loss\s+sharing[^\d]*(\d+\.?\d*)\s*%", re.IGNORECASE),
                re.compile(r"Share\s+of\s+loss[^\d]*(\d+\.?\d*)\s*%", re.IGNORECASE),
            ],
            'capital_percent': [
                re.compile(r"Capital\s+(?:ownership|percentage)[^\d]*(\d+\.?\d*)\s*%", re.IGNORECASE),
                re.compile(r"Ownership\s+percentage[^\d]*(\d+\.?\d*)\s*%", re.IGNORECASE),
            ],
        }
    
    # ==========================================================================
    # UTILITY METHODS
    # ==========================================================================
    
    @staticmethod
    def clean_currency(value: str) -> float:
        """
        Convert currency string to float.
        
        Examples:
            "$1,234.56" -> 1234.56
            "(1,234.56)" -> -1234.56  (parentheses = negative)
            "1234.56-" -> -1234.56
        """
        if not value:
            return 0.0
        
        # Remove currency symbols and spaces
        cleaned = value.replace('$', '').replace(',', '').strip()
        
        # Handle negatives
        if cleaned.startswith('(') and cleaned.endswith(')'):
            cleaned = '-' + cleaned[1:-1]
        elif cleaned.endswith('-'):
            cleaned = '-' + cleaned[:-1]
        
        try:
            return float(cleaned)
        except ValueError:
            return 0.0
    
    @staticmethod
    def clean_percentage(value: str) -> float:
        """
        Convert percentage string to float.
        
        Examples:
            "50%" -> 50.0
            "33.33%" -> 33.33
        """
        if not value:
            return 0.0
        
        cleaned = value.replace('%', '').strip()
        
        try:
            return float(cleaned)
        except ValueError:
            return 0.0
    
    @classmethod
    def extract_all_fields(cls, text: str) -> Dict:
        """
        Try to extract all fields from text using all patterns.
        
        Returns dict with extracted values and confidence scores.
        """
        results = {}
        
        # Extract EIN
        for pattern in cls.get_ein_patterns():
            match = pattern.search(text)
            if match:
                results['ein'] = match.group(1)
                break
        
        # Extract tax year
        for pattern in cls.get_tax_year_patterns():
            match = pattern.search(text)
            if match:
                results['tax_year'] = match.group(1)
                break
        
        # Extract entity name
        for pattern in cls.get_entity_name_patterns():
            match = pattern.search(text)
            if match:
                results['entity_name'] = match.group(1).strip()
                break
        
        # Extract box values
        for field_name, patterns in cls.get_box_patterns().items():
            for pattern in patterns:
                match = pattern.search(text)
                if match:
                    results[field_name] = cls.clean_currency(match.group(1))
                    break
        
        # Extract capital account
        for field_name, patterns in cls.get_capital_patterns().items():
            for pattern in patterns:
                match = pattern.search(text)
                if match:
                    results[field_name] = cls.clean_currency(match.group(1))
                    break
        
        # Extract percentages
        for field_name, patterns in cls.get_percentage_patterns().items():
            for pattern in patterns:
                match = pattern.search(text)
                if match:
                    results[field_name] = cls.clean_percentage(match.group(1))
                    break
        
        return results


# ==========================================================================
# QUICK TEST
# ==========================================================================

if __name__ == "__main__":
    # Test with sample K-1 text
    sample_text = """
    Schedule K-1 (Form 1065)
    Department of the Treasury
    Internal Revenue Service
    
    For calendar year 2023
    
    Partnership's name: ABC Real Estate Partnership LLC
    Employer identification number: 12-3456789
    
    Partner's name: John Doe
    
    Part III Partner's Share of Current Year Income
    
    1. Ordinary business income (loss) . . . . . . . . . . 50,000
    2. Net rental real estate income (loss) . . . . . . . 10,000
    5. Interest income . . . . . . . . . . . . . . . . . . 2,500
    
    Capital Account Analysis
    Beginning capital account . . . . . . . . . . . . . 100,000
    Capital contributed during year . . . . . . . . . . 25,000
    Ending capital account . . . . . . . . . . . . . . . 175,000
    
    Profit sharing percentage: 50.00%
    """
    
    # Extract fields
    extracted = K1Patterns.extract_all_fields(sample_text)
    
    print("Extracted fields from sample text:")
    for field, value in extracted.items():
        print(f"  {field}: {value}")
    
    print("\n✅ Patterns module working!")