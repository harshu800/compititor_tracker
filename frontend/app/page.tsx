import Link from "next/link";
import { redirect } from "next/navigation";
import { auth } from "@clerk/nextjs/server";
import { MarketingHeader } from "@/components/MarketingHeader";
import { PricingCards } from "@/components/PricingCards";
import { SITE_NAME } from "@/lib/seo";

const EXAMPLE = {
  competitor: "Acme CRM",
  before: "$29/month",
  after: "$39/month",
  why: "Your $35 plan is now cheaper than their Pro plan.",
  action: "Review your pricing comparison page and highlight the pricing difference.",
};

const STEPS = [
  { title: "Add a competitor", body: "Enter their site — we suggest their pricing, features, and changelog pages automatically." },
  { title: "We watch, quietly", body: "Daily or weekly checks, filtered to ignore cookie banners, tracking IDs, and other noise." },
  { title: "You get the decision, not the diff", body: "A meaningful change becomes a scored, explained, actionable alert — not a wall of HTML." },
];

export default async function LandingPage() {
  const { userId } = await auth();
  if (userId) {
    redirect("/dashboard");
  }

  return (
    <div className="min-h-screen bg-white">
      <MarketingHeader />

      <main>
        <section className="max-w-4xl mx-auto px-6 pt-20 pb-16 text-center">
          <h1 className="text-4xl md:text-5xl font-semibold text-gray-900 leading-tight mb-5">
            Know what your competitors changed —<br className="hidden md:block" /> and what to do about it
          </h1>
          <p className="text-lg text-gray-500 max-w-2xl mx-auto mb-8">
            {SITE_NAME} monitors pricing, features, and positioning across your competitors&apos; public
            pages, and turns every meaningful change into a scored, explained, actionable alert.
          </p>
          <div className="flex items-center justify-center gap-3">
            <Link href="/sign-up" className="bg-gray-900 text-white rounded-lg px-6 py-3 text-sm font-medium hover:bg-gray-800">
              Start monitoring free
            </Link>
            <Link href="/pricing" className="border border-gray-300 rounded-lg px-6 py-3 text-sm font-medium hover:bg-gray-50">
              See pricing
            </Link>
          </div>
        </section>

        <section className="max-w-2xl mx-auto px-6 pb-20">
          <div className="rounded-2xl border border-gray-200 overflow-hidden">
            <div className="bg-red-50 px-5 py-3 border-b border-gray-100 flex items-center gap-2 text-sm font-medium text-red-800">
              🔴 {EXAMPLE.competitor} changed pricing
            </div>
            <div className="px-5 py-5 space-y-4 text-sm">
              <div className="flex gap-8">
                <div>
                  <div className="text-xs text-gray-400 mb-1">Pro plan — before</div>
                  <div className="font-medium text-gray-900 line-through decoration-red-400">{EXAMPLE.before}</div>
                </div>
                <div>
                  <div className="text-xs text-gray-400 mb-1">Pro plan — after</div>
                  <div className="font-medium text-gray-900">{EXAMPLE.after}</div>
                </div>
              </div>
              <div>
                <div className="text-xs text-gray-400 mb-1">Why it matters</div>
                <p className="text-gray-700">{EXAMPLE.why}</p>
              </div>
              <div className="bg-blue-50 border border-blue-100 rounded-lg p-3">
                <div className="text-xs text-blue-700 font-medium mb-1">Suggested action</div>
                <p className="text-blue-900">{EXAMPLE.action}</p>
              </div>
            </div>
          </div>
        </section>

        <section className="bg-gray-50 py-20">
          <div className="max-w-5xl mx-auto px-6 grid md:grid-cols-3 gap-8">
            {STEPS.map((step, i) => (
              <div key={step.title}>
                <div className="text-xs font-medium text-gray-400 mb-2">STEP {i + 1}</div>
                <h3 className="font-semibold text-gray-900 mb-2">{step.title}</h3>
                <p className="text-sm text-gray-500">{step.body}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="max-w-6xl mx-auto px-6 py-20">
          <h2 className="text-2xl font-semibold text-gray-900 text-center mb-10">Pricing that scales with how many competitors you track</h2>
          <PricingCards />
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
