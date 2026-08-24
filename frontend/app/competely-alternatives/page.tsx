import type { Metadata } from "next";
import { SeoLandingPage } from "@/components/SeoLandingPage";
import { ALTERNATIVES_PAGES } from "@/lib/seoContent";
import { SITE_URL } from "@/lib/seo";

const content = ALTERNATIVES_PAGES["competely-alternatives"];

export const metadata: Metadata = {
  title: content.metaTitle,
  description: content.metaDescription,
  alternates: { canonical: `${SITE_URL}/competely-alternatives` },
  openGraph: {
    title: content.metaTitle,
    description: content.metaDescription,
    url: `${SITE_URL}/competely-alternatives`,
  },
};

export default function Page() {
  return <SeoLandingPage content={content} />;
}
