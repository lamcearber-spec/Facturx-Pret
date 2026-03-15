"use client";

import { useTranslations } from "next-intl";
import { Link } from "@/i18n/navigation";
import { LanguageSwitcher } from "@/components/ui/LanguageSwitcher";

export function Footer() {
  const t = useTranslations("legal.footer");

  return (
    <footer className="py-8 border-t border-gray-200 bg-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="text-sm text-gray-500">{t("copyright")}</div>
            <LanguageSwitcher variant="compact" />
          </div>
          <nav className="flex flex-wrap justify-center gap-6 text-sm text-gray-500">
            <Link href="/" className="hover:text-gray-700">{t("home")}</Link>
            <Link href="/mentions-legales" className="hover:text-gray-700">{t("mentions_legales")}</Link>
            <Link href="/confidentialite" className="hover:text-gray-700">{t("confidentialite")}</Link>
            <Link href="/cgv" className="hover:text-gray-700">{t("cgv")}</Link>
            <Link href="/contact" className="hover:text-gray-700">{t("contact")}</Link>
          </nav>
        </div>
      </div>
    </footer>
  );
}
