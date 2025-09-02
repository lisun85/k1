from extractor import K1Extractor
import pdfplumber

def test_both_extraction_methods():
    """Test both the original and enhanced coordinate extraction"""
    
    print("="*70)
    print("TESTING K-1 EXTRACTION METHODS")
    print("="*70)
    
    extractor = K1Extractor(verbose=True)
    pdf_path = "Input/Input_Enviva_Sample_Tax_Package_10000_units-2.pdf"
    
    # Test original coordinate extraction
    print("\n1. ORIGINAL COORDINATE EXTRACTION:")
    print("-"*50)
    coord_fields_v1 = extractor._extract_with_coordinates(pdf_path)
    print(f"Extracted {len(coord_fields_v1)} fields")
    
    # Test enhanced coordinate extraction
    print("\n2. ENHANCED COORDINATE EXTRACTION:")
    print("-"*50)
    coord_fields_v2 = extractor._extract_with_coordinates_v2(pdf_path)
    print(f"Extracted {len(coord_fields_v2)} fields")
    
    # Test simple extraction
    print("\n3. SIMPLE TEXT-BASED EXTRACTION:")
    print("-"*50)
    simple_fields = extractor._extract_k1_simple(pdf_path)
    print(f"Extracted {len(simple_fields)} fields")
    for field, value in simple_fields.items():
        print(f"  {field}: {value}")
    
    # Compare results
    print("\n4. COMPARISON OF METHODS:")
    print("-"*50)
    
    key_fields = [
        ('box_1_ordinary_income', -27942),
        ('box_19_distributions', 25100),
        ('capital_beginning', 271500),
        ('capital_ending', 207584),
        ('capital_distributions', 25100),
    ]
    
    print("\nField                     | Original | Enhanced | Simple   | Expected")
    print("-"*75)
    for field, expected in key_fields:
        v1_val = coord_fields_v1.get(field, 'Missing')
        v2_val = coord_fields_v2.get(field, 'Missing')
        v3_val = simple_fields.get(field, 'Missing')
        
        # Format values for display
        v1_str = f"{v1_val:,.0f}" if isinstance(v1_val, (int, float)) else str(v1_val)
        v2_str = f"{v2_val:,.0f}" if isinstance(v2_val, (int, float)) else str(v2_val)
        v3_str = f"{v3_val:,.0f}" if isinstance(v3_val, (int, float)) else str(v3_val)
        exp_str = f"{expected:,.0f}"
        
        # Check marks
        v1_check = "✓" if v1_val == expected else "✗"
        v2_check = "✓" if v2_val == expected else "✗"
        v3_check = "✓" if v3_val == expected else "✗"
        
        print(f"{field:<25} | {v1_str:<8} {v1_check} | {v2_str:<8} {v2_check} | {v3_str:<8} {v3_check} | {exp_str}")
    
    # Debug: Look for specific values in the PDF
    print("\n5. SEARCHING FOR SPECIFIC VALUES IN PDF:")
    print("-"*50)
    
    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[0]
        words = page.extract_words()
        
        # Look for key values
        search_values = {
            '-27,942': 'Box 1 value',
            '25,100': 'Box 19/Distributions',
            '271,500': 'Beginning capital',
            '207,584': 'Ending capital',
        }
        
        for value, description in search_values.items():
            found = False
            for word in words:
                if value in word['text'] or value.replace(',', '') in word['text']:
                    print(f"✓ Found {description}: '{word['text']}' at x={word['x0']:.1f}, y={word['top']:.1f}")
                    found = True
                    break
            if not found:
                # Try without comma
                for word in words:
                    if value.replace(',', '') == word['text']:
                        print(f"✓ Found {description}: '{word['text']}' at x={word['x0']:.1f}, y={word['top']:.1f}")
                        found = True
                        break
            if not found:
                print(f"✗ Could not find {description} ({value})")

if __name__ == "__main__":
    test_both_extraction_methods()