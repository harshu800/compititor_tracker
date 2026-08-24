import type { Metadata } from "next";
import { SeoLandingPage } from "@/components/SeoLandingPage";
import { ALTERNATIVES_PAGES } from "@/lib/seoContent";
import { SITE_URL } from "@/lib/seo";

const content = ALTERNATIVES_PAGES["visualping-alternatives"];

export const metadata: Metadata = {
  title: content.metaTitle,
  description: content.metaDescription,
  alternates: { canonical: `${SITE_URL}/visualping-alternatives` },
  openGraph: {
    title: content.metaTitle,
    description: content.metaDescription,
    url: `${SITE_URL}/visualping-alternatives`,
  },
};

export default function Page() {
  return <SeoLandingPage content={content} />;
}
