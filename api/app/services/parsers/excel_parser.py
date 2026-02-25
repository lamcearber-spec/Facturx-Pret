"""Excel (XLSX/XLS) invoice parser: pandas with AI fallback."""

import io
import logging

import pandas as pd

from app.services.parsers.base import BaseParser, ParseResult
from app.services.parsers.csv_parser import CSVParser
from app.services.parsers.ai_fallback import ai_parser, AIParserError

logger = logging.getLogger(__name__)


class ExcelParser(BaseParser):
    """Parse invoice data from Excel files. Reuses CSV column mapping logic."""

    async def parse(self, file_content: bytes, filename: str) -> ParseResult:
        # Stage 1: Read Excel into DataFrame, then use CSV parser logic
        try:
            ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "xlsx"
            engine = "openpyxl" if ext == "xlsx" else "xlrd"

            df = pd.read_excel(
                io.BytesIO(file_content),
                engine=engine,
                dtype=str,
            )

            if df is not None and not df.empty:
                # Reuse CSV column mapping
                csv_p = CSVParser()
                mapped = csv_p._map_columns(df)
                if mapped:
                    invoices = csv_p._build_invoices(df, mapped)
                    if invoices:
                        return self._build_partial_result(
                            invoices[0], method="direct", confidence=0.85,
                            warnings=[f"{len(invoices)} Rechnung(en) erkannt."]
                            if len(invoices) > 1 else [],
                        )

                # Convert to text for AI
                text_repr = df.to_string()
        except Exception as e:
            logger.warning("Excel direct parsing failed: %s", e)
            text_repr = ""

        # Stage 2: AI fallback
        return await self._ai_parse(text_repr or "", filename)

    async def _ai_parse(self, text: str, filename: str) -> ParseResult:
        """AI fallback for Excel parsing."""
        if not ai_parser.is_available:
            return ParseResult(
                errors=["KI-Parser nicht konfiguriert und Excel konnte nicht verarbeitet werden."],
                parsing_method="failed",
            )

        try:
            data = await ai_parser.extract_invoice_data(
                f"Excel-Datei ({filename}):\n{text[:10000]}"
            )
            return self._build_partial_result(
                data, method="ai", confidence=0.75,
                warnings=["Daten wurden per KI aus Excel extrahiert — bitte überprüfen."],
            )
        except AIParserError as e:
            return ParseResult(
                errors=[f"KI-Extraktion fehlgeschlagen: {str(e)}"],
                parsing_method="ai",
            )
