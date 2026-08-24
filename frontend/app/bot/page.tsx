import type { Metadata } from "next";
import { MarketingHeader } from "@/components/MarketingHeader";
import { SITE_NAME, SITE_URL } from "@/lib/seo";

export const metadata: Metadata = {
  title: "About Our Crawler",
  description: `Information about the CompetitorSignalBot web crawler used by ${SITE_NAME} to monitor publicly accessible competitor web pages on behalf of our users.`,
  alternates: { canonical: `${SITE_URL}/bot` },
};

/**
 * Linked from the crawler's User-Agent header (see backend
 * CRAWLER_USER_AGENT) — site owners who notice this bot's traffic can land
 * here to understand what it is and how to reach us. This page exists
 * specifically because an unexplained bot showing up in someone's access
 * logs reads as suspicious; a linked, honest explanation is standard and
 * expected practice for any crawler operated commercially.
 */
export default function BotInfoPage() {
  return (
    <div className="min-h-screen bg-white">
      <MarketingHeader />
      <main className="max-w-2xl mx-auto px-6 py-16">
        <h1 className="text-2xl font-semibold text-gray-900 mb-6">About the CompetitorSignalBot crawler</h1>

        <div className="space-y-6 text-sm text-gray-700 leading-relaxed">
          <p>
            If you&apos;re reading this because you noticed <code className="bg-gray-100 px-1.5 py-0.5 rounded">CompetitorSignalBot</code> in
            your access logs: this bot belongs to {SITE_NAME}, a service that lets our users monitor specific
            public pages of your website — for example, a pricing or changelog page — for changes they&apos;ve
            explicitly chosen to track.
          </p>

          <section>
            <h2 className="font-semibold text-gray-900 mb-2">What it does</h2>
            <ul className="list-disc pl-5 space-y-1.5">
              <li>Fetches only specific URLs a user has explicitly added to monitor — never a full crawl of your site.</li>
              <li>Checks each page on a daily or weekly schedule, chosen by the user, not continuously.</li>
              <li>Reads publicly accessible pages only — it never attempts to log in or access anything behind authentication.</li>
              <li>Respects your <code className="bg-gray-100 px-1.5 py-0.5 rounded">robots.txt</code> and standard rate limits.</li>
            </ul>
          </section>

          <section>
            <h2 className="font-semibold text-gray-900 mb-2">If you&apos;d like it to stop</h2>
            <p>
              Add a disallow rule for <code className="bg-gray-100 px-1.5 py-0.5 rounded">CompetitorSignalBot</code> in
              your <code className="bg-gray-100 px-1.5 py-0.5 rounded">robots.txt</code> and we&apos;ll honor it on the next check.
              You&apos;re also welcome to contact us directly (below) and we&apos;ll stop monitoring your site.
            </p>
          </section>

          <section>
            <h2 className="font-semibold text-gray-900 mb-2">Contact</h2>
            <p>
              Questions, concerns, or a request to be excluded: <a href="mailto:bot@competitorsignal.com" className="text-gray-900 underline">bot@competitorsignal.com</a>
            </p>
          </section>
        </div>
      </main>
    </div>
  );
}
