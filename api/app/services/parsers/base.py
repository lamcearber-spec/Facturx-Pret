"""Base parser interface for all file type parsers."""

from abc import ABC, abstractmethod

from pydantic import BaseModel, Field

from app.models.invoice import InvoiceRequest


class ParseResult(BaseModel):
    """Result of parsing a file into invoice data."""

    invoice: InvoiceRequest | None = Field(
        None,
        description="Fully parsed invoice, if all required fields were found",
    )
    partial_data: dict | None = Field(
        None,
        description="Incomplete data for user review/completion",
    )
    confidence: float = Field(
        0.0,
        ge=0.0,
        le=1.0,
        description="Confidence score of parsing result",
    )
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    parsing_method: str = Field(
        "unknown",
        description="Method used: 'direct', 'ai', 'hybrid'",
    )


class BaseParser(ABC):
    """Abstract base class for file parsers."""

    @abstractmethod
    async def parse(self, file_content: bytes, filename: str) -> ParseResult:
        """
        Parse file content into invoice data.

        Args:
            file_content: Raw file bytes
            filename: Original filename (for extension detection)

        Returns:
            ParseResult with invoice data or partial data for review
        """
        ...

    def _build_partial_result(
        self,
        data: dict,
        method: str,
        confidence: float,
        warnings: list[str] | None = None,
        errors: list[str] | None = None,
    ) -> ParseResult:
        """Try to build a full InvoiceRequest; fall back to partial_data."""
        try:
            invoice = InvoiceRequest(**data)
            return ParseResult(
                invoice=invoice,
                confidence=confidence,
                parsing_method=method,
                warnings=warnings or [],
                errors=errors or [],
            )
        except Exception:
            return ParseResult(
                partial_data=data,
                confidence=confidence,
                parsing_method=method,
                warnings=warnings or [],
                errors=errors or [],
            )
