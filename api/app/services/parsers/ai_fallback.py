"""
Azure OpenAI-based invoice data extraction.

Mirrors the DatevBereit AI parsing pattern (apps/api/celery_app/pdf/openai_parser.py).
Uses Azure OpenAI to extract structured invoice data from raw text or descriptions.
"""

import json
import logging
from typing import Any

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from app.core.config import settings

logger = logging.getLogger(__name__)


class AIParserError(Exception):
    """Error during AI-based parsing."""
    pass


# Prompt for extracting invoice data from arbitrary text
INVOICE_EXTRACTION_PROMPT = """Du bist ein Experte für Rechnungsverarbeitung und E-Invoicing (ZUGFeRD/Factur-X, EN 16931).
Extrahiere alle Rechnungsdaten aus dem folgenden Text und gib sie als JSON zurück.

Text:
{text}

Antworte ausschließlich mit einem validen JSON-Objekt in diesem Format:
{{
  "invoice_number": "Rechnungsnummer",
  "issue_date": "YYYY-MM-DD",
  "type_code": "380",
  "currency_code": "EUR",
  "buyer_reference": "Leitweg-ID oder Bestellnummer oder null",
  "notes": "Bemerkungen oder null",
  "seller": {{
    "name": "Firmenname des Verkäufers",
    "address": {{
      "line1": "Straße und Hausnummer",
      "line2": "Zusatz oder null",
      "city": "Stadt",
      "postal_code": "PLZ",
      "country_code": "DE"
    }},
    "vat_id": "USt-IdNr. z.B. DE123456789 oder null",
    "tax_number": "Steuernummer oder null",
    "email": "E-Mail oder null",
    "phone": "Telefon oder null"
  }},
  "buyer": {{
    "name": "Firmenname des Käufers",
    "address": {{
      "line1": "Straße und Hausnummer",
      "line2": "Zusatz oder null",
      "city": "Stadt",
      "postal_code": "PLZ",
      "country_code": "DE"
    }},
    "vat_id": "USt-IdNr. oder null",
    "email": "E-Mail oder null"
  }},
  "line_items": [
    {{
      "line_id": "1",
      "name": "Bezeichnung der Position",
      "description": "Beschreibung oder null",
      "quantity": 1.0,
      "unit_code": "C62",
      "unit_price": 100.00,
      "vat_rate": 19.00,
      "vat_category": "S"
    }}
  ],
  "payment": {{
    "means_code": "58",
    "iban": "IBAN oder null",
    "bic": "BIC oder null",
    "bank_name": "Bankname oder null",
    "due_date": "YYYY-MM-DD oder null",
    "payment_terms": "Zahlungsbedingungen oder null"
  }}
}}

Wichtige Regeln:
1. Datumsformat DD.MM.YYYY oder MM/DD/YYYY zu YYYY-MM-DD konvertieren
2. Zahlenformat 1.234,56 (deutsch) zu 1234.56 konvertieren
3. USt-IdNr. mit DE-Präfix wenn erkennbar
4. unit_code: C62=Stück, HUR=Stunde, DAY=Tag, KGM=Kilogramm, MTR=Meter
5. vat_category: S=Standard, Z=Null, E=Befreit, AE=Reverse Charge
6. type_code: 380=Rechnung, 381=Gutschrift, 384=Korrekturrechnung
7. means_code: 58=SEPA-Überweisung, 30=Überweisung, 59=SEPA-Lastschrift
8. Antworte NUR mit dem JSON, kein zusätzlicher Text
9. Beträge und Mengen als Dezimalzahlen (nicht als Strings)
10. Fehlende Pflichtfelder mit sinnvollen Platzhaltern füllen"""


class AIFallbackParser:
    """
    Azure OpenAI-based fallback parser for invoice data extraction.

    Used when direct/structured parsing fails or yields incomplete data.
    """

    MAX_TEXT_LENGTH = 15000

    def __init__(
        self,
        api_key: str | None = None,
        endpoint: str | None = None,
        deployment: str | None = None,
        api_version: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.1,
    ):
        self.api_key = api_key or (
            settings.AZURE_OPENAI_API_KEY.get_secret_value()
            if settings.AZURE_OPENAI_API_KEY else None
        )
        self.endpoint = endpoint or settings.AZURE_OPENAI_ENDPOINT
        self.deployment = deployment or settings.AZURE_OPENAI_DEPLOYMENT
        self.api_version = api_version or settings.AZURE_OPENAI_API_VERSION
        self.max_tokens = max_tokens
        self.temperature = temperature
        self._client = None

    @property
    def client(self):
        """Lazy initialization of Azure OpenAI client."""
        if self._client is None:
            if not self.api_key:
                raise AIParserError("Azure OpenAI API key not configured")
            if not self.endpoint:
                raise AIParserError("Azure OpenAI endpoint not configured")

            try:
                from openai import AzureOpenAI
                self._client = AzureOpenAI(
                    api_key=self.api_key,
                    api_version=self.api_version,
                    azure_endpoint=self.endpoint,
                )
            except ImportError:
                raise AIParserError("openai package not installed")

        return self._client

    @property
    def is_available(self) -> bool:
        """Check if Azure OpenAI is configured."""
        return bool(self.api_key and self.endpoint)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception_type((Exception,)),
        reraise=True,
    )
    async def extract_invoice_data(self, text: str) -> dict[str, Any]:
        """
        Extract structured invoice data from raw text using Azure OpenAI.

        Args:
            text: Raw text extracted from a file

        Returns:
            Dictionary matching InvoiceRequest schema

        Raises:
            AIParserError: If extraction fails
        """
        if not self.is_available:
            raise AIParserError("Azure OpenAI not configured")

        # Truncate text if too long
        if len(text) > self.MAX_TEXT_LENGTH:
            text = text[:self.MAX_TEXT_LENGTH]
            logger.warning("Text truncated to %d characters", self.MAX_TEXT_LENGTH)

        prompt = INVOICE_EXTRACTION_PROMPT.format(text=text)

        try:
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {
                        "role": "system",
                        "content": "Du bist ein Experte für deutsche Rechnungen und E-Invoicing. "
                                   "Antworte immer nur mit validem JSON.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature,
            )

            content = response.choices[0].message.content
            if not content:
                raise AIParserError("Empty response from Azure OpenAI")

            # Strip markdown code fences if present
            content = content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()

            data = json.loads(content)
            logger.info("AI extraction successful for invoice: %s", data.get("invoice_number"))
            return data

        except json.JSONDecodeError as e:
            logger.error("Failed to parse AI response as JSON: %s", str(e))
            raise AIParserError(f"Invalid JSON from AI: {str(e)}")
        except Exception as e:
            logger.error("AI extraction failed: %s", str(e))
            raise AIParserError(f"AI extraction failed: {str(e)}")


# Module-level singleton
ai_parser = AIFallbackParser()
