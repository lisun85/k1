# Data structures
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

# ENUMS: Define the valid options for certain fields

class FormType(str, Enum):
    """
    The below are the types of K-1 form are we dealing with
    Different forms have slightly different fields and layouts.
    """
    FORM_1065 = "1065"    # Partnership K-1 (most common)
    FORM_1120S = "1120S"  # S-Corporation K-1  
    FORM_1041 = "1041"    # Estate/Trust K-1
    UNKNOWN = "unknown"   # Couldn't determine type


class ExtractionMethod(str, Enum):

    PDF_TEXT = "pdf_text"  # Best - digital PDF with selectable text
    OCR = "ocr"            # Good - scanned document, used Tesseract
    TABLE = "table"        # Good - found structured table
    LAYOUT = "layout"      # OK - used position-based extraction
    ML = "ml"              # Variable - used AI model
    MANUAL = "manual"      # Perfect - human entered

    "PDF is most reliable as its direct text extraction. ML and Manual are test cases"

# MAIN DATA MODEL: This is what we're extracting from every K-1

class K1Data(BaseModel):
    """
    The complete representation of a K-1 form in code.
    
    DESIGN DECISIONS:
    - Every field is Optional because extraction might fail partially
    - Using float for money (in production, might use Decimal)
    - Storing raw_text for debugging failed extractions
    - Including confidence_score to show extraction quality
    """
    
    # === METADATA (Info about the extraction itself) ===
    # PSEUDOCODE: Track HOW and WHEN we extracted this data
    form_type: FormType = FormType.UNKNOWN
    tax_year: Optional[str] = None  # "2023", "2024", etc.
    extraction_timestamp: datetime = Field(default_factory=datetime.now)
    extraction_method: ExtractionMethod = ExtractionMethod.PDF_TEXT
    confidence_score: float = Field(
        default=0.0, 
        ge=0.0,  # >= 0
        le=1.0   # <= 1  
    )
    
    # === ENTITY INFORMATION (The company/partnership) ===
    # PSEUDOCODE: Who issued this K-1?

    # NEW (Pydantic v2 style)
    ein: Optional[str] = Field(
        None, 
        description="Employer ID Number (XX-XXXXXXX)",
        pattern=r'^\d{2}-\d{7}$'  # ← CHANGED TO 'pattern'
    )    
    entity_name: Optional[str] = Field(
        None, 
        description="Partnership/Corporation name"
    )
    entity_address: Optional[str] = None
    
    # === PARTNER/SHAREHOLDER INFORMATION (The recipient) ===
    # PSEUDOCODE: Who is receiving this K-1?
    partner_name: Optional[str] = Field(
        None, 
        description="Partner/Shareholder name"
    )
    partner_ssn: Optional[str] = Field(
        None, 
        description="SSN (XXX-XX-XXXX) or EIN",
        # Note: In production, this should be encrypted
    )
    partner_address: Optional[str] = None
    
    # === INCOME SECTION (BOXES 1-11) ===
    # PSEUDOCODE: All the different types of income reported
    # Each box corresponds to a specific line on the tax return
    
    box_1_ordinary_income: Optional[float] = Field(
        None, 
        description="Ordinary business income (loss) - goes to Schedule E"
    )
    box_2_rental_real_estate: Optional[float] = Field(
        None, 
        description="Net rental real estate income (loss) - Schedule E"
    )
    box_3_other_rental: Optional[float] = Field(
        None, 
        description="Other net rental income (loss) - Schedule E"
    )
    box_4_guaranteed_payments: Optional[float] = Field(
        None, 
        description="Guaranteed payments for services"
    )
    box_5_interest_income: Optional[float] = Field(
        None, 
        description="Interest income - Schedule B"
    )
    box_6a_ordinary_dividends: Optional[float] = Field(
        None, 
        description="Ordinary dividends - Schedule B"
    )
    box_6b_qualified_dividends: Optional[float] = Field(
        None, 
        description="Qualified dividends - taxed at capital gains rate"
    )
    box_7_royalties: Optional[float] = Field(
        None, 
        description="Royalties - Schedule E"
    )
    box_8_net_short_term_gain: Optional[float] = Field(
        None, 
        description="Net short-term capital gain (loss) - Schedule D"
    )
    box_9a_net_long_term_gain: Optional[float] = Field(
        None, 
        description="Net long-term capital gain (loss) - Schedule D"
    )
    box_9b_collectibles_gain: Optional[float] = Field(
        None, 
        description="Collectibles (28%) gain (loss) - special tax rate"
    )
    box_9c_unrecaptured_1250: Optional[float] = Field(
        None, 
        description="Unrecaptured section 1250 gain - from property sales"
    )
    box_10_net_1231_gain: Optional[float] = Field(
        None, 
        description="Net section 1231 gain (loss) - Form 4797"
    )
    box_11_other_income: Optional[float] = Field(
        None, 
        description="Other income (loss) - various schedules"
    )
    
    # === DEDUCTIONS SECTION (BOXES 12-13) ===
    # PSEUDOCODE: Amounts that reduce taxable income
    box_12_section_179: Optional[float] = Field(
        None, 
        description="Section 179 deduction - equipment purchases"
    )
    box_13_other_deductions: Optional[Dict[str, float]] = Field(
        default_factory=dict,
        description="Other deductions - can have codes A, B, C, etc."
        # Example: {"A": 1000, "B": 500} for multiple deduction types
    )
    
    # === CREDITS & OTHER ITEMS ===
    # PSEUDOCODE: Tax credits and special items
    box_14_self_employment: Optional[float] = Field(
        None, 
        description="Self-employment earnings (loss) - Schedule SE"
    )
    box_15_credits: Optional[Dict[str, float]] = Field(
        default_factory=dict,
        description="Credits - can have multiple codes"
    )
    box_16_foreign_transactions: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Foreign taxes paid, income, etc."
    )
    box_17_amt_items: Optional[Dict[str, float]] = Field(
        default_factory=dict,
        description="Alternative minimum tax (AMT) items"
    )
    box_20_other: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Other information - codes with various data"
    )
    
    # === CAPITAL ACCOUNT SECTION ===
    # PSEUDOCODE: Track partner's investment in the partnership
    # Should reconcile: Beginning + Contributions - Distributions = Ending
    capital_beginning: Optional[float] = Field(
        None, 
        description="Beginning capital account balance"
    )
    capital_contributions: Optional[float] = Field(
        None, 
        description="Capital contributed during year"
    )
    capital_distributions: Optional[float] = Field(
        None, 
        description="Distributions/withdrawals during year"  
    )
    capital_ending: Optional[float] = Field(
        None, 
        description="Ending capital account balance"
    )
    
    # === OWNERSHIP PERCENTAGES ===
    # PSEUDOCODE: Partner's share of the entity
    profit_sharing_percent: Optional[float] = Field(
        None, 
        description="Profit sharing %", 
        ge=0,   # Can't be negative
        le=100  # Can't exceed 100%
    )
    loss_sharing_percent: Optional[float] = Field(
        None, 
        description="Loss sharing %", 
        ge=0, 
        le=100
    )
    capital_percent: Optional[float] = Field(
        None, 
        description="Capital ownership %", 
        ge=0, 
        le=100
    )

    # === DEBUG/AUDIT TRAIL ===
    # PSEUDOCODE: Keep raw data for debugging and validation
    raw_text: Optional[str] = Field(
        None, 
        description="Raw extracted text for debugging"
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="Non-critical issues during extraction"
    )
    errors: List[str] = Field(
        default_factory=list,
        description="Critical errors during extraction"
    )

    # === PYDANTIC CONFIGURATION ===
    class Config:
        "Tell Pydantic how to handle this model"
        json_encoders = {
            datetime: lambda v: v.isoformat()  # Convert datetime to string
        }
        schema_extra = {
            "example": {
                "form_type": "1065",
                "tax_year": "2023",
                "ein": "12-3456789",
                "entity_name": "ABC Partnership LLC",
                "box_1_ordinary_income": 50000.00
            }
        }

    # === BUSINESS LOGIC METHODS ===
    # PSEUDOCODE: Smart calculations on the extracted data
    
    def get_total_income(self) -> float:
        """
        Calculate total income from all income boxes.
        
        PSEUDOCODE:
        1. Collect all income fields (boxes 1-11)
        2. Filter out None values
        3. Sum all valid amounts
        4. Return total
        """
        income_fields = [
            self.box_1_ordinary_income,
            self.box_2_rental_real_estate,
            self.box_3_other_rental,
            self.box_4_guaranteed_payments,
            self.box_5_interest_income,
            self.box_6a_ordinary_dividends,
            self.box_7_royalties,
            self.box_8_net_short_term_gain,
            self.box_9a_net_long_term_gain,
            self.box_11_other_income
        ]
        # Only sum non-None values (fields we successfully extracted)
        return sum(f for f in income_fields if f is not None)
    
    def get_completeness_score(self) -> float:
        """
        Calculate how complete the extraction is (0-1 scale).
        
        PSEUDOCODE:
        1. Define "important" fields that should always be present
        2. Count how many we successfully extracted
        3. Return percentage as decimal
        
        This helps users know if they should manually review.
        """
        important_fields = [
            self.ein,               # Must have entity ID
            self.tax_year,          # Must know what year
            self.entity_name,       # Should have entity name
            self.partner_name,      # Should have partner name
            self.box_1_ordinary_income,  # Usually has income
            self.capital_ending     # Should have capital balance
        ]
        filled = sum(1 for f in important_fields if f is not None)
        total = len(important_fields)
        return filled / total if total > 0 else 0

    def validate_capital_account(self) -> bool:
        """
        Check if capital account reconciles.
        
        PSEUDOCODE:
        Formula: Beginning + Contributions + Income - Distributions = Ending
        
        Returns True if reconciles within $1 (rounding tolerance)
        """
        if all([
            self.capital_beginning is not None,
            self.capital_ending is not None,
            self.capital_distributions is not None
        ]):
            contributions = self.capital_contributions or 0
            distributions = self.capital_distributions or 0
            income = self.get_total_income()
            
            expected = self.capital_beginning + contributions + income - distributions
            actual = self.capital_ending
            
            # Allow $1 tolerance for rounding
            return abs(expected - actual) <= 1.0
        return True  # Can't validate if missing data
    
    def to_summary(self) -> Dict:
        """
        Get a human-readable summary of the K-1.
        
        PSEUDOCODE:
        1. Pull out key fields
        2. Format as readable dictionary
        3. Include calculated fields
        
        Used for quick display in UI.
        """
        return {
            "form_type": self.form_type.value if self.form_type else "Unknown",
            "tax_year": self.tax_year or "Unknown",
            "entity": self.entity_name or "Unknown Entity",
            "partner": self.partner_name or "Unknown Partner",
            "total_income": f"${self.get_total_income():,.2f}",
            "completeness": f"{self.get_completeness_score():.0%}",
            "confidence": f"{self.confidence_score:.0%}",
            "capital_reconciles": self.validate_capital_account()
        }
    
    @field_validator('ein')
    @classmethod
    def validate_ein(cls, v):
        """
        Validate EIN format (XX-XXXXXXX).
        """
        if v is None:
            return v
        # Remove spaces and validate format
        v = v.strip().replace(" ", "")
        if not v or len(v) != 10 or v[2] != '-':
            raise ValueError(f"Invalid EIN format: {v}")
        return v

# ==============================================================================
# EXTRACTION RESULT: Wrapper for the extraction process outcome
# ==============================================================================

class ExtractionResult(BaseModel):
    """
    Contains the result of attempting to extract a K-1.
    
    PSEUDOCODE:
    - If success=True: data contains extracted K1Data
    - If success=False: check errors for what went wrong
    - Always includes metadata about the extraction process
    """
    
    # Core result
    success: bool                          # Did extraction work?
    data: Optional[K1Data] = None         # The extracted data (if successful)
    
    # Process metadata
    processing_time: float = 0.0          # How long did extraction take?
    extraction_method: ExtractionMethod = ExtractionMethod.PDF_TEXT
    
    # File metadata
    page_count: int = 0                   # How many pages in the PDF?
    file_name: str = ""                   # What file did we process?
    file_size_mb: float = 0.0            # How large was the file?
    
    # Error tracking
    error_message: Optional[str] = None   # What went wrong (if failed)?
    warnings: List[str] = Field(default_factory=list)
    
    def __str__(self) -> str:
        """
        Human-readable representation.
        
        PSEUDOCODE:
        - If successful: ✅ Show form type and year
        - If failed: ❌ Show error message
        """
        if self.success and self.data:
            return f"✅ Extracted {self.data.form_type.value} for {self.data.tax_year}"
        return f"❌ Extraction failed: {self.error_message or 'Unknown error'}"
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        result = {
            "success": self.success,
            "processing_time": f"{self.processing_time:.2f}s",
            "method": self.extraction_method.value,
            "file": self.file_name
        }
        
        if self.success and self.data:
            result["data"] = self.data.to_summary()
        else:
            result["error"] = self.error_message
            
        return result


# ==============================================================================
# BATCH PROCESSING: For handling multiple K-1s at once 
# ==============================================================================

class BatchExtractionResult(BaseModel):
    """
    Result of processing multiple K-1 files.
    
    PSEUDOCODE:
    1. Track overall statistics
    2. Store individual results
    3. Generate summary report
    """
    total_files: int = 0
    successful: int = 0
    failed: int = 0
    total_time: float = 0.0
    results: List[ExtractionResult] = Field(default_factory=list)
    
    def get_success_rate(self) -> float:
        """Calculate success percentage"""
        if self.total_files == 0:
            return 0.0
        return (self.successful / self.total_files) * 100
    
    def to_summary(self) -> Dict:
        """Generate summary statistics"""
        return {
            "total_files": self.total_files,
            "successful": self.successful,
            "failed": self.failed,
            "success_rate": f"{self.get_success_rate():.1f}%",
            "avg_time": f"{self.total_time / max(self.total_files, 1):.2f}s"
        }