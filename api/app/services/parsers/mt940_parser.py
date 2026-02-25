"""MT940 bank statement parser with AI fallback."""

import logging
import re

from app.services.parsers.base import BaseParser, ParseResult
from app.services.parsers.ai_fallback import ai_parser, AIParserError

logger = logging.getLogger(__name__)


class MT940Parser(BaseParser):
    """
    Parse invoice data from MT940 bank statement files.

    MT940 is a bank statement format, not an invoice format. We extract
    transaction references and amounts that may relate to invoices, then
    use AI to structure the data.
    """

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
                errors=["MT940-Datei konnte nicht dekodiert werden."],
                parsing_method="failed",
            )

        # Stage 1: Extract MT940 fields
        data = self._extract_mt940_fields(text)

        # Stage 2: AI to interpret as invoice data
        return await self._ai_parse(text, filename, data)

    def _extract_mt940_fields(self, text: str) -> dict:
        """Extract basic MT940 fields."""
        data: dict = {}

        # Account IBAN (:25:)
        m = re.search(r":25:([^\n]+)", text)
        if m:
            data["account"] = m.group(1).strip()

        # Statement lines (:61:)
        transactions = re.findall(r":61:([^\n]+)", text)
        if transactions:
            data["transaction_count"] = len(transactions)

        # Transaction details (:86:)
        details = re.findall(r":86:([^\n:]+(?:\n(?!:)[^\n:]+)*)", text)
        if details:
            data["transaction_details"] = [d.strip() for d in details[:10]]

        return data

    async def _ai_parse(self, text: str, filename: str, extracted: dict) -> ParseResult:
        """AI to extract invoice-relevant data from MT940."""
        if not ai_parser.is_available:
            return ParseResult(
                partial_data=extracted,
                confidence=0.2,
                parsing_method="direct",
                warnings=[
                    "MT940 ist ein Kontoauszugsformat. "
                    "KI-Parser nicht verfügbar für erweiterte Extraktion."
                ],
            )

        try:
            data = await ai_parser.extract_invoice_data(
                f"MT940-Kontoauszug ({filename}):\n{text[:10000]}\n\n"
                f"Bitte versuche, Rechnungsdaten aus den Transaktionsdetails zu extrahieren."
            )
            return self._build_partial_result(
                data, method="ai", confidence=0.5,
                warnings=[
                    "MT940 ist ein Kontoauszugsformat. "
                    "Rechnungsdaten wurden geschätzt — bitte sorgfältig überprüfen."
                ],
            )
        except AIParserError as e:
            return ParseResult(
                partial_data=extracted,
                confidence=0.1,
                errors=[f"KI-Extraktion fehlgeschlagen: {str(e)}"],
                parsing_method="ai",
            )
