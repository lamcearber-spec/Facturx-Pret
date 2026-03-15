import { Inter } from "next/font/google";
import { NextIntlClientProvider } from "next-intl";
import { getMessages } from "next-intl/server";
import { notFound } from "next/navigation";
import type { Metadata } from "next";
import { locales } from "@/i18n/config";
import { Footer } from "@/components/ui/Footer";

const inter = Inter({ subsets: ["latin"] });

export function generateStaticParams() {
  return locales.map((locale) => ({ locale }));
}

export async function generateMetadata({
  params: { locale },
}: {
  params: { locale: string };
}): Promise<Metadata> {
  const isFR = locale === "fr";
  return {
    title: isFR
      ? "Factur-X Prêt — Créez vos factures Factur-X"
      : "Factur-X Prêt — Create Factur-X Invoices",
    description: isFR
      ? "Générez des factures conformes EN 16931 au format Factur-X 1.0.8. PDF/A-3 avec XML CII intégré."
      : "Generate EN 16931 compliant Factur-X 1.0.8 invoices. PDF/A-3 with embedded CII XML.",
    alternates: {
      canonical: `/${locale}`,
      languages: {
        fr: "/fr",
        en: "/en",
        "x-default": "/fr",
      },
    },
    openGraph: {
      title: isFR
        ? "Factur-X Prêt — Créez vos factures Factur-X"
        : "Factur-X Prêt — Create Factur-X Invoices",
      description: isFR
        ? "Générez des factures conformes EN 16931 au format Factur-X 1.0.8. PDF/A-3 avec XML CII intégré."
        : "Generate EN 16931 compliant Factur-X 1.0.8 invoices. PDF/A-3 with embedded CII XML.",
      url: `https://facturx-pret.fr/${locale}`,
      siteName: "Factur-X Prêt",
      locale: isFR ? "fr_FR" : "en_GB",
      alternateLocale: isFR ? "en_GB" : "fr_FR",
      type: "website",
    },
    twitter: {
      card: "summary",
      title: isFR
        ? "Factur-X Prêt — Créez vos factures Factur-X"
        : "Factur-X Prêt — Create Factur-X Invoices",
      description: isFR
        ? "Générez des factures conformes EN 16931 au format Factur-X 1.0.8."
        : "Generate EN 16931 compliant Factur-X 1.0.8 invoices.",
    },
  };
}

const jsonLd = {
  "@context": "https://schema.org",
  "@type": "SoftwareApplication",
  name: "Factur-X Prêt",
  applicationCategory: "BusinessApplication",
  operatingSystem: "Web",
  offers: {
    "@type": "AggregateOffer",
    lowPrice: "0",
    highPrice: "99",
    priceCurrency: "EUR",
  },
  provider: {
    "@type": "Organization",
    name: "Radom UG (haftungsbeschränkt)",
    address: {
      "@type": "PostalAddress",
      streetAddress: "Taunusanlage 8",
      addressLocality: "Frankfurt am Main",
      postalCode: "60329",
      addressCountry: "DE",
    },
  },
  description:
    "Generate EN 16931 compliant Factur-X 1.0.8 invoices. PDF/A-3 with embedded CII XML.",
};

export default async function LocaleLayout({
  children,
  params: { locale },
}: {
  children: React.ReactNode;
  params: { locale: string };
}) {
  if (!locales.includes(locale as any)) {
    notFound();
  }

  const messages = await getMessages();

  return (
    <html lang={locale}>
      <head>
        <link rel="icon" href="/favicon.svg" type="image/svg+xml" />
        <link rel="manifest" href="/manifest.json" />
        <meta name="theme-color" content="#2563EB" />
        <link rel="alternate" hrefLang="fr" href="/fr" />
        <link rel="alternate" hrefLang="en" href="/en" />
        <link rel="alternate" hrefLang="x-default" href="/fr" />
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
        />
      </head>
      <body className={inter.className}>
        <NextIntlClientProvider messages={messages}>
          {children}
          <Footer />
        </NextIntlClientProvider>
      </body>
    </html>
  );
}
