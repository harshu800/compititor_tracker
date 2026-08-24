import type { Metadata } from "next";
import { SeoLandingPage } from "@/components/SeoLandingPage";
import { SEO_PAGES } from "@/lib/seoContent";
import { SITE_URL } from "@/lib/seo";

const content = SEO_PAGES["competitor-price-tracking"];

export const metadata: Metadata = {
  title: content.metaTitle,
  description: content.metaDescription,
  alternates: { canonical: `${SITE_URL}/competitor-price-tracking` },
  openGraph: {
    title: content.metaTitle,
    description: content.metaDescription,
    url: `${SITE_URL}/competitor-price-tracking`,
  },
};

export default function Page() {
  return <SeoLandingPage content={content} />;
}
