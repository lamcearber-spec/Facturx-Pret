"""
Invoice generation and file parsing endpoints.

POST /generate     - JSON -> Factur-X PDF
POST /upload       - File upload -> parsed invoice data
POST /convert      - File upload -> Factur-X PDF directly
POST /batch        - CSV/Excel -> ZIP of Factur-X PDFs
POST /validate     - Validate invoice JSON
POST /preview-xml  - Get CII XML preview
"""

import io
import logging
import zipfile
from typing import Annotated

from fastapi import APIRouter, File, HTTPException, Response, UploadFile
from pydantic import ValidationError

from app.core.config import settings
from app.models.invoice import InvoiceRequest, InvoiceResponse, ValidationResult
from app.services.pdf_generator import generate_facturx_pdf
from app.services.xml_generator import generate_cii_xml
from app.services.parsers.base import ParseResult
from app.services.parsers.pdf_parser import PDFParser
from app.services.parsers.csv_parser import CSVParser
from app.services.parsers.excel_parser import ExcelParser
from app.services.parsers.image_parser import ImageParser
from app.services.parsers.xml_parser import XMLParser
from app.services.parsers.mt940_parser import MT940Parser

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/invoice", tags=["invoice"])

# File extension -> parser mapping
EXTENSION_PARSERS = {
    ".pdf": PDFParser,
    ".csv": CSVParser,
    ".xlsx": ExcelParser,
    ".xls": ExcelParser,
    ".jpg": ImageParser,
    ".jpeg": ImageParser,
    ".png": ImageParser,
    ".heic": ImageParser,
    ".xml": XMLParser,
    ".sta": MT940Parser,
    ".mt940": MT940Parser,
    ".940": MT940Parser,
    ".mt9": MT940Parser,
}

ALLOWED_EXTENSIONS = set(EXTENSION_PARSERS.keys())


def _get_extension(filename: str) -> str:
    """Get lowercase file extension with dot."""
    if "." in filename:
        return "." + filename.rsplit(".", 1)[1].lower()
    return ""


@router.post("/generate", response_class=Response)
async def generate_invoice(invoice: InvoiceRequest):
    """
    Generate a Factur-X PDF/A-3 from structured invoice data.

    Returns the PDF file directly. Filename uses SIREN_YYYYMMDD.pdf
    pattern if seller SIREN is provided.
    """
    try:
        pdf_bytes, filename = generate_facturx_pdf(invoice)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
            },
        )
    except Exception as e:
        logger.error("PDF generation failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Echec de la generation du PDF : {str(e)}")


@router.post("/upload")
async def upload_and_parse(file: Annotated[UploadFile, File(description="Invoice file")]) -> ParseResult:
    """
    Upload a file (PDF, CSV, Excel, MT940, XML, image) and parse invoice data.

    Returns structured invoice data or partial data for user review.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Nom de fichier manquant.")

    ext = _get_extension(file.filename)
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Type de fichier '{ext}' non supporte. "
                   f"Formats acceptes : {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )

    content = await file.read()
    if len(content) > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"Fichier trop volumineux. Maximum : {settings.MAX_FILE_SIZE // (1024*1024)} Mo",
        )

    parser_class = EXTENSION_PARSERS[ext]
    parser = parser_class()
    result = await parser.parse(content, file.filename)
    return result


@router.post("/convert", response_class=Response)
async def convert_to_facturx(file: Annotated[UploadFile, File(description="Invoice file to convert")]):
    """
    Upload a file, parse it, and generate a Factur-X PDF directly.

    Combines upload + parse + generate in one step.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Nom de fichier manquant.")

    ext = _get_extension(file.filename)
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Type de fichier '{ext}' non supporte.")

    content = await file.read()
    if len(content) > settings.MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="Fichier trop volumineux.")

    # Parse
    parser_class = EXTENSION_PARSERS[ext]
    parser = parser_class()
    result = await parser.parse(content, file.filename)

    if not result.invoice:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "Les donnees de facturation n'ont pas pu etre entierement extraites.",
                "partial_data": result.partial_data,
                "errors": result.errors,
                "warnings": result.warnings,
            },
        )

    # Generate
    try:
        pdf_bytes, filename = generate_facturx_pdf(result.invoice)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except Exception as e:
        logger.error("Conversion failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Echec de la conversion : {str(e)}")


@router.post("/batch", response_class=Response)
async def batch_generate(file: Annotated[UploadFile, File(description="CSV/Excel with multiple invoices")]):
    """
    Upload a CSV/Excel with multiple invoices, generate Factur-X PDFs as ZIP.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Nom de fichier manquant.")

    ext = _get_extension(file.filename)
    if ext not in {".csv", ".xlsx", ".xls"}:
        raise HTTPException(
            status_code=400,
            detail="Le traitement par lots est uniquement disponible pour les fichiers CSV et Excel.",
        )

    content = await file.read()

    # Parse - for batch, we expect multiple rows = multiple invoices
    # For now, use the single-invoice parser and handle one invoice
    parser_class = EXTENSION_PARSERS[ext]
    parser = parser_class()
    result = await parser.parse(content, file.filename)

    if not result.invoice:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "Les donnees de facturation n'ont pas pu etre extraites.",
                "errors": result.errors,
                "warnings": result.warnings,
            },
        )

    # Generate PDF and package as ZIP
    try:
        pdf_bytes, filename = generate_facturx_pdf(result.invoice)

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr(filename, pdf_bytes)
        zip_buffer.seek(0)

        return Response(
            content=zip_buffer.getvalue(),
            media_type="application/zip",
            headers={"Content-Disposition": 'attachment; filename="FacturX_Factures.zip"'},
        )
    except Exception as e:
        logger.error("Batch generation failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Echec du traitement par lots : {str(e)}")


@router.post("/validate")
async def validate_invoice(invoice: InvoiceRequest) -> ValidationResult:
    """Validate invoice data without generating a PDF."""
    warnings = []

    # Check seller email (BT-34 recommended)
    if not invoice.seller.email:
        warnings.append("E-mail du vendeur (BT-34) manquant - recommande pour EN 16931.")

    # Check buyer email (BT-49 recommended)
    if not invoice.buyer.email:
        warnings.append("E-mail de l'acheteur (BT-49) manquant - recommande pour EN 16931.")

    # Check payment info
    if not invoice.payment:
        warnings.append("Informations de paiement manquantes - recommandees.")

    # Check buyer reference
    if not invoice.buyer_reference:
        warnings.append("Reference acheteur (BT-10) manquante.")

    # Check SIREN for French sellers
    if invoice.seller.address.country_code == "FR" and not invoice.seller.siren:
        warnings.append("SIREN du vendeur manquant - obligatoire pour les entreprises francaises.")

    return ValidationResult(valid=True, warnings=warnings)


@router.post("/preview-xml", response_class=Response)
async def preview_xml(invoice: InvoiceRequest):
    """Generate and return only the CII XML (no PDF)."""
    try:
        xml_bytes = generate_cii_xml(invoice)
        return Response(
            content=xml_bytes,
            media_type="application/xml",
            headers={
                "Content-Disposition": f'attachment; filename="factur-x.xml"',
            },
        )
    except Exception as e:
        logger.error("XML generation failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Echec de la generation XML : {str(e)}")
