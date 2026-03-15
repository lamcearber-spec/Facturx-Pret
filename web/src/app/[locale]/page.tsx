"use client";

import { useState } from "react";
import { useTranslations, useLocale } from "next-intl";
import { Link } from "@/i18n/navigation";
import {
  FileText, Upload, Download, CheckCircle, Shield, Cpu,
  FileSpreadsheet, Image, Code2, Layers, Clock, Zap,
  ChevronDown, ChevronUp, ArrowRight, Menu, X,
} from "lucide-react";
import { siteConfig } from "@/config";
import { LanguageSwitcher } from "@/components/ui/LanguageSwitcher";

export default function LandingPage() {
  const t = useTranslations();
  const locale = useLocale();
  const [openFaq, setOpenFaq] = useState<number | null>(null);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <div className="min-h-screen bg-white">
      {/* Header */}
      <header className="sticky top-0 z-50 bg-white/80 backdrop-blur-md border-b border-gray-100">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-lg bg-blue-600 flex items-center justify-center text-white font-bold text-sm">
                {siteConfig.logoText}
              </div>
              <span className="font-semibold text-lg text-gray-900">{siteConfig.name}</span>
            </div>

            {/* Desktop nav */}
            <nav className="hidden md:flex items-center gap-6">
              <a href="#features" className="text-sm text-gray-600 hover:text-gray-900">
                {t("features.title")}
              </a>
              <a href="#pricing" className="text-sm text-gray-600 hover:text-gray-900">
                {t("pricing.title")}
              </a>
              <a href="#faq" className="text-sm text-gray-600 hover:text-gray-900">
                {t("faq.title")}
              </a>
              <LanguageSwitcher variant="compact" />
              <Link
                href="/generator"
                className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors"
              >
                {t("hero.cta_primary")}
              </Link>
            </nav>

            {/* Mobile menu button */}
            <button
              className="md:hidden p-2"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            >
              {mobileMenuOpen ? <X size={20} /> : <Menu size={20} />}
            </button>
          </div>

          {/* Mobile nav */}
          {mobileMenuOpen && (
            <div className="md:hidden py-4 border-t border-gray-100">
              <div className="flex flex-col gap-3">
                <a href="#features" className="text-sm text-gray-600 py-2">{t("features.title")}</a>
                <a href="#pricing" className="text-sm text-gray-600 py-2">{t("pricing.title")}</a>
                <a href="#faq" className="text-sm text-gray-600 py-2">{t("faq.title")}</a>
                <LanguageSwitcher variant="minimal" />
                <Link
                  href="/generator"
                  className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg text-center"
                >
                  {t("hero.cta_primary")}
                </Link>
              </div>
            </div>
          )}
        </div>
      </header>

      {/* Hero */}
      <section className="pt-20 pb-16 sm:pt-28 sm:pb-24">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <div className="inline-flex items-center px-3 py-1 rounded-full bg-blue-50 text-blue-700 text-xs font-medium mb-6">
            <Shield size={14} className="mr-1.5" />
            {t("hero.badge")}
          </div>

          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-gray-900 mb-6 leading-tight">
            {t("hero.headline")}
          </h1>
          <p className="text-lg sm:text-xl text-gray-600 max-w-2xl mx-auto mb-10">
            {t("hero.subheadline")}
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              href="/generator"
              className="inline-flex items-center justify-center px-6 py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors text-base"
            >
              <FileText size={18} className="mr-2" />
              {t("hero.cta_primary")}
              <ArrowRight size={16} className="ml-2" />
            </Link>
            <Link
              href="/generator?tab=upload"
              className="inline-flex items-center justify-center px-6 py-3 border border-gray-300 text-gray-700 font-medium rounded-lg hover:bg-gray-50 transition-colors text-base"
            >
              <Upload size={18} className="mr-2" />
              {t("hero.cta_secondary")}
            </Link>
          </div>

          {/* Format badges */}
          <div className="mt-12 flex flex-wrap justify-center gap-3">
            {["zugferd", "facturx", "en16931", "pdfa3", "cii"].map((key) => (
              <span
                key={key}
                className="px-3 py-1 bg-gray-100 text-gray-700 text-xs font-medium rounded-full"
              >
                {t(`formats.${key}`)}
              </span>
            ))}
          </div>
        </div>
      </section>

      {/* How it works */}
      <section className="py-16 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl font-bold text-center text-gray-900 mb-12">
            {t("how_it_works.title")}
          </h2>
          <div className="grid md:grid-cols-3 gap-8">
            {[
              { icon: Upload, num: "1", title: t("how_it_works.step1_title"), desc: t("how_it_works.step1_desc") },
              { icon: Cpu, num: "2", title: t("how_it_works.step2_title"), desc: t("how_it_works.step2_desc") },
              { icon: Download, num: "3", title: t("how_it_works.step3_title"), desc: t("how_it_works.step3_desc") },
            ].map((step) => (
              <div key={step.num} className="text-center">
                <div className="w-16 h-16 rounded-2xl bg-blue-100 flex items-center justify-center mx-auto mb-4">
                  <step.icon size={28} className="text-blue-600" />
                </div>
                <div className="text-sm text-blue-600 font-semibold mb-2">
                  {t("how_it_works.step")} {step.num}
                </div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">{step.title}</h3>
                <p className="text-gray-600 text-sm">{step.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl font-bold text-center text-gray-900 mb-12">
            {t("features.title")}
          </h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {[
              { key: "en16931", icon: CheckCircle },
              { key: "pdfa3", icon: FileText },
              { key: "cii_xml", icon: Code2 },
              { key: "all_formats", icon: FileSpreadsheet },
              { key: "ai_parsing", icon: Cpu },
              { key: "batch", icon: Layers },
              { key: "mandate", icon: Clock },
              { key: "xmp_metadata", icon: Shield },
            ].map(({ key, icon: Icon }) => (
              <div
                key={key}
                className="p-6 rounded-xl border border-gray-200 hover:border-blue-200 hover:shadow-sm transition-all"
              >
                <div className="w-10 h-10 rounded-lg bg-blue-50 flex items-center justify-center mb-4">
                  <Icon size={20} className="text-blue-600" />
                </div>
                <h3 className="font-semibold text-gray-900 mb-2">
                  {t(`features.${key}.title`)}
                </h3>
                <p className="text-sm text-gray-600">
                  {t(`features.${key}.desc`)}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing */}
      <section id="pricing" className="py-16 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl font-bold text-center text-gray-900 mb-12">
            {t("pricing.title")}
          </h2>
          <div className="grid md:grid-cols-4 gap-6">
            {[
              { key: "free", price: "0", desc: t("pricing.free_desc"), highlight: false },
              { key: "starter", price: t("pricing.starter_price"), desc: t("pricing.starter_desc"), highlight: false },
              { key: "pro", price: t("pricing.pro_price"), desc: t("pricing.pro_desc"), highlight: true },
              { key: "business", price: t("pricing.business_price"), desc: t("pricing.business_desc"), highlight: false },
            ].map((plan) => (
              <div
                key={plan.key}
                className={`p-6 rounded-xl border ${
                  plan.highlight
                    ? "border-blue-600 ring-2 ring-blue-100 bg-white"
                    : "border-gray-200 bg-white"
                }`}
              >
                <h3 className="font-semibold text-gray-900 mb-2">
                  {t(`pricing.${plan.key}`)}
                </h3>
                <div className="mb-4">
                  <span className="text-3xl font-bold text-gray-900">{plan.price}€</span>
                  {plan.price !== "0" && (
                    <span className="text-sm text-gray-500 ml-1">{t("pricing.per_month")}</span>
                  )}
                </div>
                <p className="text-sm text-gray-600 mb-6">{plan.desc}</p>
                <Link
                  href="/generator"
                  className={`block text-center px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    plan.highlight
                      ? "bg-blue-600 text-white hover:bg-blue-700"
                      : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                  }`}
                >
                  {t("pricing.cta")}
                </Link>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* FAQ */}
      <section id="faq" className="py-16">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl font-bold text-center text-gray-900 mb-12">
            {t("faq.title")}
          </h2>
          <div className="space-y-3">
            {[1, 2, 3, 4, 5, 6].map((i) => (
              <div
                key={i}
                className="border border-gray-200 rounded-lg overflow-hidden"
              >
                <button
                  className="w-full flex items-center justify-between px-6 py-4 text-left hover:bg-gray-50 transition-colors"
                  onClick={() => setOpenFaq(openFaq === i ? null : i)}
                >
                  <span className="font-medium text-gray-900">{t(`faq.q${i}`)}</span>
                  {openFaq === i ? (
                    <ChevronUp size={18} className="text-gray-400 flex-shrink-0" />
                  ) : (
                    <ChevronDown size={18} className="text-gray-400 flex-shrink-0" />
                  )}
                </button>
                {openFaq === i && (
                  <div className="px-6 pb-4 text-sm text-gray-600">
                    {t(`faq.a${i}`)}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Footer is rendered by layout.tsx */}
    </div>
  );
}
