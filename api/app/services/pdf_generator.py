"""
PDF/A-3 generator for Factur-X invoices.

1. Renders an invoice into a visual PDF using fpdf2 (no system dependencies)
2. Embeds the CII XML as factur-x.xml using the factur-x library
3. Injects XMP Extension Schema metadata (fx namespace, EN 16931 conformance)
"""

import io
import logging
from decimal import Decimal
from pathlib import Path

from fpdf import FPDF

from app.models.invoice import InvoiceRequest
from app.services.xml_generator import generate_cii_xml

logger = logging.getLogger(__name__)


class InvoicePDF(FPDF):
    """Custom FPDF subclass for Factur-X invoice rendering."""

    def __init__(self, invoice: InvoiceRequest):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.invoice = invoice
        self.set_auto_page_break(auto=True, margin=25)
        self._setup_fonts()

    def _setup_fonts(self):
        """Use built-in Helvetica (no font files needed)."""
        pass

    def header(self):
        """Page header rendered once at top of first page."""
        pass

    def footer(self):
        """Page footer with Factur-X badge."""
        self.set_y(-20)
        self.set_draw_color(226, 232, 240)
        self.line(20, self.get_y(), 190, self.get_y())
        self.ln(3)
        self.set_font("Helvetica", "B", 7)
        self.set_fill_color(45, 55, 72)
        self.set_text_color(255, 255, 255)
        badge_text = "Factur-X 1.0.8 / EN 16931"
        badge_w = self.get_string_width(badge_text) + 6
        self.cell(badge_w, 5, badge_text, fill=True, align="C")
        self.set_text_color(136, 136, 136)
        self.set_font("Helvetica", "", 7)
        self.ln(5)
        self.cell(0, 4, "Cette facture contient un fichier XML lisible par machine (factur-x.xml) au format CII.", align="C")


def _format_amount_fr(amount, currency="EUR"):
    """Format amount with French number convention (space thousands, comma decimal)."""
    formatted = f"{amount:,.2f}"
    formatted = formatted.replace(",", " ").replace(".", ",")
    return f"{formatted} {currency}"


def _build_invoice_pdf(invoice: InvoiceRequest) -> bytes:
    """Build a visual invoice PDF using fpdf2."""
    pdf = InvoicePDF(invoice)
    pdf.add_page()

    seller = invoice.seller
    buyer = invoice.buyer
    currency = invoice.currency_code

    y_start = 15
    pdf.set_xy(110, y_start)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(26, 26, 26)
    pdf.cell(80, 5, seller.name, align="R")
    pdf.ln(5)

    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(85, 85, 85)
    pdf.set_x(110)
    pdf.cell(80, 4, seller.address.line1, align="R")
    pdf.ln(4)
    if seller.address.line2:
        pdf.set_x(110)
        pdf.cell(80, 4, seller.address.line2, align="R")
        pdf.ln(4)
    pdf.set_x(110)
    pdf.cell(80, 4, f"{seller.address.postal_code} {seller.address.city}", align="R")
    pdf.ln(4)
    pdf.set_x(110)
    pdf.cell(80, 4, seller.address.country_code, align="R")
    pdf.ln(4)

    seller_tax = seller.vat_id or seller.tax_number or ""
    if seller_tax:
        pdf.set_x(110)
        pdf.cell(80, 4, f"TVA: {seller_tax}", align="R")
        pdf.ln(4)
    if seller.siren:
        pdf.set_x(110)
        pdf.cell(80, 4, f"SIREN: {seller.siren}", align="R")
        pdf.ln(4)
    if seller.email:
        pdf.set_x(110)
        pdf.cell(80, 4, seller.email, align="R")
        pdf.ln(4)
    if seller.phone:
        pdf.set_x(110)
        pdf.cell(80, 4, seller.phone, align="R")
        pdf.ln(4)

    # Buyer block (left side)
    pdf.set_xy(20, y_start)
    pdf.set_font("Helvetica", "", 7)
    pdf.set_text_color(136, 136, 136)
    pdf.cell(80, 3, "DESTINATAIRE", align="L")
    pdf.ln(4)

    pdf.set_x(20)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(26, 26, 26)
    pdf.cell(80, 5, buyer.name, align="L")
    pdf.ln(5)

    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(26, 26, 26)
    pdf.set_x(20)
    pdf.cell(80, 4, buyer.address.line1, align="L")
    pdf.ln(4)
    if buyer.address.line2:
        pdf.set_x(20)
        pdf.cell(80, 4, buyer.address.line2, align="L")
        pdf.ln(4)
    pdf.set_x(20)
    pdf.cell(80, 4, f"{buyer.address.postal_code} {buyer.address.city}", align="L")
    pdf.ln(4)
    pdf.set_x(20)
    pdf.cell(80, 4, buyer.address.country_code, align="L")
    pdf.ln(4)

    buyer_tax = buyer.vat_id or ""
    if buyer_tax:
        pdf.set_x(20)
        pdf.cell(80, 4, f"TVA: {buyer_tax}", align="L")
        pdf.ln(4)

    # Invoice title
    pdf.ln(10)
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(45, 55, 72)
    pdf.cell(0, 10, f"Facture {invoice.invoice_number}", ln=True)
    pdf.ln(3)

    # Meta table
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(26, 26, 26)

    meta_rows = [
        ("N\u00b0 de facture :", invoice.invoice_number),
        ("Date de facture :", invoice.issue_date.strftime("%d/%m/%Y")),
    ]
    if invoice.buyer_reference:
        meta_rows.append(("Votre reference :", invoice.buyer_reference))
    meta_rows.append(("Devise :", currency))

    for label, value in meta_rows:
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(85, 85, 85)
        pdf.cell(40, 5, label, align="L")
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(26, 26, 26)
        pdf.cell(0, 5, str(value), ln=True)

    pdf.ln(5)

    # Line items table
    col_widths = [12, 52, 20, 18, 28, 18, 28]
    headers = ["Pos.", "Designation", "Qte", "Unite", "Prix unit.", "TVA", "Montant HT"]

    pdf.set_font("Helvetica", "B", 8)
    pdf.set_fill_color(247, 248, 250)
    pdf.set_draw_color(45, 55, 72)
    pdf.set_text_color(26, 26, 26)

    x_start = 17
    pdf.set_x(x_start)
    for i, (header, w) in enumerate(zip(headers, col_widths)):
        align = "R" if i >= 2 else "L"
        pdf.cell(w, 7, header, border="B", fill=True, align=align)
    pdf.ln()

    pdf.set_font("Helvetica", "", 8)
    pdf.set_draw_color(226, 232, 240)

    for item in invoice.line_items:
        pdf.set_x(x_start)
        pdf.cell(col_widths[0], 6, str(item.line_id), border="B", align="L")
        name_display = item.name[:30] + "..." if len(item.name) > 33 else item.name
        pdf.cell(col_widths[1], 6, name_display, border="B", align="L")
        pdf.cell(col_widths[2], 6, f"{item.quantity:g}", border="B", align="R")
        pdf.cell(col_widths[3], 6, item.unit_code, border="B", align="R")
        pdf.cell(col_widths[4], 6, f"{item.unit_price:,.2f}", border="B", align="R")
        pdf.cell(col_widths[5], 6, f"{item.vat_rate}%", border="B", align="R")
        pdf.cell(col_widths[6], 6, f"{item.line_total:,.2f}", border="B", align="R")
        pdf.ln()

    pdf.ln(5)

    # Totals (right aligned)
    totals_x = 110
    totals_label_w = 40
    totals_value_w = 40

    def _total_row(label: str, value: str, bold: bool = False, border_top: bool = False):
        pdf.set_x(totals_x)
        if border_top:
            pdf.set_draw_color(45, 55, 72)
            pdf.line(totals_x, pdf.get_y(), totals_x + totals_label_w + totals_value_w, pdf.get_y())
            pdf.ln(1)
            pdf.set_x(totals_x)
        style = "B" if bold else ""
        size = 11 if bold else 9
        pdf.set_font("Helvetica", style, size)
        pdf.cell(totals_label_w, 6, label, align="L")
        pdf.cell(totals_value_w, 6, value, align="R")
        pdf.ln()

    _total_row("Total HT :", f"{invoice.line_total:,.2f} {currency}")
    _total_row("Total TVA :", f"{invoice.tax_total:,.2f} {currency}")
    _total_row("Total TTC :", f"{invoice.grand_total:,.2f} {currency}", bold=True, border_top=True)

    pdf.ln(5)

    # Tax summary table
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_fill_color(247, 248, 250)
    pdf.set_draw_color(226, 232, 240)

    tax_cols = [30, 50, 50]
    tax_headers = ["Taux TVA", "Base HT", "Montant TVA"]

    pdf.set_x(x_start)
    for header, w in zip(tax_headers, tax_cols):
        align = "R" if header != "Taux TVA" else "L"
        pdf.cell(w, 6, header, fill=True, border="B", align=align)
    pdf.ln()

    pdf.set_font("Helvetica", "", 8)
    for rate, basis in invoice.tax_breakdown.items():
        tax_amount = (basis * rate / Decimal("100")).quantize(Decimal("0.01"))
        pdf.set_x(x_start)
        pdf.cell(tax_cols[0], 5, f"{rate}%", border="B", align="L")
        pdf.cell(tax_cols[1], 5, f"{basis:,.2f} {currency}", border="B", align="R")
        pdf.cell(tax_cols[2], 5, f"{tax_amount:,.2f} {currency}", border="B", align="R")
        pdf.ln()

    pdf.ln(5)

    # Payment info
    if invoice.payment:
        pdf.set_fill_color(247, 248, 250)
        pdf.set_font("Helvetica", "B", 9)

        y_before = pdf.get_y()
        parts = []
        if invoice.payment.iban:
            parts.append(f"IBAN : {invoice.payment.iban}")
        if invoice.payment.bic:
            parts.append(f"BIC : {invoice.payment.bic}")
        if invoice.payment.bank_name:
            parts.append(f"Banque : {invoice.payment.bank_name}")
        if invoice.payment.due_date:
            due_str = invoice.payment.due_date.strftime("%d/%m/%Y")
            parts.append(f"Echeance : {due_str}")
        if invoice.payment.payment_terms:
            parts.append(invoice.payment.payment_terms)

        block_h = 8 + len(parts) * 5
        pdf.set_x(x_start)
        pdf.cell(160, block_h, "", fill=True)

        pdf.set_xy(x_start + 3, y_before + 2)
        pdf.cell(0, 5, "Informations de paiement")
        pdf.ln(5)

        pdf.set_font("Helvetica", "", 9)
        for part in parts:
            pdf.set_x(x_start + 3)
            pdf.cell(0, 4, part)
            pdf.ln(4)

        pdf.ln(3)

    # Notes
    if invoice.notes:
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(85, 85, 85)
        pdf.set_x(x_start)
        pdf.multi_cell(160, 4, invoice.notes)

    # Output
    return pdf.output()


def _build_filename(invoice: InvoiceRequest) -> str:
    """
    Build PDF filename using SIREN_YYYYMMDD pattern if SIREN available.

    Falls back to FacturX_{invoice_number}.pdf if no SIREN.
    """
    if invoice.seller.siren:
        date_str = invoice.issue_date.strftime("%Y%m%d")
        return f"{invoice.seller.siren}_{date_str}.pdf"
    return f"FacturX_{invoice.invoice_number}.pdf"


def generate_facturx_pdf(invoice: InvoiceRequest) -> tuple[bytes, str]:
    """
    Generate a Factur-X compliant PDF/A-3 with embedded CII XML.

    Steps:
        1. Generate CII XML via drafthorse
        2. Render invoice PDF via fpdf2
        3. Embed XML into PDF via factur-x (PDF/A-3 + XMP metadata)

    Args:
        invoice: Validated invoice data

    Returns:
        Tuple of (PDF/A-3 bytes with embedded factur-x.xml, filename)
    """
    # Step 1: Generate CII XML
    xml_bytes = generate_cii_xml(invoice)

    # Step 2: Render visual PDF (fpdf2 returns bytearray, facturx needs bytes)
    pdf_bytes = bytes(_build_invoice_pdf(invoice))

    # Step 3: Embed XML into PDF/A-3
    from facturx import generate_from_binary
    facturx_pdf = generate_from_binary(
        pdf_bytes,
        xml_bytes,
        # factur-x auto-detects the flavor from the guideline parameter
    )

    filename = _build_filename(invoice)

    logger.info(
        "Generated Factur-X PDF for invoice %s (%s, %.1f KB PDF, %.1f KB XML)",
        invoice.invoice_number,
        filename,
        len(facturx_pdf) / 1024,
        len(xml_bytes) / 1024,
    )
    return facturx_pdf, filename
