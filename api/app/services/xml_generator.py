"""
CII XML generator using drafthorse.

Generates UN/CEFACT Cross Industry Invoice XML (D22B schema)
with EN 16931 conformance profile for Factur-X 1.0.8.
"""

import logging
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from drafthorse.models.accounting import ApplicableTradeTax
from drafthorse.models.document import Document
from drafthorse.models.note import IncludedNote
from drafthorse.models.party import TaxRegistration
from drafthorse.models.payment import PaymentMeans, PaymentTerms
from drafthorse.models.tradelines import LineItem as DHLineItem

from app.models.invoice import InvoiceRequest

logger = logging.getLogger(__name__)


def generate_cii_xml(invoice: InvoiceRequest) -> bytes:
    """
    Generate CII XML from an InvoiceRequest.

    Args:
        invoice: Validated invoice data

    Returns:
        XML bytes in UN/CEFACT CII format (EN 16931 profile)
    """
    doc = Document()

    # EN 16931 guideline parameter (COMFORT profile = EN 16931)
    doc.context.guideline_parameter.id = "urn:cen.eu:en16931:2017"

    # Document header
    doc.header.id = invoice.invoice_number
    doc.header.type_code = invoice.type_code
    doc.header.issue_date_time = invoice.issue_date

    # Notes
    if invoice.notes:
        doc.header.notes.add(IncludedNote(content=invoice.notes))

    # --- Seller (BG-4) ---
    seller = doc.trade.agreement.seller
    seller.name = invoice.seller.name
    seller.address.line_one = invoice.seller.address.line1
    if invoice.seller.address.line2:
        seller.address.line_two = invoice.seller.address.line2
    seller.address.city_name = invoice.seller.address.city
    seller.address.postcode = invoice.seller.address.postal_code
    seller.address.country_id = invoice.seller.address.country_code

    if invoice.seller.vat_id:
        seller.tax_registrations.add(
            TaxRegistration(id=("VA", invoice.seller.vat_id))
        )
    if invoice.seller.tax_number:
        seller.tax_registrations.add(
            TaxRegistration(id=("FC", invoice.seller.tax_number))
        )

    if invoice.seller.email:
        seller.electronic_address.uri_ID._text = invoice.seller.email
        seller.electronic_address.uri_ID._scheme_id = "EM"

    # --- Buyer (BG-7) ---
    buyer = doc.trade.agreement.buyer
    buyer.name = invoice.buyer.name
    buyer.address.line_one = invoice.buyer.address.line1
    if invoice.buyer.address.line2:
        buyer.address.line_two = invoice.buyer.address.line2
    buyer.address.city_name = invoice.buyer.address.city
    buyer.address.postcode = invoice.buyer.address.postal_code
    buyer.address.country_id = invoice.buyer.address.country_code

    if invoice.buyer.vat_id:
        buyer.tax_registrations.add(
            TaxRegistration(id=("VA", invoice.buyer.vat_id))
        )

    if invoice.buyer.email:
        buyer.electronic_address.uri_ID._text = invoice.buyer.email
        buyer.electronic_address.uri_ID._scheme_id = "EM"

    # Buyer reference (BT-10)
    if invoice.buyer_reference:
        doc.trade.agreement.buyer_reference = invoice.buyer_reference

    # --- Line Items (BG-25) ---
    for item in invoice.line_items:
        li = DHLineItem()
        li.document.line_id = item.line_id
        li.product.name = item.name
        if item.description:
            li.product.description = item.description

        li.agreement.net.amount = item.unit_price
        li.agreement.net.basis_quantity = (Decimal("1.0000"), item.unit_code)
        li.delivery.billed_quantity = (item.quantity, item.unit_code)

        li.settlement.trade_tax.type_code = "VAT"
        li.settlement.trade_tax.category_code = item.vat_category
        li.settlement.trade_tax.rate_applicable_percent = item.vat_rate

        li.settlement.monetary_summation.total_amount = item.line_total

        doc.trade.items.add(li)

    # --- Settlement ---
    doc.trade.settlement.currency_code = invoice.currency_code

    # Payment means (BG-16)
    if invoice.payment:
        pm = PaymentMeans(type_code=invoice.payment.means_code)
        doc.trade.settlement.payment_means.add(pm)

        # Payment terms
        terms = PaymentTerms()
        if invoice.payment.payment_terms:
            terms.description = invoice.payment.payment_terms
        if invoice.payment.due_date:
            terms.due = datetime.combine(
                invoice.payment.due_date,
                datetime.min.time(),
                tzinfo=timezone.utc,
            )
        else:
            # Default: 30 days
            terms.due = datetime.now(timezone.utc) + timedelta(days=30)
        doc.trade.settlement.terms.add(terms)

    # --- Tax summary (BG-23) ---
    # Total-level VAT rounding: compute tax per rate group, not per line
    for rate, basis_amount in invoice.tax_breakdown.items():
        tax = ApplicableTradeTax()
        tax_amount = (basis_amount * rate / Decimal("100")).quantize(Decimal("0.01"))
        tax.calculated_amount = tax_amount
        tax.basis_amount = basis_amount
        tax.type_code = "VAT"
        tax.category_code = "S"
        tax.rate_applicable_percent = rate
        doc.trade.settlement.trade_tax.add(tax)

    # --- Monetary totals (BG-22) ---
    totals = doc.trade.settlement.monetary_summation
    totals.line_total = invoice.line_total
    totals.charge_total = Decimal("0.00")
    totals.allowance_total = Decimal("0.00")
    totals.tax_basis_total = invoice.tax_basis_total
    totals.tax_total = (invoice.tax_total, invoice.currency_code)
    totals.grand_total = invoice.grand_total
    totals.due_amount = invoice.grand_total

    # Serialize to XML (Factur-X EN 16931 / COMFORT profile)
    xml_bytes = doc.serialize(schema="FACTUR-X_EN16931")
    logger.info(
        "Generated CII XML for invoice %s (%.1f KB)",
        invoice.invoice_number,
        len(xml_bytes) / 1024,
    )
    return xml_bytes
