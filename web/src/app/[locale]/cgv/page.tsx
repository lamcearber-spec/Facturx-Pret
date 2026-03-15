import { useTranslations } from "next-intl";
import { getTranslations } from "next-intl/server";
import type { Metadata } from "next";
import { Link } from "@/i18n/navigation";

export async function generateMetadata({
  params: { locale },
}: {
  params: { locale: string };
}): Promise<Metadata> {
  const t = await getTranslations({ locale, namespace: "legal.cgv" });
  return {
    title: t("title") + " — Factur-X Prêt",
    description: t("meta_description"),
    alternates: {
      canonical: `/${locale}/cgv`,
      languages: { fr: "/fr/cgv", en: "/en/cgv" },
    },
  };
}

export default function CGVPage() {
  const t = useTranslations("legal.cgv");

  const sections = [
    { title: "objet_title", text: "objet_text" },
    { title: "tarifs_title", text: "tarifs_text" },
    { title: "paiement_title", text: "paiement_text" },
    { title: "responsabilite_title", text: "responsabilite_text" },
    { title: "resiliation_title", text: "resiliation_text" },
    { title: "droit_applicable_title", text: "droit_applicable_text" },
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
