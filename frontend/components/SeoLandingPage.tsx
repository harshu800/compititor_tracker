import Link from "next/link";
import { MarketingHeader } from "@/components/MarketingHeader";
import { PricingCards } from "@/components/PricingCards";
import { SeoPageContent } from "@/lib/seoContent";
import { SITE_NAME, SITE_URL } from "@/lib/seo";

export function SeoLandingPage({ content }: { content: SeoPageContent }) {
  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "SoftwareApplication",
    name: SITE_NAME,
    applicationCategory: "BusinessApplication",
    operatingSystem: "Web",
    description: content.metaDescription,
    url: `${SITE_URL}/${content.slug}`,
    offers: {
      "@type": "Offer",
      price: "0",
      priceCurrency: "USD",
      description: "Free plan available",
    },
  };

  return (
    <div className="min-h-screen bg-white">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />
      <MarketingHeader />

      <main>
        <section className="max-w-4xl mx-auto px-6 pt-16 pb-12 text-center">
          <p className="text-sm font-medium text-gray-500 mb-3">{content.eyebrow}</p>
          <h1 className="text-3xl md:text-4xl font-semibold text-gray-900 leading-tight mb-5">
            {content.h1}
          </h1>
          <p className="text-lg text-gray-500 max-w-2xl mx-auto mb-8">{content.intro}</p>
          <div className="flex items-center justify-center gap-3">
            <Link href="/sign-up" className="bg-gray-900 text-white rounded-lg px-6 py-3 text-sm font-medium hover:bg-gray-800">
              Start monitoring free
            </Link>
            <Link href="/pricing" className="border border-gray-300 rounded-lg px-6 py-3 text-sm font-medium hover:bg-gray-50">
              See pricing
            </Link>
          </div>
        </section>

        <section className="bg-gray-50 py-16">
          <div className="max-w-5xl mx-auto px-6 grid md:grid-cols-2 gap-8">
            {content.highlights.map((h) => (
              <div key={h.title} className="bg-white rounded-xl border border-gray-200 p-5">
                <h2 className="font-semibold text-gray-900 mb-2">{h.title}</h2>
                <p className="text-sm text-gray-500">{h.body}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="max-w-6xl mx-auto px-6 py-16">
          <h2 className="text-2xl font-semibold text-gray-900 text-center mb-10">Pricing</h2>
          <PricingCards />
        </section>

        <section className="max-w-2xl mx-auto px-6 pb-20">
          <h2 className="text-xl font-semibold text-gray-900 mb-6 text-center">Common questions</h2>
          <div className="space-y-6">
            {content.faqs.map((faq) => (
              <div key={faq.q}>
                <h3 className="font-medium text-gray-900 mb-1">{faq.q}</h3>
                <p className="text-sm text-gray-500">{faq.a}</p>
              </div>
            ))}
          </div>
        </section>
      </main>

      <footer className="border-t border-gray-100 py-8">
        <div className="max-w-6xl mx-auto px-6 text-sm text-gray-400 flex justify-between">
          <span>© {new Date().getFullYear()} {SITE_NAME}</span>
          <Link href="/pricing" className="hover:text-gray-600">Pricing</Link>
        </div>
      </footer>
    </div>
  );
}
