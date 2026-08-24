import type { MetadataRoute } from "next";
import { SITE_URL } from "@/lib/seo";
import { SEO_PAGES, ALTERNATIVES_PAGES } from "@/lib/seoContent";

export default function sitemap(): MetadataRoute.Sitemap {
  const staticPages = ["", "pricing"];
  const seoPages = Object.keys(SEO_PAGES);
  const alternativesPages = Object.keys(ALTERNATIVES_PAGES);

  const allPaths = [...staticPages, ...seoPages, ...alternativesPages];

  return allPaths.map((path) => ({
    url: `${SITE_URL}/${path}`,
    lastModified: new Date(),
    changeFrequency: "weekly",
    priority: path === "" ? 1.0 : 0.8,
  }));
}
