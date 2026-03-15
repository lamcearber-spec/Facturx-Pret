import { useTranslations } from "next-intl";
import { getTranslations } from "next-intl/server";
import type { Metadata } from "next";
import { Link } from "@/i18n/navigation";

export async function generateMetadata({
  params: { locale },
}: {
  params: { locale: string };
}): Promise<Metadata> {
  const t = await getTranslations({ locale, namespace: "legal.mentions_legales" });
  return {
    title: t("title") + " — Factur-X Prêt",
    description: t("meta_description"),
    alternates: {
      canonical: `/${locale}/mentions-legales`,
      languages: { fr: "/fr/mentions-legales", en: "/en/mentions-legales" },
    },
  };
}

export default function MentionsLegalesPage() {
  const t = useTranslations("legal.mentions_legales");

  return (
    <div className="min-h-screen bg-white">
      <div className="max-w-3xl mx-auto px-4 py-16 sm:py-24">
        <Link href="/" className="text-sm text-blue-600 hover:text-blue-700 mb-8 inline-block">
          &larr; {useTranslations("legal.footer")("home")}
        </Link>

        <h1 className="text-3xl font-bold text-gray-900 mb-8">{t("title")}</h1>

        <div className="prose prose-gray max-w-none space-y-8">
          <section>
            <h2 className="text-xl font-semibold text-gray-900 mb-4">{t("editeur")}</h2>
            <div className="space-y-1 text-gray-600">
              <p><strong>{t("company")}</strong></p>
              <p>{t("address")}</p>
              <p>{t("register")}</p>
              <p>{t("vat_label")} : {t("vat")}</p>
              <p>{t("director_label")} : {t("director")}</p>
              <p>E-mail : <a href={`mailto:${t("email")}`} className="text-blue-600 hover:text-blue-700">{t("email")}</a></p>
              <p>Tél. : <a href={`tel:${t("phone")}`} className="text-blue-600 hover:text-blue-700">{t("phone")}</a></p>
            </div>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-gray-900 mb-4">{t("hebergement")}</h2>
            <p className="text-gray-600">{t("hebergement_text")}</p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-gray-900 mb-4">{t("informations")}</h2>
            <p className="text-gray-600">{t("informations_text")}</p>
          </section>
        </div>
      </div>
    </div>
  );
}
