"""
table_extractor.py - Table Extraction for K-1 Forms
===================================================
Extracts structured data from tables in K-1 PDFs using Camelot and Tabula.

Many K-1s format data in tables, especially:
- Capital account reconciliation
- Income/deduction items with codes
- Partner information sections
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import re
import camelot
import tabula
from pathlib import Path

class TableExtractor:
    """
    Extracts data from tables in K-1 PDFs.
    
    Strategy:
    1. Use Camelot for bordered tables (more accurate)
    2. Fall back to Tabula for borderless tables
    3. Parse tables to find K-1 fields
    4. Return structured data
    """
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        
        # Common K-1 table headers we're looking for
        self.k1_table_patterns = {
            'capital_account': [
                'beginning capital',
                'capital contributed',
                'current year increase',
                'withdrawals',
                'distributions',
                'ending capital'
            ],
            'income_items': [
                'ordinary business income',
                'rental real estate',
                'interest income',
                'dividends',
                'royalties',
                'capital gain'
            ],
            'deductions': [
                'section 179',
                'other deductions',
                'depletion'
            ],
            'ownership': [
                'profit',
                'loss',
                'capital',
                'percentage'
            ]
        }
    
    def log(self, message: str):
        """Print log messages if verbose mode is on."""
        if self.verbose:
            print(f"[TableExtractor] {message}")
    
    def extract_tables(self, pdf_path: str) -> Dict:
        """
        Main method to extract all tables from PDF.
        
        Returns:
            Dictionary with extracted K-1 fields from tables
        """
        extracted_data = {}
        
        # Try Camelot first (better for bordered tables)
        self.log("Trying Camelot extraction...")
        camelot_data = self._extract_with_camelot(pdf_path)
        if camelot_data:
            extracted_data.update(camelot_data)
            self.log(f"Camelot extracted {len(camelot_data)} fields")
        
        # Try Tabula as well (better for borderless tables)
        self.log("Trying Tabula extraction...")
        tabula_data = self._extract_with_tabula(pdf_path)
        if tabula_data:
            # Only add fields not already found by Camelot
            for key, value in tabula_data.items():
                if key not in extracted_data:
                    extracted_data[key] = value
            self.log(f"Tabula extracted {len(tabula_data)} additional fields")
        
        return extracted_data
    
    def _extract_with_camelot(self, pdf_path: str) -> Dict:
        """
        Extract tables using Camelot.
        
        Camelot is better for:
        - Tables with clear borders
        - Multi-page tables
        - Complex table structures
        """
        extracted_data = {}
        
        try:
            # Read tables from all pages
            tables = camelot.read_pdf(
                pdf_path,
                pages='all',
                flavor='lattice',  # For bordered tables
                suppress_stdout=True
            )
            
            if len(tables) == 0:
                # Try stream flavor for borderless tables
                tables = camelot.read_pdf(
                    pdf_path,
                    pages='all',
                    flavor='stream',
                    suppress_stdout=True
                )
            
            self.log(f"Found {len(tables)} tables with Camelot")
            
            # Process each table
            for i, table in enumerate(tables):
                df = table.df
                self.log(f"Processing table {i+1}: shape {df.shape}")
                
                # Extract K-1 fields from this table
                table_data = self._parse_table_for_k1_fields(df)
                extracted_data.update(table_data)
                
        except Exception as e:
            self.log(f"Camelot extraction failed: {e}")
        
        return extracted_data
    
    def _extract_with_tabula(self, pdf_path: str) -> Dict:
        """
        Extract tables using Tabula.
        
        Tabula is better for:
        - Borderless tables
        - Simple table structures
        - Tables with merged cells
        """
        extracted_data = {}
        
        try:
            # Read all tables from the PDF
            dfs = tabula.read_pdf(
                pdf_path,
                pages='all',
                multiple_tables=True,
                pandas_options={'header': None},  # Don't assume first row is header
                silent=True
            )
            
            self.log(f"Found {len(dfs)} tables with Tabula")
            
            # Process each table
            for i, df in enumerate(dfs):
                if df.empty:
                    continue
                    
                self.log(f"Processing table {i+1}: shape {df.shape}")
                
                # Extract K-1 fields from this table
                table_data = self._parse_table_for_k1_fields(df)
                extracted_data.update(table_data)
                
        except Exception as e:
            self.log(f"Tabula extraction failed: {e}")
        
        return extracted_data
    
    def _parse_table_for_k1_fields(self, df: pd.DataFrame) -> Dict:
        """
        Parse a dataframe table to extract K-1 fields.
        
        Strategies:
        1. Look for key-value pairs (label in col 0, value in col 1)
        2. Look for specific K-1 patterns
        3. Handle capital account tables
        4. Handle income/deduction tables with box numbers
        """
        extracted_data = {}
        
        # Clean the dataframe
        df = self._clean_dataframe(df)
        
        if df.empty:
            return extracted_data
        
        # Strategy 1: Look for capital account table
        capital_data = self._extract_capital_account(df)
        if capital_data:
            extracted_data.update(capital_data)
        
        # Strategy 2: Look for income boxes (Box 1, Box 2, etc.)
        box_data = self._extract_box_values(df)
        if box_data:
            extracted_data.update(box_data)
        
        # Strategy 3: Look for percentages
        percentage_data = self._extract_percentages(df)
        if percentage_data:
            extracted_data.update(percentage_data)
        
        # Strategy 4: Look for EIN/SSN
        id_data = self._extract_identifiers(df)
        if id_data:
            extracted_data.update(id_data)
        
        return extracted_data
    
    def _clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and prepare dataframe for parsing."""
        # Remove empty rows and columns
        df = df.dropna(how='all').dropna(axis=1, how='all')
        
        # Convert all cells to string
        df = df.astype(str)
        
        # Replace 'nan' strings with empty strings
        df = df.replace('nan', '')
        
        # Strip whitespace
        df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)
        
        return df
    
    def _extract_capital_account(self, df: pd.DataFrame) -> Dict:
        """Extract capital account information from table."""
        extracted = {}
        
        # Convert dataframe to string for pattern matching
        table_text = df.to_string().lower()
        
        # Check if this looks like a capital account table
        if 'capital' not in table_text and 'beginning' not in table_text:
            return extracted
        
        # Look through each row
        for idx, row in df.iterrows():
            row_text = ' '.join(str(cell).lower() for cell in row)
            
            # Beginning capital
            if 'beginning' in row_text and 'capital' in row_text:
                value = self._extract_currency_from_row(row)
                if value:
                    extracted['capital_beginning'] = value
            
            # Ending capital
            elif 'ending' in row_text and 'capital' in row_text:
                value = self._extract_currency_from_row(row)
                if value:
                    extracted['capital_ending'] = value
            
            # Contributions
            elif 'contribut' in row_text:
                value = self._extract_currency_from_row(row)
                if value:
                    extracted['capital_contributions'] = value
            
            # Distributions
            elif 'distribution' in row_text or 'withdrawal' in row_text:
                value = self._extract_currency_from_row(row)
                if value:
                    extracted['capital_distributions'] = value
        
        return extracted
    
    def _extract_box_values(self, df: pd.DataFrame) -> Dict:
        """Extract values for numbered boxes (Box 1, Box 2, etc.)."""
        extracted = {}
        
        # Pattern for box numbers
        box_pattern = re.compile(r'box\s*(\d+[a-z]?)', re.IGNORECASE)
        
        for idx, row in df.iterrows():
            row_text = ' '.join(str(cell) for cell in row)
            
            # Look for box numbers
            match = box_pattern.search(row_text)
            if match:
                box_num = match.group(1).lower()
                value = self._extract_currency_from_row(row)
                
                if value is not None:
                    # Map to our field names
                    field_map = {
                        '1': 'box_1_ordinary_income',
                        '2': 'box_2_rental_real_estate',
                        '3': 'box_3_other_rental',
                        '4': 'box_4_guaranteed_payments',
                        '5': 'box_5_interest_income',
                        '6a': 'box_6a_ordinary_dividends',
                        '6b': 'box_6b_qualified_dividends',
                        '7': 'box_7_royalties',
                        '8': 'box_8_net_short_term_gain',
                        '9a': 'box_9a_net_long_term_gain',
                        '11': 'box_11_other_income',
                        '12': 'box_12_section_179'
                    }
                    
                    if box_num in field_map:
                        extracted[field_map[box_num]] = value
        
        return extracted
    
    def _extract_percentages(self, df: pd.DataFrame) -> Dict:
        """Extract ownership percentages from table."""
        extracted = {}
        
        for idx, row in df.iterrows():
            row_text = ' '.join(str(cell).lower() for cell in row)
            
            # Profit percentage
            if 'profit' in row_text and '%' in row_text:
                value = self._extract_percentage_from_row(row)
                if value:
                    extracted['profit_sharing_percent'] = value
            
            # Loss percentage
            elif 'loss' in row_text and '%' in row_text:
                value = self._extract_percentage_from_row(row)
                if value:
                    extracted['loss_sharing_percent'] = value
            
            # Capital percentage
            elif 'capital' in row_text and '%' in row_text:
                value = self._extract_percentage_from_row(row)
                if value:
                    extracted['capital_percent'] = value
        
        return extracted
    
    def _extract_identifiers(self, df: pd.DataFrame) -> Dict:
        """Extract EIN, SSN, and other identifiers from table."""
        extracted = {}
        
        # EIN pattern
        ein_pattern = re.compile(r'\d{2}-?\d{7}')
        
        # SSN pattern
        ssn_pattern = re.compile(r'\d{3}-?\d{2}-?\d{4}')
        
        for idx, row in df.iterrows():
            row_text = ' '.join(str(cell) for cell in row)
            
            # Look for EIN
            if 'ein' in row_text.lower() or 'employer' in row_text.lower():
                ein_match = ein_pattern.search(row_text)
                if ein_match:
                    extracted['ein'] = ein_match.group()
            
            # Look for SSN
            if 'ssn' in row_text.lower() or 'social' in row_text.lower():
                ssn_match = ssn_pattern.search(row_text)
                if ssn_match:
                    extracted['partner_ssn'] = ssn_match.group()
        
        return extracted
    
    def _extract_currency_from_row(self, row: pd.Series) -> Optional[float]:
        """Extract currency value from a table row."""
        # Pattern for currency values
        currency_pattern = re.compile(r'[\$\s]*([\d,]+\.?\d*)\s*[\)\-]?')
        
        # Check each cell in the row
        for cell in row:
            cell_str = str(cell)
            
            # Skip if not numeric-looking
            if not any(char.isdigit() for char in cell_str):
                continue
            
            # Try to extract currency
            match = currency_pattern.search(cell_str)
            if match:
                try:
                    # Clean and convert to float
                    value_str = match.group(1).replace(',', '')
                    value = float(value_str)
                    
                    # Check for negative (parentheses or trailing dash)
                    if '(' in cell_str or cell_str.strip().endswith('-'):
                        value = -value
                    
                    return value
                except ValueError:
                    continue
        
        return None
    
    def _extract_percentage_from_row(self, row: pd.Series) -> Optional[float]:
        """Extract percentage value from a table row."""
        # Pattern for percentage values
        percentage_pattern = re.compile(r'([\d\.]+)\s*%')
        
        for cell in row:
            cell_str = str(cell)
            match = percentage_pattern.search(cell_str)
            if match:
                try:
                    return float(match.group(1))
                except ValueError:
                    continue
        
        return None


# Test the table extractor
if __name__ == "__main__":
    import sys
    
    print("🔬 Testing Table Extractor\n")
    
    # Test with a sample PDF if provided
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
        
        if Path(pdf_path).exists():
            extractor = TableExtractor(verbose=True)
            results = extractor.extract_tables(pdf_path)
            
            print("\n📊 Extracted fields from tables:")
            for field, value in results.items():
                print(f"  {field}: {value}")
        else:
            print(f"❌ File not found: {pdf_path}")
    else:
        print("Usage: python table_extractor.py <pdf_path>")
        print("\nCreating mock table test...")
        
        # Test individual methods with mock data
        extractor = TableExtractor(verbose=True)
        
        # Create a mock dataframe that looks like a K-1 table
        mock_df = pd.DataFrame([
            ["Beginning capital account", "$100,000"],
            ["Capital contributed", "$25,000"],
            ["Ending capital account", "$175,000"],
            ["", ""],
            ["Box 1 Ordinary income", "$50,000"],
            ["Box 2 Rental income", "$10,000"],
            ["", ""],
            ["Profit percentage", "50.00%"],
            ["Loss percentage", "50.00%"]
        ])
        
        print("\nTesting with mock table:")
        print(mock_df)
        
        results = extractor._parse_table_for_k1_fields(mock_df)
        print("\n📊 Extracted from mock table:")
        for field, value in results.items():
            print(f"  {field}: {value}")