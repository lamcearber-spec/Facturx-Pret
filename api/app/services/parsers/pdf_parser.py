"""PDF invoice parser: pdfplumber direct extraction with AI fallback."""

import logging
import re
from datetime import date

from app.services.parsers.base import BaseParser, ParseResult
from app.services.parsers.ai_fallback import ai_parser, AIParserError

logger = logging.getLogger(__name__)

# Regex patterns for common German invoice fields
PATTERNS = {
    "invoice_number": re.compile(
        r"(?:Rechnungs?(?:nummer|nr\.?|[-\s]Nr\.?)|Invoice\s*(?:No\.?|Number))"
        r"\s*[:\s]\s*([A-Za-z0-9\-/]+)",
        re.IGNORECASE,
    ),
    "date": re.compile(
        r"(?:Rechnungsdatum|Datum|Date|Belegdatum)"
        r"\s*[:\s]\s*(\d{1,2}[./]\d{1,2}[./]\d{2,4})",
        re.IGNORECASE,
    ),
    "vat_id": re.compile(
        r"(?:USt[.-]?Id(?:Nr)?\.?|VAT\s*ID)\s*[:\s]\s*(DE\s*\d{9})",
        re.IGNORECASE,
    ),
    "tax_number": re.compile(
        r"(?:Steuernummer|Tax\s*No\.?)\s*[:\s]\s*([\d/\s]+)",
        re.IGNORECASE,
    ),
    "iban": re.compile(
        r"(?:IBAN)\s*[:\s]\s*([A-Z]{2}\d{2}[\s]?[\dA-Z]{4}[\s]?[\dA-Z\s]{10,30})",
        re.IGNORECASE,
    ),
    "bic": re.compile(
        r"(?:BIC|SWIFT)\s*[:\s]\s*([A-Z]{6}[A-Z0-9]{2,5})",
        re.IGNORECASE,
    ),
    "total": re.compile(
        r"(?:Gesamtbetrag|Rechnungsbetrag|Total|Summe\s*brutto)"
        r"\s*[:\s]*\s*([\d.,]+)\s*(?:EUR|€)?",
        re.IGNORECASE,
    ),
    "net_total": re.compile(
        r"(?:Nettobetrag|Summe\s*netto|Net\s*total)"
        r"\s*[:\s]*\s*([\d.,]+)\s*(?:EUR|€)?",
        re.IGNORECASE,
    ),
    "vat_amount": re.compile(
        r"(?:MwSt\.?|USt\.?|VAT)\s*(?:\d+\s*%?)?\s*[:\s]*\s*([\d.,]+)\s*(?:EUR|€)?",
        re.IGNORECASE,
    ),
}


def _parse_german_date(date_str: str) -> date | None:
    """Parse DD.MM.YYYY or DD/MM/YYYY to date."""
    for fmt in ("%d.%m.%Y", "%d/%m/%Y", "%d.%m.%y", "%d/%m/%y"):
        try:
            from datetime import datetime
            return datetime.strptime(date_str.strip(), fmt).date()
        except ValueError:
            continue
    return None


def _parse_german_amount(amount_str: str) -> float | None:
    """Parse 1.234,56 or 1,234.56 to float."""
    s = amount_str.strip()
    if not s:
        return None
    # German format: 1.234,56
    if "," in s and "." in s:
        if s.rindex(",") > s.rindex("."):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    elif "," in s:
        s = s.replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


class PDFParser(BaseParser):
    """Parse invoice data from PDF files."""

    async def parse(self, file_content: bytes, filename: str) -> ParseResult:
        # Stage 1: Direct extraction with pdfplumber
        text = self._extract_text(file_content)
        if not text or len(text.strip()) < 50:
            # Likely scanned PDF — go straight to AI
            return await self._ai_parse(text or "", filename)

        # Stage 2: Try regex extraction
        data = self._extract_fields(text)
        if data.get("invoice_number") and data.get("seller", {}).get("name"):
            return self._build_partial_result(
                data, method="direct", confidence=0.7,
                warnings=["Einige Felder wurden möglicherweise nicht korrekt erkannt."],
            )

        # Stage 3: AI fallback
        return await self._ai_parse(text, filename)

    def _extract_text(self, file_content: bytes) -> str | None:
        """Extract text from PDF using pdfplumber."""
        try:
            import io
            import pdfplumber
            with pdfplumber.open(io.BytesIO(file_content)) as pdf:
                pages = [page.extract_text() or "" for page in pdf.pages]
                return "\n\n".join(pages)
        except Exception as e:
            logger.warning("pdfplumber extraction failed: %s", e)
            return None

    def _extract_fields(self, text: str) -> dict:
        """Extract invoice fields using regex patterns."""
        data: dict = {}

        # Invoice number
        m = PATTERNS["invoice_number"].search(text)
        if m:
            data["invoice_number"] = m.group(1).strip()

        # Date
        m = PATTERNS["date"].search(text)
        if m:
            d = _parse_german_date(m.group(1))
            if d:
                data["issue_date"] = d.isoformat()

        # VAT ID
        m = PATTERNS["vat_id"].search(text)
        if m:
            vat_id = m.group(1).replace(" ", "")
            # Try to associate with seller (first occurrence)
            data.setdefault("seller", {})["vat_id"] = vat_id

        # IBAN
        m = PATTERNS["iban"].search(text)
        if m:
            data.setdefault("payment", {})["iban"] = m.group(1).replace(" ", "")

        # BIC
        m = PATTERNS["bic"].search(text)
        if m:
            data.setdefault("payment", {})["bic"] = m.group(1)

        return data

    async def _ai_parse(self, text: str, filename: str) -> ParseResult:
        """Use AI fallback for extraction."""
        if not ai_parser.is_available:
            return ParseResult(
                errors=["AI-Parser nicht konfiguriert und direkte Extraktion fehlgeschlagen."],
                parsing_method="failed",
            )

        try:
            data = await ai_parser.extract_invoice_data(text)
            return self._build_partial_result(
                data, method="ai", confidence=0.8,
                warnings=["Daten wurden per KI extrahiert — bitte überprüfen."],
            )
        except AIParserError as e:
            return ParseResult(
                errors=[f"KI-Extraktion fehlgeschlagen: {str(e)}"],
                parsing_method="ai",
            )
