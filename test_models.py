"""Test that our models work correctly"""

from models import K1Data, FormType, ExtractionResult, ExtractionMethod

# Test creating a K-1 with some data
k1 = K1Data(
    form_type=FormType.FORM_1065,
    tax_year="2023",
    ein="12-3456789",
    entity_name="ABC Partnership LLC",
    partner_name="John Doe",
    box_1_ordinary_income=50000.00,
    box_2_rental_real_estate=10000.00,
    capital_beginning=100000.00,
    capital_ending=110000.00,
    confidence_score=0.95
)

# Test the summary method
print("K-1 Summary:")
print(k1.to_summary())
print(f"\nTotal Income: ${k1.get_total_income():,.2f}")
print(f"Completeness: {k1.get_completeness_score():.0%}")

# Test the extraction result
result = ExtractionResult(
    success=True,
    data=k1,
    processing_time=1.5,
    extraction_method=ExtractionMethod.PDF_TEXT,
    file_name="test_k1.pdf"
)

print(f"\nExtraction Result: {result}")
print("Result Dict:", result.to_dict())

# Test validation
try:
    bad_k1 = K1Data(ein="invalid-ein")
except ValueError as e:
    print(f"\nValidation working: {e}")

print("\n✅ Models working correctly!")