"""CSV invoice parser: pandas column mapping with AI fallback."""

import csv
import io
import logging

import pandas as pd

from app.services.parsers.base import BaseParser, ParseResult
from app.services.parsers.ai_fallback import ai_parser, AIParserError

logger = logging.getLogger(__name__)

# Expected column names (German and English variants)
COLUMN_MAP = {
    # Invoice number
    "rechnungsnummer": "invoice_number",
    "rechnungsnr": "invoice_number",
    "invoice_number": "invoice_number",
    "invoice_no": "invoice_number",
    "belegnummer": "invoice_number",
    # Date
    "rechnungsdatum": "issue_date",
    "datum": "issue_date",
    "date": "issue_date",
    "invoice_date": "issue_date",
    # Seller
    "verkäufer": "seller_name",
    "lieferant": "seller_name",
    "seller": "seller_name",
    "seller_name": "seller_name",
    "firma": "seller_name",
    # Seller address
    "verkäufer_straße": "seller_street",
    "seller_street": "seller_street",
    "verkäufer_plz": "seller_postal_code",
    "seller_postal_code": "seller_postal_code",
    "verkäufer_ort": "seller_city",
    "seller_city": "seller_city",
    "verkäufer_land": "seller_country",
    "seller_country": "seller_country",
    # Seller tax
    "ust_id": "seller_vat_id",
    "vat_id": "seller_vat_id",
    "ust_idnr": "seller_vat_id",
    "steuernummer": "seller_tax_number",
    "tax_number": "seller_tax_number",
    # Buyer
    "käufer": "buyer_name",
    "kunde": "buyer_name",
    "buyer": "buyer_name",
    "buyer_name": "buyer_name",
    "empfänger": "buyer_name",
    # Buyer address
    "käufer_straße": "buyer_street",
    "buyer_street": "buyer_street",
    "käufer_plz": "buyer_postal_code",
    "buyer_postal_code": "buyer_postal_code",
    "käufer_ort": "buyer_city",
    "buyer_city": "buyer_city",
    "käufer_land": "buyer_country",
    "buyer_country": "buyer_country",
    # Line items
    "bezeichnung": "item_name",
    "beschreibung": "item_name",
    "item_name": "item_name",
    "position": "item_name",
    "artikel": "item_name",
    "menge": "quantity",
    "quantity": "quantity",
    "anzahl": "quantity",
    "einheit": "unit_code",
    "unit": "unit_code",
    "einzelpreis": "unit_price",
    "preis": "unit_price",
    "price": "unit_price",
    "unit_price": "unit_price",
    "ust_satz": "vat_rate",
    "mwst": "vat_rate",
    "vat_rate": "vat_rate",
    "steuersatz": "vat_rate",
    # Payment
    "iban": "iban",
    "bic": "bic",
    "fällig": "due_date",
    "due_date": "due_date",
    "zahlungsziel": "due_date",
}


class CSVParser(BaseParser):
    """Parse invoice data from CSV files."""

    async def parse(self, file_content: bytes, filename: str) -> ParseResult:
        # Stage 1: Try pandas parsing with column mapping
        try:
            df = self._read_csv(file_content)
            if df is not None and not df.empty:
                mapped = self._map_columns(df)
                if mapped:
                    invoices = self._build_invoices(df, mapped)
                    if invoices:
                        return self._build_partial_result(
                            invoices[0], method="direct", confidence=0.85,
                            warnings=[f"{len(invoices)} Rechnung(en) erkannt."]
                            if len(invoices) > 1 else [],
                        )
        except Exception as e:
            logger.warning("CSV direct parsing failed: %s", e)

        # Stage 2: AI fallback
        return await self._ai_parse(file_content, filename)

    def _read_csv(self, file_content: bytes) -> pd.DataFrame | None:
        """Read CSV with encoding/delimiter detection."""
        text = None
        for encoding in ["utf-8-sig", "utf-8", "latin-1", "cp1252"]:
            try:
                text = file_content.decode(encoding)
                break
            except UnicodeDecodeError:
                continue

        if text is None:
            return None

        # Detect delimiter
        try:
            dialect = csv.Sniffer().sniff(text[:4096], delimiters=",;\t|")
            sep = dialect.delimiter
        except csv.Error:
            sep = ";"  # German default

        return pd.read_csv(io.StringIO(text), sep=sep, dtype=str)

    def _map_columns(self, df: pd.DataFrame) -> dict[str, str]:
        """Map DataFrame columns to known invoice fields."""
        mapped = {}
        for col in df.columns:
            normalized = col.strip().lower().replace(" ", "_").replace("-", "_")
            if normalized in COLUMN_MAP:
                mapped[col] = COLUMN_MAP[normalized]
        return mapped

    def _build_invoices(self, df: pd.DataFrame, column_map: dict[str, str]) -> list[dict]:
        """Build invoice data dicts from mapped DataFrame."""
        # Reverse map: field_name -> column_name
        field_to_col = {v: k for k, v in column_map.items()}

        invoices = []
        for _, row in df.iterrows():
            data: dict = {
                "type_code": "380",
                "currency_code": "EUR",
            }

            # Simple fields
            for field, col in field_to_col.items():
                val = str(row.get(col, "")).strip()
                if not val or val == "nan":
                    continue

                if field == "invoice_number":
                    data["invoice_number"] = val
                elif field == "issue_date":
                    data["issue_date"] = val
                elif field == "seller_name":
                    data.setdefault("seller", {"address": {"line1": "", "city": "", "postal_code": "", "country_code": "DE"}})
                    data["seller"]["name"] = val
                elif field == "seller_street":
                    data.setdefault("seller", {}).setdefault("address", {})["line1"] = val
                elif field == "seller_city":
                    data.setdefault("seller", {}).setdefault("address", {})["city"] = val
                elif field == "seller_postal_code":
                    data.setdefault("seller", {}).setdefault("address", {})["postal_code"] = val
                elif field == "seller_country":
                    data.setdefault("seller", {}).setdefault("address", {})["country_code"] = val
                elif field == "seller_vat_id":
                    data.setdefault("seller", {})["vat_id"] = val
                elif field == "seller_tax_number":
                    data.setdefault("seller", {})["tax_number"] = val
                elif field == "buyer_name":
                    data.setdefault("buyer", {"address": {"line1": "", "city": "", "postal_code": "", "country_code": "DE"}})
                    data["buyer"]["name"] = val
                elif field == "buyer_street":
                    data.setdefault("buyer", {}).setdefault("address", {})["line1"] = val
                elif field == "buyer_city":
                    data.setdefault("buyer", {}).setdefault("address", {})["city"] = val
                elif field == "buyer_postal_code":
                    data.setdefault("buyer", {}).setdefault("address", {})["postal_code"] = val
                elif field == "buyer_country":
                    data.setdefault("buyer", {}).setdefault("address", {})["country_code"] = val
                elif field == "item_name":
                    item = data.setdefault("_current_item", {})
                    item["name"] = val
                elif field == "quantity":
                    item = data.setdefault("_current_item", {})
                    item["quantity"] = val
                elif field == "unit_price":
                    item = data.setdefault("_current_item", {})
                    item["unit_price"] = val.replace(",", ".")
                elif field == "vat_rate":
                    item = data.setdefault("_current_item", {})
                    item["vat_rate"] = val.replace(",", ".").replace("%", "")
                elif field == "iban":
                    data.setdefault("payment", {})["iban"] = val
                elif field == "due_date":
                    data.setdefault("payment", {})["due_date"] = val

            # Finalize line item
            current_item = data.pop("_current_item", None)
            if current_item and current_item.get("name"):
                current_item.setdefault("line_id", "1")
                current_item.setdefault("quantity", "1")
                current_item.setdefault("unit_code", "C62")
                current_item.setdefault("vat_rate", "19.00")
                current_item.setdefault("vat_category", "S")
                data["line_items"] = [current_item]

            if data.get("invoice_number") or data.get("seller"):
                invoices.append(data)

        return invoices

    async def _ai_parse(self, file_content: bytes, filename: str) -> ParseResult:
        """AI fallback for CSV parsing."""
        if not ai_parser.is_available:
            return ParseResult(
                errors=["KI-Parser nicht konfiguriert und Spalten konnten nicht zugeordnet werden."],
                parsing_method="failed",
            )

        # Send first ~100 rows as text to AI
        text = None
        for enc in ["utf-8-sig", "utf-8", "latin-1", "cp1252"]:
            try:
                text = file_content.decode(enc)
                break
            except UnicodeDecodeError:
                continue

        if not text:
            return ParseResult(errors=["Datei konnte nicht dekodiert werden."], parsing_method="failed")

        lines = text.splitlines()[:100]
        sample = "\n".join(lines)

        try:
            data = await ai_parser.extract_invoice_data(
                f"CSV-Datei ({filename}):\n{sample}"
            )
            return self._build_partial_result(
                data, method="ai", confidence=0.75,
                warnings=["Daten wurden per KI aus CSV extrahiert — bitte überprüfen."],
            )
        except AIParserError as e:
            return ParseResult(
                errors=[f"KI-Extraktion fehlgeschlagen: {str(e)}"],
                parsing_method="ai",
            )
