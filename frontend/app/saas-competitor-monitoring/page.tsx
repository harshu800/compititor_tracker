import type { Metadata } from "next";
import { SeoLandingPage } from "@/components/SeoLandingPage";
import { SEO_PAGES } from "@/lib/seoContent";
import { SITE_URL } from "@/lib/seo";

const content = SEO_PAGES["saas-competitor-monitoring"];

export const metadata: Metadata = {
  title: content.metaTitle,
  description: content.metaDescription,
  alternates: { canonical: `${SITE_URL}/saas-competitor-monitoring` },
  openGraph: {
    title: content.metaTitle,
    description: content.metaDescription,
    url: `${SITE_URL}/saas-competitor-monitoring`,
  },
};

export default function Page() {
  return <SeoLandingPage content={content} />;
}
