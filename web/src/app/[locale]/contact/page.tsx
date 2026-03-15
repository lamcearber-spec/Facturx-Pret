import { useTranslations } from "next-intl";
import { getTranslations } from "next-intl/server";
import type { Metadata } from "next";
import { Link } from "@/i18n/navigation";
import { Mail, Building2, MapPin } from "lucide-react";

export async function generateMetadata({
  params: { locale },
}: {
  params: { locale: string };
}): Promise<Metadata> {
  const t = await getTranslations({ locale, namespace: "legal.contact" });
  return {
    title: t("title") + " — Factur-X Prêt",
    description: t("meta_description"),
    alternates: {
      canonical: `/${locale}/contact`,
      languages: { fr: "/fr/contact", en: "/en/contact" },
    },
  };
}

export default function ContactPage() {
  const t = useTranslations("legal.contact");

  return (
    <div className="min-h-screen bg-white">
      <div className="max-w-3xl mx-auto px-4 py-16 sm:py-24">
        <Link href="/" className="text-sm text-blue-600 hover:text-blue-700 mb-8 inline-block">
          &larr; {useTranslations("legal.footer")("home")}
        </Link>

        <h1 className="text-3xl font-bold text-gray-900 mb-4">{t("heading")}</h1>
        <p className="text-gray-600 mb-10">{t("text")}</p>

        <div className="space-y-6">
          <div className="flex items-start gap-4">
            <div className="w-10 h-10 rounded-lg bg-blue-50 flex items-center justify-center flex-shrink-0">
              <Mail size={20} className="text-blue-600" />
            </div>
            <div>
              <p className="font-medium text-gray-900 mb-1">{t("email_label")}</p>
              <a href="mailto:support@facturx-pret.fr" className="text-blue-600 hover:text-blue-700">
                support@facturx-pret.fr
              </a>
            </div>
          </div>

          <div className="flex items-start gap-4">
            <div className="w-10 h-10 rounded-lg bg-blue-50 flex items-center justify-center flex-shrink-0">
              <Building2 size={20} className="text-blue-600" />
            </div>
            <div>
              <p className="font-medium text-gray-900 mb-1">{t("company_label")}</p>
              <p className="text-gray-600">Radom UG (haftungsbeschränkt)</p>
            </div>
          </div>

          <div className="flex items-start gap-4">
            <div className="w-10 h-10 rounded-lg bg-blue-50 flex items-center justify-center flex-shrink-0">
              <MapPin size={20} className="text-blue-600" />
            </div>
            <div>
              <p className="font-medium text-gray-900 mb-1">{t("address_label")}</p>
              <p className="text-gray-600">Taunusanlage 8, 60329 Frankfurt am Main</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
