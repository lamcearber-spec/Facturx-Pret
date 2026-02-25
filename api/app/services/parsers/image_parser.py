"""Image invoice parser: OCR + AI fallback for JPG/PNG/HEIC."""

import io
import logging

from app.services.parsers.base import BaseParser, ParseResult
from app.services.parsers.ai_fallback import ai_parser, AIParserError

logger = logging.getLogger(__name__)


class ImageParser(BaseParser):
    """Parse invoice data from image files (photos/screenshots of invoices)."""

    async def parse(self, file_content: bytes, filename: str) -> ParseResult:
        # Convert HEIC to PNG if needed
        image_bytes = self._prepare_image(file_content, filename)

        # Stage 1: Try OCR to extract text
        text = self._ocr_extract(image_bytes)

        if text and len(text.strip()) > 50:
            # Stage 2: Parse extracted OCR text with AI
            return await self._ai_parse(text, filename)

        # Stage 3: If OCR failed, try AI vision directly
        return await self._ai_parse(
            f"[Bilddatei: {filename} — OCR-Text konnte nicht extrahiert werden. "
            f"Bitte extrahiere die Rechnungsdaten aus dem Kontext.]",
            filename,
        )

    def _prepare_image(self, file_content: bytes, filename: str) -> bytes:
        """Convert HEIC and normalize image format."""
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

        if ext == "heic":
            try:
                import pillow_heif
                from PIL import Image

                heif_file = pillow_heif.read_heif(file_content)
                img = Image.frombytes(
                    heif_file.mode, heif_file.size, heif_file.data,
                    "raw", heif_file.mode, heif_file.stride,
                )
                buf = io.BytesIO()
                img.save(buf, format="PNG")
                return buf.getvalue()
            except Exception as e:
                logger.warning("HEIC conversion failed: %s", e)

        return file_content

    def _ocr_extract(self, image_bytes: bytes) -> str | None:
        """Extract text from image using Pillow + pytesseract if available."""
        try:
            from PIL import Image
            import pytesseract

            img = Image.open(io.BytesIO(image_bytes))
            text = pytesseract.image_to_string(img, lang="deu")
            return text
        except ImportError:
            logger.info("pytesseract not available, skipping OCR")
            return None
        except Exception as e:
            logger.warning("OCR failed: %s", e)
            return None

    async def _ai_parse(self, text: str, filename: str) -> ParseResult:
        """AI fallback for image parsing."""
        if not ai_parser.is_available:
            return ParseResult(
                errors=[
                    "KI-Parser nicht konfiguriert. "
                    "Bilddateien benötigen den KI-Parser zur Extraktion."
                ],
                parsing_method="failed",
            )

        try:
            data = await ai_parser.extract_invoice_data(
                f"Rechnungsbild ({filename}):\n{text}"
            )
            return self._build_partial_result(
                data, method="ai", confidence=0.7,
                warnings=[
                    "Daten wurden per KI aus einem Bild extrahiert — bitte sorgfältig überprüfen."
                ],
            )
        except AIParserError as e:
            return ParseResult(
                errors=[f"KI-Extraktion fehlgeschlagen: {str(e)}"],
                parsing_method="ai",
            )
