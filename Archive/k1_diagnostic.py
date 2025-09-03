"""
k1_diagnostic.py - Diagnose K-1 PDF extraction issues
=====================================================
"""

import pdfplumber
import re
from pathlib import Path


def diagnose_pdf(pdf_path: str):
    """Comprehensive diagnostic of PDF extraction issues"""
    
    print("="*80)
    print("K-1 PDF EXTRACTION DIAGNOSTIC")
    print("="*80)
    print(f"File: {pdf_path}")
    print("="*80)
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            print(f"\n📄 PDF Properties:")
            print(f"  Pages: {len(pdf.pages)}")
            print(f"  Metadata: {pdf.metadata}")
            
            if not pdf.pages:
                print("❌ ERROR: No pages found in PDF!")
                return
            
            page = pdf.pages[0]
            print(f"\n📐 Page Dimensions:")
            print(f"  Width: {page.width}")
            print(f"  Height: {page.height}")
            
            # Method 1: Extract raw text
            print("\n" + "="*80)
            print("METHOD 1: RAW TEXT EXTRACTION")
            print("="*80)
            
            text = page.extract_text()
            if text:
                print(f"✅ Text extracted: {len(text)} characters")
                
                # Show first 500 characters
                print("\nFirst 500 characters:")
                print("-"*40)
                print(text[:500])
                print("-"*40)
                
                # Check for key K-1 indicators
                print("\n🔍 Checking for K-1 form indicators:")
                indicators = {
                    "Schedule K-1": "schedule k-1" in text.lower(),
                    "Form 1065": "form 1065" in text.lower(),
                    "Partnership": "partnership" in text.lower(),
                    "Part I": "part i" in text.lower(),
                    "Part II": "part ii" in text.lower(),
                    "Part III": "part iii" in text.lower(),
                }
                
                for indicator, found in indicators.items():
                    status = "✅" if found else "❌"
                    print(f"  {status} {indicator}: {found}")
                
                # Look for specific values from Sample_MadeUp
                print("\n🔍 Looking for Sample_MadeUp specific values:")
                values_to_find = {
                    "Wayne Enterprises": "wayne enterprises" in text.lower(),
                    "Bruce Wayne": "bruce wayne" in text.lower(),
                    "12-3456789": "12-3456789" in text,
                    "123-45-6789": "123-45-6789" in text,
                    "100,000": "100,000" in text or "100000" in text,
                    "9,000": "9,000" in text or "9000" in text,
                    "50,000": "50,000" in text or "50000" in text,
                    "500,000": "500,000" in text or "500000" in text,
                    "559,000": "559,000" in text or "559000" in text,
                }
                
                for value, found in values_to_find.items():
                    status = "✅" if found else "❌"
                    print(f"  {status} {value}: {found}")
                
                # Analyze lines
                lines = text.split('\n')
                print(f"\n📝 Line Analysis:")
                print(f"  Total lines: {len(lines)}")
                
                # Show lines with actual data
                print("\n  Lines with numbers (potential values):")
                for i, line in enumerate(lines[:100]):  # Check first 100 lines
                    if re.search(r'\d{2,}', line):  # Lines with at least 2 digits
                        print(f"    Line {i}: {line[:80]}")
                
            else:
                print("❌ No text extracted!")
            
            # Method 2: Extract words with positions
            print("\n" + "="*80)
            print("METHOD 2: WORD EXTRACTION WITH POSITIONS")
            print("="*80)
            
            words = page.extract_words(x_tolerance=3, y_tolerance=3)
            if words:
                print(f"✅ Words extracted: {len(words)} words")
                
                # Show sample words
                print("\nFirst 20 words:")
                for i, word in enumerate(words[:20]):
                    print(f"  {i}: '{word['text']}' at ({word['x0']:.1f}, {word['top']:.1f})")
                
                # Look for specific words
                print("\n🔍 Looking for key values in words:")
                for word in words:
                    text = word['text']
                    if any(key in text.lower() for key in ['wayne', 'bruce', '100,000', '9,000', '12-3456789']):
                        print(f"  Found: '{text}' at position ({word['x0']:.1f}, {word['top']:.1f})")
                
            else:
                print("❌ No words extracted!")
            
            # Method 3: Extract tables
            print("\n" + "="*80)
            print("METHOD 3: TABLE EXTRACTION")
            print("="*80)
            
            tables = page.extract_tables()
            if tables:
                print(f"✅ Tables found: {len(tables)}")
                for i, table in enumerate(tables):
                    print(f"\nTable {i+1}: {len(table)} rows x {len(table[0]) if table else 0} columns")
                    # Show first few rows
                    for row in table[:5]:
                        print(f"  {row}")
            else:
                print("❌ No tables found!")
            
            # Method 4: Check for form fields
            print("\n" + "="*80)
            print("METHOD 4: FORM FIELDS CHECK")
            print("="*80)
            
            # Try to extract form fields if they exist
            if hasattr(page, 'annots') and page.annots:
                print(f"✅ Annotations found: {len(page.annots)}")
                for annot in page.annots[:10]:
                    print(f"  {annot}")
            else:
                print("❌ No form field annotations found")
            
            # Method 5: Check characters
            print("\n" + "="*80)
            print("METHOD 5: CHARACTER EXTRACTION")
            print("="*80)
            
            chars = page.chars
            if chars:
                print(f"✅ Characters extracted: {len(chars)}")
                
                # Analyze fonts
                fonts = set()
                for char in chars:
                    if 'fontname' in char:
                        fonts.add(char['fontname'])
                
                print(f"\n📝 Fonts used in document:")
                for font in fonts:
                    print(f"  - {font}")
                
                # Show sample characters
                print("\nFirst 50 characters:")
                text_from_chars = ''.join(char.get('text', '') for char in chars[:50])
                print(f"  {text_from_chars}")
            else:
                print("❌ No characters extracted!")
            
            # Method 6: Try different extraction settings
            print("\n" + "="*80)
            print("METHOD 6: ALTERNATIVE EXTRACTION SETTINGS")
            print("="*80)
            
            # Try with different tolerances
            print("\nTrying with loose tolerance (x=10, y=10):")
            words_loose = page.extract_words(x_tolerance=10, y_tolerance=10)
            text_loose = page.extract_text(x_tolerance=10, y_tolerance=10)
            if text_loose:
                print(f"✅ Text extracted: {len(text_loose)} characters")
                print("First 200 characters:")
                print(text_loose[:200])
            else:
                print("❌ Still no text extracted")
            
            # Check if PDF might be scanned (image-based)
            print("\n" + "="*80)
            print("PDF TYPE ANALYSIS")
            print("="*80)
            
            # Check if it's likely a scanned PDF
            has_text = bool(text)
            has_many_chars = len(chars) > 100 if chars else False
            has_images = bool(page.images) if hasattr(page, 'images') else False
            
            print(f"  Has extractable text: {has_text}")
            print(f"  Has many characters: {has_many_chars}")
            print(f"  Has embedded images: {has_images}")
            
            if not has_text and has_images:
                print("\n⚠️  This appears to be a SCANNED PDF (image-based)")
                print("  Extraction requires OCR (Optical Character Recognition)")
                print("  Standard text extraction will not work!")
            elif has_text and len(text) < 100:
                print("\n⚠️  Very little text extracted")
                print("  The PDF might be partially scanned or corrupted")
            elif has_text:
                print("\n✅ This appears to be a TEXT-BASED PDF")
                print("  Text extraction should work, but may need adjustment")
            
            # Final diagnosis
            print("\n" + "="*80)
            print("DIAGNOSIS SUMMARY")
            print("="*80)
            
            if not text or len(text) < 100:
                print("❌ PROBLEM: Cannot extract text from PDF")
                print("\nPossible causes:")
                print("1. PDF is scanned (image-based) - needs OCR")
                print("2. PDF is encrypted or protected")
                print("3. PDF uses non-standard encoding")
                print("4. PDF is corrupted")
                print("\nRecommended solutions:")
                print("1. Try OCR extraction with pytesseract")
                print("2. Re-save the PDF using Adobe Acrobat or similar")
                print("3. Check if PDF requires password")
                print("4. Try online PDF to text converters to verify")
            else:
                print("✅ Text extraction is working")
                print("\nBut extraction logic may need adjustment for:")
                print("1. Field positioning and layout")
                print("2. Pattern matching for specific fields")
                print("3. Handling of multi-line values")
                
    except Exception as e:
        print(f"\n❌ ERROR during diagnostic: {e}")
        import traceback
        traceback.print_exc()


def main():
    import sys
    
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
    else:
        pdf_path = "Input/Sample_MadeUp.pdf"
    
    if not Path(pdf_path).exists():
        print(f"❌ File not found: {pdf_path}")
        return
    
    diagnose_pdf(pdf_path)


if __name__ == "__main__":
    main()