"""
extractor.py - Main K-1 Extraction Engine
=========================================
Orchestrator that brings together PDF reading, OCR, 
pattern matching, and validation to extract K-1 data.

ARCHITECTURE:
1. Try multiple extraction methods
2. Merge results intelligently
3. Calculate confidence scores
4. Return structured data
"""

import os
import time
from typing import Dict, Optional, List, Tuple
from pathlib import Path
import re

# PDF processing
import pdfplumber
import PyPDF2
from PyPDF2 import PdfReader

# OCR
import pytesseract
from pdf2image import convert_from_path
from PIL import Image

# Our modules
from models import K1Data, ExtractionResult, FormType, ExtractionMethod
from patterns import K1Patterns

# For better logging
from datetime import datetime
import traceback


class K1Extractor:
    """
    Main K-1 extraction orchestrator.
    
    STRATEGY:
    1. Try PDF text extraction (fastest, most accurate)
    2. If that fails or has low confidence, try OCR
    3. Apply patterns to extracted text
    4. Validate and score results
    5. Return structured data
    """
    
    def __init__(self, verbose: bool = True):
        """
        Initialize the K-1 extractor.
        
        Args:
            verbose: Whether to print progress messages
        """
        self.verbose = verbose
        self.patterns = K1Patterns()
        
        # Track extraction statistics
        self.stats = {
            'pdfs_processed': 0,
            'successful_extractions': 0,
            'failed_extractions': 0,
            'avg_processing_time': 0
        }
    
    def log(self, message: str):
        """Print progress messages if verbose mode is on."""
        if self.verbose:
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] {message}")
    
    # ==========================================================================
    # MAIN EXTRACTION METHOD
    # ==========================================================================
    
    def extract_from_pdf(self, pdf_path: str) -> ExtractionResult:
        """
        Main extraction method - orchestrates the entire process.
        
        PSEUDOCODE:
        1. Validate file exists and is PDF
        2. Try text extraction
        3. If text extraction fails/insufficient, try OCR
        4. Apply patterns to extract fields
        5. Validate extracted data
        6. Calculate confidence scores
        7. Return results
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            ExtractionResult with extracted data or error information
        """
        start_time = time.time()
        self.log(f"📄 Starting extraction for: {os.path.basename(pdf_path)}")
        
        # Validate file
        if not os.path.exists(pdf_path):
            return ExtractionResult(
                success=False,
                error_message=f"File not found: {pdf_path}",
                processing_time=time.time() - start_time
            )
        
        # Get file metadata
        file_size_mb = os.path.getsize(pdf_path) / (1024 * 1024)
        file_name = os.path.basename(pdf_path)
        
        try:
            # Step 1: Try PDF text extraction
            self.log("🔍 Attempting PDF text extraction...")
            pdf_text, page_count = self._extract_pdf_text(pdf_path)
            
            # Check if we got meaningful text
            text_quality = self._assess_text_quality(pdf_text)
            self.log(f"📊 Text quality score: {text_quality:.0%}")
            
            # Step 2: If text quality is low, try OCR
            ocr_text = ""
            extraction_method = ExtractionMethod.PDF_TEXT
            
            if text_quality < 0.3:  # Less than 30% quality
                self.log("🔄 Text quality low, attempting OCR...")
                ocr_text = self._extract_with_ocr(pdf_path)
                if len(ocr_text) > len(pdf_text): # If OCR text is better than PDF text, use it. Using characters as a proxy for quality.
                    pdf_text = ocr_text
                    extraction_method = ExtractionMethod.OCR
                    self.log("✅ OCR provided better text")
            
            # Step 3: Extract fields using patterns
            self.log("🎯 Applying extraction patterns...")
            extracted_fields = self.patterns.extract_all_fields(pdf_text)
            
            # Step 4: Detect form type
            form_type = self._detect_form_type(pdf_text)
            self.log(f"📋 Detected form type: {form_type}")
            
            # Step 5: Create K1Data object
            k1_data = self._create_k1_data(
                extracted_fields, 
                form_type, 
                extraction_method,
                pdf_text
            )
            
            # Step 6: Calculate confidence score
            confidence = self._calculate_confidence(k1_data, extracted_fields)
            k1_data.confidence_score = confidence
            self.log(f"🎯 Overall confidence: {confidence:.0%}")
            
            # Step 7: Validate data
            validation_warnings = self._validate_k1_data(k1_data)
            if validation_warnings:
                k1_data.warnings.extend(validation_warnings)
                self.log(f"⚠️  {len(validation_warnings)} validation warnings")
            
            # Success!
            processing_time = time.time() - start_time
            self.log(f"✅ Extraction completed in {processing_time:.2f} seconds")
            
            return ExtractionResult(
                success=True,
                data=k1_data,
                processing_time=processing_time,
                extraction_method=extraction_method,
                page_count=page_count,
                file_name=file_name,
                file_size_mb=file_size_mb
            )
            
        except Exception as e:
            # Handle any unexpected errors
            error_msg = f"Extraction failed: {str(e)}"
            self.log(f"❌ {error_msg}")
            
            if self.verbose:
                traceback.print_exc()
            
            return ExtractionResult(
                success=False,
                error_message=error_msg,
                processing_time=time.time() - start_time,
                file_name=file_name,
                file_size_mb=file_size_mb
            )
    
    # ==========================================================================
    # PDF TEXT EXTRACTION
    # ==========================================================================
    
    def _extract_pdf_text(self, pdf_path: str) -> Tuple[str, int]:
        """
        Extract text from PDF using multiple methods.
        
        STRATEGY:
        1. Try pdfplumber (best for most PDFs)
        2. Fallback to PyPDF2 if needed
        3. Combine results from all pages
        
        Returns:
            Tuple of (extracted_text, page_count)
        """
        text = ""
        page_count = 0
        
        # Method 1: Try pdfplumber (usually best)
        try:
            with pdfplumber.open(pdf_path) as pdf:
                page_count = len(pdf.pages)
                
                for i, page in enumerate(pdf.pages):
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                        self.log(f"  📄 Extracted text from page {i+1}/{page_count}")
                    
                if text.strip():
                    return text, page_count
                    
        except Exception as e:
            self.log(f"  ⚠️  pdfplumber failed: {e}")
        
        # Method 2: Fallback to PyPDF2
        try:
            self.log("  🔄 Trying PyPDF2 as fallback...")
            reader = PdfReader(pdf_path)
            page_count = len(reader.pages)
            
            for i, page in enumerate(reader.pages):
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            
        except Exception as e:
            self.log(f"  ⚠️  PyPDF2 also failed: {e}")
        
        return text, page_count
    
    # ==========================================================================
    # OCR EXTRACTION
    # ==========================================================================
    
    def _extract_with_ocr(self, pdf_path: str) -> str:
        """
        Extract text using OCR for scanned PDFs.
        
        PROCESS:
        1. Convert PDF pages to images
        2. Preprocess images for better OCR
        3. Run Tesseract OCR
        4. Combine text from all pages
        
        Returns:
            Extracted text from OCR
        """
        try:
            # Convert PDF to images
            self.log("  🖼️  Converting PDF to images...")
            images = convert_from_path(pdf_path, dpi=300) # Can go lower or higher. 300 is a good starting point.
            
            full_text = ""
            for i, image in enumerate(images):
                self.log(f"  🔍 Running OCR on page {i+1}/{len(images)}...")
                
                # Preprocess image for better OCR
                processed_image = self._preprocess_image_for_ocr(image)
                
                # Run OCR with custom config for better accuracy
                custom_config = r'--oem 3 --psm 6'  # Use best OCR engine mode (3) and assume uniform block (6)
                page_text = pytesseract.image_to_string(
                    processed_image, 
                    config=custom_config
                )
                
                full_text += page_text + "\n"
            
            return full_text
            
        except Exception as e:
            self.log(f"  ❌ OCR failed: {e}")
            return ""
    
    def _preprocess_image_for_ocr(self, image: Image) -> Image:
        """
        Preprocess image to improve OCR accuracy.
        
        Techniques:
        - Convert to grayscale
        - Increase contrast
        - Remove noise
        - Straighten if needed
        """
        # Convert to grayscale
        image = image.convert('L')
        
        # Option to add more preprocessing here if needed:
        # - Deskewing
        # - Noise removal
        # - Contrast enhancement
        
        return image
    
    # ==========================================================================
    # FORM TYPE DETECTION
    # ==========================================================================
    
    def _detect_form_type(self, text: str) -> FormType:
        """
        Detect which type of K-1 form this is.
        
        Look for specific identifiers in the text.
        """
        text_lower = text.lower()
        
        if "form 1065" in text_lower or "schedule k-1 (form 1065)" in text_lower:
            return FormType.FORM_1065
        elif "form 1120s" in text_lower or "schedule k-1 (form 1120s)" in text_lower:
            return FormType.FORM_1120S
        elif "form 1041" in text_lower or "schedule k-1 (form 1041)" in text_lower:
            return FormType.FORM_1041
        else:
            # Try to guess based on content
            if "partnership" in text_lower:
                return FormType.FORM_1065
            elif "s corporation" in text_lower or "s-corporation" in text_lower:
                return FormType.FORM_1120S
            elif "estate" in text_lower or "trust" in text_lower:
                return FormType.FORM_1041
            
        return FormType.UNKNOWN
    
    # ==========================================================================
    # DATA CREATION & MAPPING
    # ==========================================================================
    
    def _create_k1_data(
        self, 
        extracted_fields: Dict, 
        form_type: FormType,
        extraction_method: ExtractionMethod,
        raw_text: str
    ) -> K1Data:
        """
        Create K1Data object from extracted fields.
        
        Maps extracted field names to K1Data attributes.
        """
        # Create K1Data with all extracted fields
        k1_data = K1Data(
            form_type=form_type,
            extraction_method=extraction_method,
            raw_text=raw_text[:5000] if raw_text else None  # Store first 5000 chars for debugging
        )
        
        # Map extracted fields to K1Data attributes
        field_mapping = {
            'ein': 'ein',
            'tax_year': 'tax_year',
            'entity_name': 'entity_name',
            'partner_name': 'partner_name',
            'box_1_ordinary_income': 'box_1_ordinary_income',
            'box_2_rental_real_estate': 'box_2_rental_real_estate',
            'box_3_other_rental': 'box_3_other_rental',
            'box_4_guaranteed_payments': 'box_4_guaranteed_payments',
            'box_5_interest_income': 'box_5_interest_income',
            'box_6a_ordinary_dividends': 'box_6a_ordinary_dividends',
            'box_6b_qualified_dividends': 'box_6b_qualified_dividends',
            'box_7_royalties': 'box_7_royalties',
            'box_8_net_short_term_gain': 'box_8_net_short_term_gain',
            'box_9a_net_long_term_gain': 'box_9a_net_long_term_gain',
            'box_10_net_1231_gain': 'box_10_net_1231_gain',
            'box_11_other_income': 'box_11_other_income',
            'box_12_section_179': 'box_12_section_179',
            'capital_beginning': 'capital_beginning',
            'capital_ending': 'capital_ending',
            'capital_contributions': 'capital_contributions',
            'capital_distributions': 'capital_distributions',
            'profit_sharing_percent': 'profit_sharing_percent',
            'loss_sharing_percent': 'loss_sharing_percent',
            'capital_percent': 'capital_percent',
        }
        
        # Set extracted values
        for extracted_key, model_attr in field_mapping.items():
            if extracted_key in extracted_fields:
                setattr(k1_data, model_attr, extracted_fields[extracted_key])
        
        return k1_data
    
    # ==========================================================================
    # CONFIDENCE SCORING
    # ==========================================================================
    
    def _calculate_confidence(self, k1_data: K1Data, extracted_fields: Dict) -> float:
        """
        Calculate overall confidence score for the extraction.
        
        Factors:
        - Completeness (how many fields were extracted)
        - Validation (do the numbers make sense)
        - Extraction method (PDF text is more reliable than OCR)
        - Text quality
        
        We can adjust the weights or add more factors later.
        """
        scores = []
        
        # 1. Completeness score (40% weight)
        completeness = k1_data.get_completeness_score()
        scores.append(completeness * 0.4)
        
        # 2. Critical fields present (30% weight)
        critical_fields = ['ein', 'tax_year', 'entity_name'] # Can add more fields later. Keep these as a baseline.
        critical_present = sum(
            1 for field in critical_fields 
            if getattr(k1_data, field) is not None
        )
        critical_score = critical_present / len(critical_fields)
        scores.append(critical_score * 0.3)
        
        # 3. Extraction method quality (20% weight)
        method_scores = {
            ExtractionMethod.PDF_TEXT: 1.0,
            ExtractionMethod.TABLE: 0.9,
            ExtractionMethod.LAYOUT: 0.8,
            ExtractionMethod.OCR: 0.7,
            ExtractionMethod.ML: 0.8,
            ExtractionMethod.MANUAL: 1.0
        }
        method_score = method_scores.get(k1_data.extraction_method, 0.5)
        scores.append(method_score * 0.2)
        
        # 4. Capital account validation (10% weight)
        if k1_data.validate_capital_account():
            scores.append(0.1)
        else:
            scores.append(0.05)  # Partial credit
        
        return min(sum(scores), 1.0)  # Cap at 100%
    
    def _assess_text_quality(self, text: str) -> float:
        """
        Assess the quality of extracted text.
        
        Indicators of good quality:
        - Contains expected keywords
        - Has reasonable length
        - Contains numbers
        - Has proper structure
        """
        if not text:
            return 0.0
        
        quality_score = 0.0
        
        # Check for K-1 keywords
        k1_keywords = [
            'schedule k-1', 'form 1065', 'form 1120s', 'form 1041',
            'ordinary business income', 'capital account', 
            'partner', 'shareholder', 'beneficiary'
        ]
        
        text_lower = text.lower()
        keywords_found = sum(1 for kw in k1_keywords if kw in text_lower)
        quality_score += min(keywords_found / 3, 1.0) * 0.4  # 40% weight
        
        # Check text length (expecting at least 500 characters)
        if len(text) > 2000:
            quality_score += 0.3  # 30% weight
        elif len(text) > 500:
            quality_score += 0.2
        
        # Check for numbers (K-1s have lots of numbers)
        numbers = re.findall(r'\d+', text)
        if len(numbers) > 20:
            quality_score += 0.3  # 30% weight
        elif len(numbers) > 10:
            quality_score += 0.2
        
        return min(quality_score, 1.0)
    
    # ==========================================================================
    # VALIDATION
    # ==========================================================================
    
    def _validate_k1_data(self, k1_data: K1Data) -> List[str]:
        """
        Validate extracted K-1 data for common issues.
        
        Returns:
            List of warning messages
        """
        warnings = []
        
        # Check EIN format
        if k1_data.ein:
            if not re.match(r'^\d{2}-\d{7}$', k1_data.ein):
                warnings.append(f"EIN format may be invalid: {k1_data.ein}")
        
        # Check tax year
        if k1_data.tax_year:
            try:
                year = int(k1_data.tax_year)
                if year < 2000 or year > 2030:
                    warnings.append(f"Tax year seems unusual: {year}")
            except:
                warnings.append(f"Tax year format invalid: {k1_data.tax_year}")
        
        # Check percentages
        for field in ['profit_sharing_percent', 'loss_sharing_percent', 'capital_percent']:
            value = getattr(k1_data, field)
            if value is not None and (value < 0 or value > 100):
                warnings.append(f"{field} outside valid range: {value}%")
        
        # Check capital account reconciliation
        if not k1_data.validate_capital_account():
            warnings.append("Capital account may not reconcile")
        
        # Check for negative values that shouldn't be negative
        if k1_data.capital_ending is not None and k1_data.capital_ending < 0:
            warnings.append("Ending capital account is negative")
        
        return warnings


# # ==========================================================================
# # QUICK TEST
# # ==========================================================================

# if __name__ == "__main__":
#     print("🚀 Testing K1 Extractor\n")
    
#     # Test with a sample PDF if you have one
#     test_pdf = "sample_k1.pdf"  # Replace with your test PDF
    
#     if os.path.exists(test_pdf):
#         extractor = K1Extractor(verbose=True)
#         result = extractor.extract_from_pdf(test_pdf)
        
#         if result.success:
#             print("\n✅ Extraction successful!")
#             print(f"📊 Summary: {result.data.to_summary()}")
#         else:
#             print(f"\n❌ Extraction failed: {result.error_message}")
#     else:
#         print(f"⚠️  No test PDF found at {test_pdf}")
#         print("\nCreating mock test...")
        
#         # Test with mock data
#         from models import K1Data, FormType, ExtractionMethod
        
#         extractor = K1Extractor(verbose=True)
        
#         # Test the individual components
#         print("Testing text quality assessment...")
#         sample_text = "Schedule K-1 (Form 1065) Partner's Share of Income Box 1 Ordinary business income 50000"
#         quality = extractor._assess_text_quality(sample_text)
#         print(f"  Text quality: {quality:.0%}")
        
#         print("\nTesting form type detection...")
#         form_type = extractor._detect_form_type(sample_text)
#         print(f"  Detected form: {form_type}")
        
#         print("\n✅ Extractor module ready!")