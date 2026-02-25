/**
 * TypeScript types matching backend Pydantic models.
 */

export interface Address {
  line1: string;
  line2?: string | null;
  city: string;
  postal_code: string;
  country_code: string;
}

export interface Party {
  name: string;
  address: Address;
  vat_id?: string | null;
  tax_number?: string | null;
  siren?: string | null;
  email?: string | null;
  phone?: string | null;
  contact_name?: string | null;
}

export interface LineItem {
  line_id: string;
  name: string;
  description?: string | null;
  quantity: number;
  unit_code: string;
  unit_price: number;
  vat_rate: number;
  vat_category: string;
}

export interface PaymentInfo {
  means_code: string;
  iban?: string | null;
  bic?: string | null;
  bank_name?: string | null;
  due_date?: string | null;
  payment_terms?: string | null;
}

export interface InvoiceRequest {
  invoice_number: string;
  issue_date: string;
  type_code: string;
  currency_code: string;
  buyer_reference?: string | null;
  notes?: string | null;
  seller: Party;
  buyer: Party;
  line_items: LineItem[];
  payment?: PaymentInfo | null;
}

export interface ParseResult {
  invoice: InvoiceRequest | null;
  partial_data: Record<string, unknown> | null;
  confidence: number;
  warnings: string[];
  errors: string[];
  parsing_method: string;
}

export interface ValidationResult {
  valid: boolean;
  errors: string[];
  warnings: string[];
}
