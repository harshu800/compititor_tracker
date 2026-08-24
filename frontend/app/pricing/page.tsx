import { MarketingHeader } from "@/components/MarketingHeader";
import { PricingCards } from "@/components/PricingCards";
import { SITE_NAME } from "@/lib/seo";

export const metadata = {
  title: "Pricing",
  description: `Simple, transparent pricing for ${SITE_NAME} — the AI competitor monitoring and intelligence software for SaaS founders, product teams, and agencies. Start free.`,
};

const FAQS = [
  {
    q: "What counts as a \"monitored page\"?",
    a: "Any specific URL you track — a pricing page, homepage, changelog, blog, or a custom URL you add. Each competitor can have multiple monitored pages.",
  },
  {
    q: "What happens if I go over my plan's limits?",
    a: "You won't be able to add new competitors or pages past your plan's limit until you upgrade or archive existing ones — nothing you're already monitoring gets silently dropped.",
  },
  {
    q: "Can I change plans later?",
    a: "Yes. Reach out and we'll move your workspace to a new plan — your monitoring history stays intact.",
  },
  {
    q: "Do you monitor pages that require a login?",
    a: "No — only publicly accessible pages, and we respect robots.txt and reasonable rate limits on every site we check.",
  },
];

export default function PricingPage() {
  return (
    <div className="min-h-screen bg-white">
      <MarketingHeader />
      <main className="max-w-6xl mx-auto px-6 py-16">
        <div className="text-center mb-12">
          <h1 className="text-3xl md:text-4xl font-semibold text-gray-900 mb-3">
            Simple pricing, no surprises
          </h1>
          <p className="text-gray-500 max-w-xl mx-auto">
            Start free. Upgrade when you&apos;re tracking enough competitors that you need more room —
            never because a feature was held back.
          </p>
        </div>

        <PricingCards />

        <section className="max-w-2xl mx-auto mt-20">
          <h2 className="text-xl font-semibold text-gray-900 mb-6 text-center">Common questions</h2>
          <div className="space-y-6">
            {FAQS.map((faq) => (
              <div key={faq.q}>
                <h3 className="font-medium text-gray-900 mb-1">{faq.q}</h3>
                <p className="text-sm text-gray-500">{faq.a}</p>
              </div>
            ))}
          </div>
        </section>
      </main>
    </div>
  );
}
