import { Inter } from "next/font/google";
import { NextIntlClientProvider } from "next-intl";
import { getMessages } from "next-intl/server";
import { notFound } from "next/navigation";
import type { Metadata } from "next";
import { locales } from "@/i18n/config";

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
      locale: isFR ? "fr_FR" : "en_GB",
      alternateLocale: isFR ? "en_GB" : "fr_FR",
    },
  };
}

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
        <link rel="alternate" hrefLang="fr" href="/fr" />
        <link rel="alternate" hrefLang="en" href="/en" />
        <link rel="alternate" hrefLang="x-default" href="/fr" />
      </head>
      <body className={inter.className}>
        <NextIntlClientProvider messages={messages}>
          {children}
        </NextIntlClientProvider>
      </body>
    </html>
  );
}
