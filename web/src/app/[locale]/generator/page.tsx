"use client";

import { useState, useCallback } from "react";
import { useTranslations } from "next-intl";
import { Link } from "@/i18n/navigation";
import {
  FileText, Upload, Layers, ArrowLeft, ArrowRight, Plus, Trash2,
  Download, Loader2, CheckCircle, AlertCircle, Eye,
} from "lucide-react";
import { siteConfig } from "@/config";
import { LanguageSwitcher } from "@/components/ui/LanguageSwitcher";
import { generateInvoice, uploadAndParse, batchGenerate } from "@/lib/api";
import type { InvoiceRequest, LineItem, ParseResult } from "@/types/invoice";

type Tab = "form" | "upload" | "batch";
type FormStep = 1 | 2 | 3 | 4 | 5;

const DEFAULT_LINE_ITEM: LineItem = {
  line_id: "1",
  name: "",
  quantity: 1,
  unit_code: "C62",
  unit_price: 0,
  vat_rate: 19,
  vat_category: "S",
};

const DEFAULT_INVOICE: InvoiceRequest = {
  invoice_number: "",
  issue_date: new Date().toISOString().split("T")[0],
  type_code: "380",
  currency_code: "EUR",
  seller: {
    name: "",
    address: { line1: "", city: "", postal_code: "", country_code: "DE" },
    vat_id: "",
    email: "",
  },
  buyer: {
    name: "",
    address: { line1: "", city: "", postal_code: "", country_code: "DE" },
    email: "",
  },
  line_items: [{ ...DEFAULT_LINE_ITEM }],
  payment: {
    means_code: "58",
    iban: "",
    bic: "",
  },
};

export default function GeneratorPage() {
  const t = useTranslations("generator");
  const [activeTab, setActiveTab] = useState<Tab>("form");
  const [formStep, setFormStep] = useState<FormStep>(1);
  const [invoice, setInvoice] = useState<InvoiceRequest>({ ...DEFAULT_INVOICE });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Upload state
  const [parseResult, setParseResult] = useState<ParseResult | null>(null);
  const [dragOver, setDragOver] = useState(false);

  const updateInvoice = useCallback((path: string, value: unknown) => {
    setInvoice((prev) => {
      const next = JSON.parse(JSON.stringify(prev));
      const keys = path.split(".");
      let obj = next;
      for (let i = 0; i < keys.length - 1; i++) {
        obj = obj[keys[i]];
      }
      obj[keys[keys.length - 1]] = value;
      return next;
    });
  }, []);

  const addLineItem = () => {
    setInvoice((prev) => ({
      ...prev,
      line_items: [
        ...prev.line_items,
        { ...DEFAULT_LINE_ITEM, line_id: String(prev.line_items.length + 1) },
      ],
    }));
  };

  const removeLineItem = (index: number) => {
    if (invoice.line_items.length <= 1) return;
    setInvoice((prev) => ({
      ...prev,
      line_items: prev.line_items.filter((_, i) => i !== index),
    }));
  };

  const handleGenerate = async () => {
    setLoading(true);
    setError(null);
    setSuccess(null);
    try {
      const blob = await generateInvoice(invoice);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `ZUGFeRD_${invoice.invoice_number || "Invoice"}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
      setSuccess(t("messages.pdf_success"));
    } catch (e: any) {
      setError(e?.response?.data?.detail || e.message || t("messages.pdf_error"));
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (file: File) => {
    setLoading(true);
    setError(null);
    setParseResult(null);
    try {
      const result = await uploadAndParse(file);
      setParseResult(result);
      if (result.invoice) {
        setInvoice(result.invoice);
        setSuccess(t("upload.success"));
      }
    } catch (e: any) {
      setError(e?.response?.data?.detail || e.message || t("messages.parse_error"));
    } finally {
      setLoading(false);
    }
  };

  const handleBatchUpload = async (file: File) => {
    setLoading(true);
    setError(null);
    try {
      const blob = await batchGenerate(file);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "ZUGFeRD_Invoices.zip";
      a.click();
      URL.revokeObjectURL(url);
      setSuccess(t("messages.batch_success"));
    } catch (e: any) {
      setError(e?.response?.data?.detail || e.message || t("messages.batch_error"));
    } finally {
      setLoading(false);
    }
  };

  const handleDrop = useCallback(
    (e: React.DragEvent, handler: (f: File) => void) => {
      e.preventDefault();
      setDragOver(false);
      const file = e.dataTransfer.files[0];
      if (file) handler(file);
    },
    []
  );

  // Calculate totals
  const lineTotal = invoice.line_items.reduce(
    (sum, item) => sum + item.quantity * item.unit_price,
    0
  );
  const taxTotal = invoice.line_items.reduce(
    (sum, item) => sum + (item.quantity * item.unit_price * item.vat_rate) / 100,
    0
  );
  const grandTotal = lineTotal + taxTotal;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-14">
            <Link href="/" className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center text-white font-bold text-xs">
                {siteConfig.logoText}
              </div>
              <span className="font-semibold text-gray-900">{siteConfig.name}</span>
            </Link>
            <div className="flex items-center gap-4">
              <span className="text-sm text-gray-500">{t("page_title")}</span>
              <LanguageSwitcher variant="compact" />
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Alerts */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
            <AlertCircle size={18} className="text-red-500 mt-0.5 flex-shrink-0" />
            <div className="text-sm text-red-700">{error}</div>
            <button onClick={() => setError(null)} className="ml-auto text-red-400 hover:text-red-600">&times;</button>
          </div>
        )}
        {success && (
          <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg flex items-start gap-3">
            <CheckCircle size={18} className="text-green-500 mt-0.5 flex-shrink-0" />
            <div className="text-sm text-green-700">{success}</div>
            <button onClick={() => setSuccess(null)} className="ml-auto text-green-400 hover:text-green-600">&times;</button>
          </div>
        )}

        {/* Tabs */}
        <div className="flex gap-1 mb-8 bg-white rounded-lg border border-gray-200 p-1">
          {[
            { id: "form" as Tab, icon: FileText, label: t("tabs.form") },
            { id: "upload" as Tab, icon: Upload, label: t("tabs.upload") },
            { id: "batch" as Tab, icon: Layers, label: t("tabs.batch") },
          ].map(({ id, icon: Icon, label }) => (
            <button
              key={id}
              onClick={() => setActiveTab(id)}
              className={`flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-md text-sm font-medium transition-colors ${
                activeTab === id
                  ? "bg-blue-600 text-white"
                  : "text-gray-600 hover:bg-gray-100"
              }`}
            >
              <Icon size={16} />
              {label}
            </button>
          ))}
        </div>

        {/* === FORM TAB === */}
        {activeTab === "form" && (
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            {/* Step indicator */}
            <div className="flex items-center gap-2 mb-8">
              {[
                { step: 1, label: t("steps.seller") },
                { step: 2, label: t("steps.buyer") },
                { step: 3, label: t("steps.items") },
                { step: 4, label: t("steps.payment") },
                { step: 5, label: t("steps.review") },
              ].map(({ step, label }) => (
                <div key={step} className="flex items-center gap-2 flex-1">
                  <button
                    onClick={() => setFormStep(step as FormStep)}
                    className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-medium ${
                      formStep === step
                        ? "bg-blue-600 text-white"
                        : formStep > step
                        ? "bg-green-100 text-green-700"
                        : "bg-gray-100 text-gray-500"
                    }`}
                  >
                    {formStep > step ? <CheckCircle size={14} /> : step}
                  </button>
                  <span className="text-xs text-gray-500 hidden sm:block">{label}</span>
                  {step < 5 && <div className="flex-1 h-px bg-gray-200" />}
                </div>
              ))}
            </div>

            {/* Step 1: Seller */}
            {formStep === 1 && (
              <div className="space-y-4">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">{t("seller.title")}</h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="sm:col-span-2">
                    <label className="block text-sm font-medium text-gray-700 mb-1">{t("seller.company_name")} *</label>
                    <input type="text" value={invoice.seller.name} onChange={(e) => updateInvoice("seller.name", e.target.value)} className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500" placeholder={t("seller.placeholder_company")} />
                  </div>
                  <div className="sm:col-span-2">
                    <label className="block text-sm font-medium text-gray-700 mb-1">{t("seller.street")} *</label>
                    <input type="text" value={invoice.seller.address.line1} onChange={(e) => updateInvoice("seller.address.line1", e.target.value)} className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500" placeholder={t("seller.placeholder_street")} />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">{t("seller.postal_code")} *</label>
                    <input type="text" value={invoice.seller.address.postal_code} onChange={(e) => updateInvoice("seller.address.postal_code", e.target.value)} className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500" placeholder={t("seller.placeholder_postal")} />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">{t("seller.city")} *</label>
                    <input type="text" value={invoice.seller.address.city} onChange={(e) => updateInvoice("seller.address.city", e.target.value)} className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500" placeholder={t("seller.placeholder_city")} />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">{t("seller.vat_id")}</label>
                    <input type="text" value={invoice.seller.vat_id || ""} onChange={(e) => updateInvoice("seller.vat_id", e.target.value)} className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500" placeholder={t("seller.placeholder_vat")} />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">{t("seller.email")}</label>
                    <input type="email" value={invoice.seller.email || ""} onChange={(e) => updateInvoice("seller.email", e.target.value)} className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500" placeholder={t("seller.placeholder_email")} />
                  </div>
                </div>
              </div>
            )}

            {/* Step 2: Buyer */}
            {formStep === 2 && (
              <div className="space-y-4">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">{t("buyer.title")}</h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="sm:col-span-2">
                    <label className="block text-sm font-medium text-gray-700 mb-1">{t("buyer.company_name")} *</label>
                    <input type="text" value={invoice.buyer.name} onChange={(e) => updateInvoice("buyer.name", e.target.value)} className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500" placeholder={t("buyer.placeholder_company")} />
                  </div>
                  <div className="sm:col-span-2">
                    <label className="block text-sm font-medium text-gray-700 mb-1">{t("buyer.street")} *</label>
                    <input type="text" value={invoice.buyer.address.line1} onChange={(e) => updateInvoice("buyer.address.line1", e.target.value)} className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500" placeholder={t("buyer.placeholder_street")} />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">{t("buyer.postal_code")} *</label>
                    <input type="text" value={invoice.buyer.address.postal_code} onChange={(e) => updateInvoice("buyer.address.postal_code", e.target.value)} className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500" placeholder={t("buyer.placeholder_postal")} />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">{t("buyer.city")} *</label>
                    <input type="text" value={invoice.buyer.address.city} onChange={(e) => updateInvoice("buyer.address.city", e.target.value)} className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500" placeholder={t("buyer.placeholder_city")} />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">{t("buyer.email")}</label>
                    <input type="email" value={invoice.buyer.email || ""} onChange={(e) => updateInvoice("buyer.email", e.target.value)} className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500" placeholder={t("buyer.placeholder_email")} />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">{t("buyer.reference")}</label>
                    <input type="text" value={invoice.buyer_reference || ""} onChange={(e) => updateInvoice("buyer_reference", e.target.value)} className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500" placeholder={t("buyer.placeholder_reference")} />
                  </div>
                </div>
              </div>
            )}

            {/* Step 3: Line Items */}
            {formStep === 3 && (
              <div className="space-y-4">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-gray-900">{t("items.title")}</h3>
                  <button onClick={addLineItem} className="flex items-center gap-1 text-sm text-blue-600 hover:text-blue-700 font-medium">
                    <Plus size={16} /> {t("items.add_item")}
                  </button>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">{t("items.invoice_number")} *</label>
                    <input type="text" value={invoice.invoice_number} onChange={(e) => updateInvoice("invoice_number", e.target.value)} className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500" placeholder={t("items.placeholder_number")} />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">{t("items.invoice_date")} *</label>
                    <input type="date" value={invoice.issue_date} onChange={(e) => updateInvoice("issue_date", e.target.value)} className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500" />
                  </div>
                </div>

                {invoice.line_items.map((item, index) => (
                  <div key={index} className="p-4 bg-gray-50 rounded-lg border border-gray-200">
                    <div className="flex items-center justify-between mb-3">
                      <span className="text-sm font-medium text-gray-700">{t("items.position")} {index + 1}</span>
                      {invoice.line_items.length > 1 && (
                        <button onClick={() => removeLineItem(index)} className="text-red-400 hover:text-red-600">
                          <Trash2 size={16} />
                        </button>
                      )}
                    </div>
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                      <div className="col-span-2 sm:col-span-4">
                        <input type="text" value={item.name} onChange={(e) => updateInvoice(`line_items.${index}.name`, e.target.value)} className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm" placeholder={`${t("items.description")} *`} />
                      </div>
                      <div>
                        <label className="block text-xs text-gray-500 mb-1">{t("items.quantity")}</label>
                        <input type="number" min="0" step="0.01" value={item.quantity} onChange={(e) => updateInvoice(`line_items.${index}.quantity`, Number(e.target.value))} className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm" />
                      </div>
                      <div>
                        <label className="block text-xs text-gray-500 mb-1">{t("items.unit")}</label>
                        <select value={item.unit_code} onChange={(e) => updateInvoice(`line_items.${index}.unit_code`, e.target.value)} className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm">
                          <option value="C62">{t("items.unit_piece")}</option>
                          <option value="HUR">{t("items.unit_hour")}</option>
                          <option value="DAY">{t("items.unit_day")}</option>
                          <option value="KGM">{t("items.unit_kg")}</option>
                          <option value="MTR">{t("items.unit_meter")}</option>
                          <option value="LTR">{t("items.unit_liter")}</option>
                        </select>
                      </div>
                      <div>
                        <label className="block text-xs text-gray-500 mb-1">{t("items.unit_price")}</label>
                        <input type="number" min="0" step="0.01" value={item.unit_price} onChange={(e) => updateInvoice(`line_items.${index}.unit_price`, Number(e.target.value))} className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm" />
                      </div>
                      <div>
                        <label className="block text-xs text-gray-500 mb-1">{t("items.vat_percent")}</label>
                        <select value={item.vat_rate} onChange={(e) => updateInvoice(`line_items.${index}.vat_rate`, Number(e.target.value))} className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm">
                          <option value={19}>19%</option>
                          <option value={7}>7%</option>
                          <option value={0}>0%</option>
                        </select>
                      </div>
                    </div>
                    <div className="mt-2 text-right text-sm text-gray-600">
                      {t("items.net")}: {(item.quantity * item.unit_price).toFixed(2)} €
                    </div>
                  </div>
                ))}

                {/* Totals */}
                <div className="mt-4 p-4 bg-blue-50 rounded-lg border border-blue-100">
                  <div className="space-y-1 text-sm">
                    <div className="flex justify-between"><span className="text-gray-600">{t("items.net_total")}:</span><span className="font-medium">{lineTotal.toFixed(2)} €</span></div>
                    <div className="flex justify-between"><span className="text-gray-600">{t("items.vat_total")}:</span><span className="font-medium">{taxTotal.toFixed(2)} €</span></div>
                    <div className="flex justify-between text-base font-bold border-t border-blue-200 pt-1 mt-1"><span>{t("items.grand_total")}:</span><span>{grandTotal.toFixed(2)} €</span></div>
                  </div>
                </div>
              </div>
            )}

            {/* Step 4: Payment */}
            {formStep === 4 && (
              <div className="space-y-4">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">{t("payment.title")}</h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="sm:col-span-2">
                    <label className="block text-sm font-medium text-gray-700 mb-1">{t("payment.iban")}</label>
                    <input type="text" value={invoice.payment?.iban || ""} onChange={(e) => updateInvoice("payment.iban", e.target.value)} className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500" placeholder={t("payment.placeholder_iban")} />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">{t("payment.bic")}</label>
                    <input type="text" value={invoice.payment?.bic || ""} onChange={(e) => updateInvoice("payment.bic", e.target.value)} className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500" placeholder={t("payment.placeholder_bic")} />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">{t("payment.due_date")}</label>
                    <input type="date" value={invoice.payment?.due_date || ""} onChange={(e) => updateInvoice("payment.due_date", e.target.value)} className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500" />
                  </div>
                  <div className="sm:col-span-2">
                    <label className="block text-sm font-medium text-gray-700 mb-1">{t("payment.terms")}</label>
                    <input type="text" value={invoice.payment?.payment_terms || ""} onChange={(e) => updateInvoice("payment.payment_terms", e.target.value)} className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500" placeholder={t("payment.placeholder_terms")} />
                  </div>
                  <div className="sm:col-span-2">
                    <label className="block text-sm font-medium text-gray-700 mb-1">{t("payment.notes")}</label>
                    <textarea value={invoice.notes || ""} onChange={(e) => updateInvoice("notes", e.target.value)} className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500" rows={3} placeholder={t("payment.placeholder_notes")} />
                  </div>
                </div>
              </div>
            )}

            {/* Step 5: Review */}
            {formStep === 5 && (
              <div className="space-y-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">{t("review.title")}</h3>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                  <div className="p-4 bg-gray-50 rounded-lg">
                    <h4 className="text-sm font-semibold text-gray-500 uppercase mb-2">{t("review.seller_label")}</h4>
                    <p className="font-medium">{invoice.seller.name}</p>
                    <p className="text-sm text-gray-600">{invoice.seller.address.line1}</p>
                    <p className="text-sm text-gray-600">{invoice.seller.address.postal_code} {invoice.seller.address.city}</p>
                    {invoice.seller.vat_id && <p className="text-sm text-gray-600">{t("review.vat_id_label")}: {invoice.seller.vat_id}</p>}
                  </div>
                  <div className="p-4 bg-gray-50 rounded-lg">
                    <h4 className="text-sm font-semibold text-gray-500 uppercase mb-2">{t("review.buyer_label")}</h4>
                    <p className="font-medium">{invoice.buyer.name}</p>
                    <p className="text-sm text-gray-600">{invoice.buyer.address.line1}</p>
                    <p className="text-sm text-gray-600">{invoice.buyer.address.postal_code} {invoice.buyer.address.city}</p>
                  </div>
                </div>

                <div className="p-4 bg-gray-50 rounded-lg">
                  <div className="flex justify-between items-center mb-3">
                    <h4 className="text-sm font-semibold text-gray-500 uppercase">{t("review.invoice_label")} {invoice.invoice_number}</h4>
                    <span className="text-sm text-gray-500">{invoice.issue_date}</span>
                  </div>
                  <div className="space-y-1">
                    {invoice.line_items.map((item, i) => (
                      <div key={i} className="flex justify-between text-sm">
                        <span>{item.quantity}x {item.name}</span>
                        <span>{(item.quantity * item.unit_price).toFixed(2)} €</span>
                      </div>
                    ))}
                  </div>
                  <div className="border-t border-gray-200 mt-3 pt-3 space-y-1">
                    <div className="flex justify-between text-sm"><span>{t("review.net_label")}:</span><span>{lineTotal.toFixed(2)} €</span></div>
                    <div className="flex justify-between text-sm"><span>{t("review.vat_label")}:</span><span>{taxTotal.toFixed(2)} €</span></div>
                    <div className="flex justify-between font-bold"><span>{t("review.total_label")}:</span><span>{grandTotal.toFixed(2)} €</span></div>
                  </div>
                </div>

                <button
                  onClick={handleGenerate}
                  disabled={loading}
                  className="w-full flex items-center justify-center gap-2 px-6 py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
                >
                  {loading ? <Loader2 size={18} className="animate-spin" /> : <Download size={18} />}
                  {t("review.generate_btn")}
                </button>
              </div>
            )}

            {/* Navigation buttons */}
            {formStep < 5 && (
              <div className="flex justify-between mt-8">
                <button
                  onClick={() => setFormStep(Math.max(1, formStep - 1) as FormStep)}
                  disabled={formStep === 1}
                  className="flex items-center gap-1 px-4 py-2 text-sm text-gray-600 hover:text-gray-900 disabled:opacity-30"
                >
                  <ArrowLeft size={16} /> {t("nav.back")}
                </button>
                <button
                  onClick={() => setFormStep(Math.min(5, formStep + 1) as FormStep)}
                  className="flex items-center gap-1 px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700"
                >
                  {t("nav.next")} <ArrowRight size={16} />
                </button>
              </div>
            )}
          </div>
        )}

        {/* === UPLOAD TAB === */}
        {activeTab === "upload" && (
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">{t("upload.title")}</h3>
            <p className="text-sm text-gray-600 mb-6">
              {t("upload.description")}
            </p>

            <div
              className={`border-2 border-dashed rounded-xl p-12 text-center transition-colors cursor-pointer ${
                dragOver ? "border-blue-500 bg-blue-50" : "border-gray-300 hover:border-gray-400"
              }`}
              onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
              onDragLeave={() => setDragOver(false)}
              onDrop={(e) => handleDrop(e, handleFileUpload)}
              onClick={() => {
                const input = document.createElement("input");
                input.type = "file";
                input.accept = ".pdf,.csv,.xlsx,.xls,.sta,.mt940,.940,.mt9,.xml,.jpg,.jpeg,.png,.heic";
                input.onchange = (e) => {
                  const file = (e.target as HTMLInputElement).files?.[0];
                  if (file) handleFileUpload(file);
                };
                input.click();
              }}
            >
              {loading ? (
                <Loader2 size={32} className="mx-auto mb-4 text-blue-600 animate-spin" />
              ) : (
                <Upload size={32} className="mx-auto mb-4 text-gray-400" />
              )}
              <p className="text-sm text-gray-600">
                {loading ? t("upload.processing") : t("upload.drop_text")}
              </p>
              <p className="text-xs text-gray-400 mt-2">{t("upload.max_size")}</p>
            </div>

            {/* Parse result */}
            {parseResult && (
              <div className="mt-6 p-4 border border-gray-200 rounded-lg">
                <div className="flex items-center gap-2 mb-3">
                  {parseResult.invoice ? (
                    <CheckCircle size={18} className="text-green-500" />
                  ) : (
                    <AlertCircle size={18} className="text-yellow-500" />
                  )}
                  <span className="font-medium text-sm">
                    {parseResult.invoice
                      ? t("upload.detected")
                      : t("upload.incomplete")}
                  </span>
                  <span className="ml-auto text-xs text-gray-400">
                    {t("upload.method")}: {parseResult.parsing_method} | {t("upload.confidence")}: {Math.round(parseResult.confidence * 100)}%
                  </span>
                </div>

                {parseResult.warnings.map((w, i) => (
                  <p key={i} className="text-xs text-yellow-600 mb-1">{w}</p>
                ))}
                {parseResult.errors.map((e, i) => (
                  <p key={i} className="text-xs text-red-600 mb-1">{e}</p>
                ))}

                {parseResult.invoice && (
                  <div className="mt-4 flex gap-3">
                    <button
                      onClick={() => { setActiveTab("form"); setFormStep(5); }}
                      className="flex items-center gap-1 px-4 py-2 text-sm text-blue-600 border border-blue-300 rounded-lg hover:bg-blue-50"
                    >
                      <Eye size={16} /> {t("upload.review_edit")}
                    </button>
                    <button
                      onClick={handleGenerate}
                      disabled={loading}
                      className="flex items-center gap-1 px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
                    >
                      <Download size={16} /> {t("upload.generate_btn")}
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* === BATCH TAB === */}
        {activeTab === "batch" && (
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">{t("batch.title")}</h3>
            <p className="text-sm text-gray-600 mb-6">
              {t("batch.description")}
            </p>

            <div
              className={`border-2 border-dashed rounded-xl p-12 text-center transition-colors cursor-pointer ${
                dragOver ? "border-blue-500 bg-blue-50" : "border-gray-300 hover:border-gray-400"
              }`}
              onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
              onDragLeave={() => setDragOver(false)}
              onDrop={(e) => handleDrop(e, handleBatchUpload)}
              onClick={() => {
                const input = document.createElement("input");
                input.type = "file";
                input.accept = ".csv,.xlsx,.xls";
                input.onchange = (e) => {
                  const file = (e.target as HTMLInputElement).files?.[0];
                  if (file) handleBatchUpload(file);
                };
                input.click();
              }}
            >
              {loading ? (
                <Loader2 size={32} className="mx-auto mb-4 text-blue-600 animate-spin" />
              ) : (
                <Layers size={32} className="mx-auto mb-4 text-gray-400" />
              )}
              <p className="text-sm text-gray-600">
                {loading ? t("batch.processing") : t("batch.drop_text")}
              </p>
              <p className="text-xs text-gray-400 mt-2">{t("batch.file_types")}</p>
            </div>

            {/* Template columns info */}
            <div className="mt-6 p-4 bg-gray-50 rounded-lg">
              <h4 className="text-sm font-semibold text-gray-700 mb-2">{t("batch.columns_title")}</h4>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-1 text-xs text-gray-600">
                {[
                  "col_invoice_number", "col_invoice_date", "col_seller", "col_vat_id",
                  "col_buyer", "col_description", "col_quantity", "col_unit_price",
                  "col_vat_rate", "col_iban",
                ].map((col) => (
                  <span key={col} className="px-2 py-1 bg-white rounded border border-gray-200">{t(`batch.${col}`)}</span>
                ))}
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
