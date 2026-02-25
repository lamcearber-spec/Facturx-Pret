/**
 * Factur-X Prêt site configuration.
 */

export const siteConfig = {
  name: "Factur-X Prêt",
  domain: "facturx-pret.fr",
  tagline: "Créez vos factures Factur-X — conforme EN 16931",
  logoText: "FX",
  supportEmail: "support@facturx-pret.fr",
} as const;

export const apiConfig = {
  baseUrl: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8004",
  endpoints: {
    generate: "/api/v1/invoice/generate",
    upload: "/api/v1/invoice/upload",
    convert: "/api/v1/invoice/convert",
    batch: "/api/v1/invoice/batch",
    validate: "/api/v1/invoice/validate",
    previewXml: "/api/v1/invoice/preview-xml",
  },
  timeout: 60000,
} as const;

export const uploadConfig = {
  maxFileSize: 50 * 1024 * 1024,
  allowedExtensions: [
    "pdf", "csv", "xlsx", "xls",
    "sta", "mt940", "940", "mt9",
    "xml",
    "jpg", "jpeg", "png", "heic",
  ],
} as const;
