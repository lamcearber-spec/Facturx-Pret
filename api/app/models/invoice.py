"""
Pydantic models for Factur-X invoice data.

Maps to EN 16931 mandatory fields for the French e-invoicing mandate.
BT-xxx references correspond to EN 16931 Business Term identifiers.
"""

from datetime import date
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, Field, field_validator, model_validator


class VATCategory(StrEnum):
    """VAT category codes per EN 16931."""

    STANDARD = "S"       # Standard rate
    ZERO_RATE = "Z"      # Zero rated
    EXEMPT = "E"         # Exempt from tax
    REVERSE_CHARGE = "AE"  # Reverse charge
    NOT_SUBJECT = "O"    # Not subject to VAT


class UnitCode(StrEnum):
    """Common UN/ECE Recommendation 20 unit codes."""

    PIECE = "C62"
    HOUR = "HUR"
    DAY = "DAY"
    KILOGRAM = "KGM"
    METRE = "MTR"
    LITRE = "LTR"
    SQUARE_METRE = "MTK"
    CUBIC_METRE = "MTQ"
    PACKAGE = "PK"
    SET = "SET"


class Address(BaseModel):
    """Postal address (BG-5 seller / BG-8 buyer)."""

    line1: str = Field(..., description="Address line 1 (BT-35/BT-50)")
    line2: str | None = Field(None, description="Address line 2 (BT-36/BT-51)")
    city: str = Field(..., description="City (BT-37/BT-52)")
    postal_code: str = Field(..., description="Post code (BT-38/BT-53)")
    country_code: str = Field("FR", description="Country code ISO 3166-1 (BT-40/BT-55)")


class Party(BaseModel):
    """Seller or buyer party information."""

    name: str = Field(..., description="Party name (BT-27/BT-44)")
    address: Address
    vat_id: str | None = Field(None, description="VAT identifier (BT-31/BT-48)")
    tax_number: str | None = Field(None, description="Tax registration number")
    siren: str | None = Field(None, description="SIREN identifier (9 digits, France)")
    email: str | None = Field(None, description="Electronic address (BT-34/BT-49)")
    phone: str | None = Field(None, description="Contact phone")
    contact_name: str | None = Field(None, description="Contact person name")

    @field_validator("siren")
    @classmethod
    def validate_siren(cls, v: str | None) -> str | None:
        """Validate SIREN is exactly 9 digits if provided."""
        if v is not None and v != "":
            cleaned = v.replace(" ", "")
            if not cleaned.isdigit() or len(cleaned) != 9:
                raise ValueError("SIREN must be exactly 9 digits")
            return cleaned
        return v


class LineItem(BaseModel):
    """Invoice line item (BG-25)."""

    line_id: str = Field(..., description="Line identifier (BT-126)")
    name: str = Field(..., description="Item name (BT-153)")
    description: str | None = Field(None, description="Item description (BT-154)")
    quantity: Decimal = Field(..., description="Invoiced quantity (BT-129)")
    unit_code: str = Field("C62", description="Unit of measure code (BT-130)")
    unit_price: Decimal = Field(..., description="Item net price (BT-146)")
    vat_rate: Decimal = Field(
        default=Decimal("20.00"),
        description="VAT rate percent (BT-152)",
    )
    vat_category: str = Field("S", description="VAT category code (BT-151)")

    @property
    def line_total(self) -> Decimal:
        """Calculate line net amount (BT-131)."""
        return (self.quantity * self.unit_price).quantize(Decimal("0.01"))


class PaymentInfo(BaseModel):
    """Payment information (BG-16)."""

    means_code: str = Field("30", description="Payment means code (BT-81). 30=Credit transfer")
    iban: str | None = Field(None, description="Payment account IBAN (BT-84)")
    bic: str | None = Field(None, description="Payment service provider BIC (BT-86)")
    bank_name: str | None = Field(None, description="Payment account name")
    due_date: date | None = Field(None, description="Payment due date (BT-9)")
    payment_terms: str | None = Field(None, description="Payment terms text (BT-20)")


class InvoiceRequest(BaseModel):
    """
    Complete invoice request matching EN 16931 mandatory fields.

    This is the main input model for Factur-X PDF generation.
    """

    # Document level
    invoice_number: str = Field(..., description="Invoice number (BT-1)")
    issue_date: date = Field(..., description="Invoice issue date (BT-2)")
    type_code: str = Field("380", description="Invoice type code (BT-3). 380=Commercial invoice")
    currency_code: str = Field("EUR", description="Invoice currency code (BT-5)")
    buyer_reference: str | None = Field(None, description="Buyer reference (BT-10)")
    notes: str | None = Field(None, description="Invoice note (BT-22)")

    # Parties
    seller: Party = Field(..., description="Seller information (BG-4)")
    buyer: Party = Field(..., description="Buyer information (BG-7)")

    # Line items
    line_items: list[LineItem] = Field(..., min_length=1, description="Invoice line items (BG-25)")

    # Payment
    payment: PaymentInfo | None = Field(None, description="Payment information (BG-16)")

    @model_validator(mode="after")
    def validate_seller_tax_id(self) -> "InvoiceRequest":
        """Seller must have either VAT ID or tax number."""
        if not self.seller.vat_id and not self.seller.tax_number:
            raise ValueError("Seller must have either vat_id or tax_number")
        return self

    @property
    def line_total(self) -> Decimal:
        """Sum of all line net amounts (BT-106)."""
        return sum(item.line_total for item in self.line_items)

    @property
    def tax_basis_total(self) -> Decimal:
        """Invoice total without VAT (BT-109)."""
        return self.line_total

    @property
    def tax_total(self) -> Decimal:
        """
        Total VAT amount (BT-110).

        Uses total-level rounding: VAT is computed per tax rate group,
        NOT per line item. This is mandatory for French e-invoicing.
        """
        total = Decimal("0.00")
        for rate, basis in self.tax_breakdown.items():
            total += (basis * rate / Decimal("100")).quantize(Decimal("0.01"))
        return total

    @property
    def grand_total(self) -> Decimal:
        """Invoice total with VAT (BT-112)."""
        return self.tax_basis_total + self.tax_total

    @property
    def tax_breakdown(self) -> dict[Decimal, Decimal]:
        """Tax breakdown by rate: {rate: taxable_amount}."""
        breakdown: dict[Decimal, Decimal] = {}
        for item in self.line_items:
            rate = item.vat_rate
            breakdown[rate] = breakdown.get(rate, Decimal("0.00")) + item.line_total
        return breakdown


class InvoiceResponse(BaseModel):
    """Response after successful invoice generation."""

    success: bool = True
    invoice_number: str
    filename: str
    content_type: str = "application/pdf"
    xml_valid: bool = True
    message: str = "Factur-X PDF generated successfully"


class ValidationResult(BaseModel):
    """Result of invoice data validation."""

    valid: bool
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
