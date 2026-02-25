"""XML invoice parser: camt.053 / generic XML with AI fallback."""

import logging
import re
from datetime import date

from app.services.parsers.base import BaseParser, ParseResult
from app.services.parsers.ai_fallback import ai_parser, AIParserError

logger = logging.getLogger(__name__)


class XMLParser(BaseParser):
    """Parse invoice data from XML files (camt.053 and other formats)."""

    async def parse(self, file_content: bytes, filename: str) -> ParseResult:
        # Decode
        text = None
        for enc in ["utf-8", "latin-1", "cp1252"]:
            try:
                text = file_content.decode(enc)
                break
            except UnicodeDecodeError:
                continue

        if not text:
            return ParseResult(
                errors=["XML-Datei konnte nicht dekodiert werden."],
                parsing_method="failed",
            )

        # Stage 1: Try to detect if it's already a CII/UBL invoice XML
        if "CrossIndustryInvoice" in text or "urn:un:unece:uncefact" in text:
            return await self._parse_cii(text)

        # Stage 2: Try camt.053 parsing
        if "camt.053" in text:
            return await self._parse_camt053(text, filename)

        # Stage 3: AI fallback for unknown XML
        return await self._ai_parse(text, filename)

    async def _parse_cii(self, text: str) -> ParseResult:
        """Parse an existing CII XML (ZUGFeRD/Factur-X)."""
        try:
            from lxml import etree
            root = etree.fromstring(text.encode("utf-8"))

            ns = {
                "rsm": "urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100",
                "ram": "urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100",
                "udt": "urn:un:unece:uncefact:data:standard:UnqualifiedDataType:100",
            }

            data: dict = {"type_code": "380", "currency_code": "EUR"}

            # Invoice number
            el = root.find(".//rsm:ExchangedDocument/ram:ID", ns)
            if el is not None and el.text:
                data["invoice_number"] = el.text

            # Type code
            el = root.find(".//rsm:ExchangedDocument/ram:TypeCode", ns)
            if el is not None and el.text:
                data["type_code"] = el.text

            # Issue date
            el = root.find(".//rsm:ExchangedDocument/ram:IssueDateTime/udt:DateTimeString", ns)
            if el is not None and el.text:
                data["issue_date"] = f"{el.text[:4]}-{el.text[4:6]}-{el.text[6:8]}"

            return self._build_partial_result(
                data, method="direct", confidence=0.9,
                warnings=["CII-XML erkannt — Basisdaten extrahiert."],
            )
        except Exception as e:
            logger.warning("CII XML parsing failed: %s", e)
            return await self._ai_parse(text, "cii.xml")

    async def _parse_camt053(self, text: str, filename: str) -> ParseResult:
        """Parse camt.053 bank statement XML — limited invoice data."""
        # camt.053 is a bank statement format, not an invoice format.
        # We can extract payment references and amounts but not full invoice data.
        return ParseResult(
            partial_data={
                "notes": "Aus camt.053 Kontoauszug importiert",
                "_source_format": "camt.053",
            },
            confidence=0.3,
            parsing_method="direct",
            warnings=[
                "camt.053 ist ein Kontoauszugsformat, kein Rechnungsformat. "
                "Nur begrenzte Daten konnten extrahiert werden."
            ],
        )

    async def _ai_parse(self, text: str, filename: str) -> ParseResult:
        """AI fallback for XML parsing."""
        if not ai_parser.is_available:
            return ParseResult(
                errors=["KI-Parser nicht konfiguriert."],
                parsing_method="failed",
            )

        try:
            data = await ai_parser.extract_invoice_data(
                f"XML-Datei ({filename}):\n{text[:10000]}"
            )
            return self._build_partial_result(
                data, method="ai", confidence=0.75,
                warnings=["Daten wurden per KI aus XML extrahiert — bitte überprüfen."],
            )
        except AIParserError as e:
            return ParseResult(
                errors=[f"KI-Extraktion fehlgeschlagen: {str(e)}"],
                parsing_method="ai",
            )
