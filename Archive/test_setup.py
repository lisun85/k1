from models import K1Data, FormType, ExtractionResult

# Test creating a K-1 data object
k1 = K1Data(
    form_type=FormType.FORM_1065,
    tax_year="2023",
    ein="12-3456789",
    entity_name="Test Partnership LLC",
    box_1_ordinary_income=50000.00
)

print(k1.to_summary())
print(f"Total income: ${k1.get_total_income():,.2f}")
print(f"Completeness: {k1.get_completeness_score():.0%}")

# Test the result object
result = ExtractionResult(
    success=True,
    data=k1,
    processing_time=1.5
)
print(result)