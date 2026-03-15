import { useTranslations } from "next-intl";
import { getTranslations } from "next-intl/server";
import type { Metadata } from "next";
import { Link } from "@/i18n/navigation";

export async function generateMetadata({
  params: { locale },
}: {
  params: { locale: string };
}): Promise<Metadata> {
  const t = await getTranslations({ locale, namespace: "legal.confidentialite" });
  return {
    title: t("title") + " — Factur-X Prêt",
    description: t("meta_description"),
    alternates: {
      canonical: `/${locale}/confidentialite`,
      languages: { fr: "/fr/confidentialite", en: "/en/confidentialite" },
    },
  };
}

export default function ConfidentialitePage() {
  const t = useTranslations("legal.confidentialite");

  const sections = [
    { title: "collecte_title", text: "collecte_text" },
    { title: "utilisation_title", text: "utilisation_text" },
    { title: "conservation_title", text: "conservation_text" },
    { title: "droits_title", text: "droits_text" },
    { title: "cookies_title", text: "cookies_text" },
    { title: "contact_title", text: "contact_text" },
  ];

  return (
    <div className="min-h-screen bg-white">
      <div className="max-w-3xl mx-auto px-4 py-16 sm:py-24">
        <Link href="/" className="text-sm text-blue-600 hover:text-blue-700 mb-8 inline-block">
          &larr; {useTranslations("legal.footer")("home")}
        </Link>

        <h1 className="text-3xl font-bold text-gray-900 mb-4">{t("title")}</h1>
        <p className="text-gray-600 mb-8">{t("intro")}</p>

        <div className="space-y-8">
          {sections.map(({ title, text }) => (
            <section key={title}>
              <h2 className="text-xl font-semibold text-gray-900 mb-3">{t(title)}</h2>
              <p className="text-gray-600">{t(text)}</p>
            </section>
          ))}
        </div>
      </div>
    </div>
  );
}
