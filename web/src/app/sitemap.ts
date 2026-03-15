import type { MetadataRoute } from "next";

const BASE_URL = "https://facturx-pret.fr";

const routes = [
  "/",
  "/generator",
  "/mentions-legales",
  "/confidentialite",
  "/cgv",
  "/contact",
];

const locales = ["fr", "en"];

export default function sitemap(): MetadataRoute.Sitemap {
  return locales.flatMap((locale) =>
    routes.map((route) => ({
      url: `${BASE_URL}/${locale}${route === "/" ? "" : route}`,
      lastModified: new Date(),
      changeFrequency: route === "/" ? ("weekly" as const) : ("monthly" as const),
      priority: route === "/" ? 1 : route === "/generator" ? 0.9 : 0.5,
    }))
  );
}
