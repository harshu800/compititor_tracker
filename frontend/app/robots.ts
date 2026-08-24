import type { MetadataRoute } from "next";
import { SITE_URL } from "@/lib/seo";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: [
      {
        userAgent: "*",
        allow: "/",
        // The whole authenticated app (dashboard, competitors, changes,
        // alerts, reports, settings) has nothing worth indexing and
        // shouldn't show up in search results — only the public marketing
        // and SEO landing pages should be crawled.
        disallow: ["/dashboard", "/competitors", "/changes", "/alerts", "/reports", "/settings"],
      },
    ],
    sitemap: `${SITE_URL}/sitemap.xml`,
  };
}
