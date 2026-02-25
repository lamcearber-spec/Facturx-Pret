/**
 * API client for Factur-X Pret API.
 */

import axios from "axios";
import { apiConfig } from "@/config";
import type { InvoiceRequest, ParseResult } from "@/types/invoice";

const api = axios.create({
  baseURL: apiConfig.baseUrl,
  timeout: apiConfig.timeout,
});

/** Generate Factur-X PDF from invoice data. Returns PDF blob. */
export async function generateInvoice(invoice: InvoiceRequest): Promise<Blob> {
  const response = await api.post(apiConfig.endpoints.generate, invoice, {
    responseType: "blob",
  });
  return response.data;
}

/** Upload a file and parse invoice data. */
export async function uploadAndParse(file: File): Promise<ParseResult> {
  const formData = new FormData();
  formData.append("file", file);
  const response = await api.post(apiConfig.endpoints.upload, formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return response.data;
}

/** Upload a file and convert directly to Factur-X PDF. */
export async function convertToFacturX(file: File): Promise<Blob> {
  const formData = new FormData();
  formData.append("file", file);
  const response = await api.post(apiConfig.endpoints.convert, formData, {
    headers: { "Content-Type": "multipart/form-data" },
    responseType: "blob",
  });
  return response.data;
}

/** Batch generate Factur-X PDFs from CSV/Excel. Returns ZIP blob. */
export async function batchGenerate(file: File): Promise<Blob> {
  const formData = new FormData();
  formData.append("file", file);
  const response = await api.post(apiConfig.endpoints.batch, formData, {
    headers: { "Content-Type": "multipart/form-data" },
    responseType: "blob",
  });
  return response.data;
}

/** Validate invoice data without generating. */
export async function validateInvoice(invoice: InvoiceRequest) {
  const response = await api.post(apiConfig.endpoints.validate, invoice);
  return response.data;
}

/** Get CII XML preview. */
export async function previewXml(invoice: InvoiceRequest): Promise<string> {
  const response = await api.post(apiConfig.endpoints.previewXml, invoice, {
    responseType: "text",
  });
  return response.data;
}
