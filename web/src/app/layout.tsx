import type { Metadata } from "next";
import { redirect } from "next/navigation";
import "./globals.css";

export const metadata: Metadata = {
  title: "Factur-X Prêt — Créez vos factures Factur-X",
  description: "Générez des factures conformes EN 16931 au format Factur-X 1.0.8. PDF/A-3 avec XML CII intégré.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
