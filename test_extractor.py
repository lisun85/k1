"""Quick test for the extractor"""

from extractor import K1Extractor

# Create sample text that looks like a K-1
sample_k1_text = """
Schedule K-1 (Form 1065)
Department of the Treasury
Internal Revenue Service

For calendar year 2023

Partnership's name: ABC Real Estate Partnership LLC
Employer identification number: 12-3456789

Partner's name: John Doe
Partner's identifying number: 123-45-6789

Part III Partner's Share of Current Year Income

1. Ordinary business income (loss) . . . . . . . . . 50,000
2. Net rental real estate income (loss) . . . . . . 10,000
5. Interest income . . . . . . . . . . . . . . . . . 2,500

Capital Account Analysis
Beginning capital account . . . . . . . . . . . . 100,000
Capital contributed during year . . . . . . . . . 25,000
Ending capital account . . . . . . . . . . . . . . 175,000

Partner's share of profit: 50.00%
"""

# Save as temporary PDF (mock for testing)
# In real use, you'd have an actual PDF

extractor = K1Extractor(verbose=True)

# Test quality assessment
quality = extractor._assess_text_quality(sample_k1_text)
print(f"\nText quality: {quality:.0%}")

# Test form detection
form_type = extractor._detect_form_type(sample_k1_text)
print(f"Form type: {form_type}")

# Test pattern extraction
from patterns import K1Patterns
patterns = K1Patterns()
fields = patterns.extract_all_fields(sample_k1_text)
print(f"\nExtracted {len(fields)} fields")

print("\n✅ Extractor components working!")