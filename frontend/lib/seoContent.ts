/**
 * Content for the keyword-targeted / "alternatives" landing pages under
 * app/(seo)/. Each entry has genuinely distinct copy (not a templated
 * keyword swap) — search engines treat near-duplicate pages as thin
 * content and won't rank them well, so each page earns its own angle:
 * a specific feature, a specific audience, or a specific comparison.
 *
 * "Alternatives" pages name real competing products (standard, legal
 * comparative marketing — nominative fair use) but deliberately make no
 * factual claims ABOUT those products' current features, pricing, or
 * limitations, since that can't be verified here. Copy is framed around
 * what CompetitorSignal does, not what the other product doesn't.
 */

export interface Highlight {
  title: string;
  body: string;
}

export interface Faq {
  q: string;
  a: string;
}

export interface SeoPageContent {
  slug: string;
  metaTitle: string;
  metaDescription: string;
  eyebrow: string;
  h1: string;
  intro: string;
  highlights: Highlight[];
  faqs: Faq[];
}

export const SEO_PAGES: Record<string, SeoPageContent> = {
  "competitor-monitoring-software": {
    slug: "competitor-monitoring-software",
    metaTitle: "Competitor Monitoring Software",
    metaDescription:
      "CompetitorSignal is competitor monitoring software that watches your competitors' pricing, features, and homepage positioning automatically, and tells you why each change matters.",
    eyebrow: "Competitor monitoring software",
    h1: "Competitor monitoring software that explains what changed, not just that it did",
    intro:
      "Most competitor monitoring tools stop at \"this page changed.\" CompetitorSignal goes further: it classifies what changed (pricing, a feature, positioning), scores how much it matters, and tells you what to do about it — so monitoring becomes a source of decisions, not another feed to scroll.",
    highlights: [
      { title: "Automatic, filtered monitoring", body: "Daily or weekly checks across pricing, homepage, features, changelog, and blog pages, with cookie banners, tracking IDs, and other noise filtered out before anything reaches you." },
      { title: "Change classification", body: "Every meaningful change is categorized — pricing, feature, positioning, CTA, and more — so you can filter your feed to exactly what you care about." },
      { title: "Deterministic impact scoring", body: "A 0–100 impact score, computed by the backend (not left to an AI to make up), so \"critical\" always means the same thing." },
      { title: "Plain-English explanations", body: "AI-generated \"why it matters\" and \"recommended action\" for every change, grounded only in what actually changed — no invented facts." },
    ],
    faqs: [
      { q: "How is this different from a screenshot-diff tool?", a: "Screenshot and HTML diff tools show you raw change; CompetitorSignal adds the layer on top — classification, business impact scoring, and a recommended action — so you're not left interpreting a wall of diffs yourself." },
      { q: "Does it monitor pages that require login?", a: "No — only publicly accessible pages, and it respects robots.txt and reasonable rate limits on every site it checks." },
      { q: "How many competitors can I monitor?", a: "The Free plan covers 5 competitors and 20 pages; Pro covers 50 competitors and 500 pages. See the pricing page for details." },
    ],
  },

  "competitor-intelligence-software": {
    slug: "competitor-intelligence-software",
    metaTitle: "Competitor Intelligence Software",
    metaDescription:
      "Competitor intelligence software for SaaS founders and product teams — CompetitorSignal turns detected competitor changes into scored, explained, actionable intelligence.",
    eyebrow: "Competitor intelligence software",
    h1: "Turn competitor activity into intelligence you can act on",
    intro:
      "Competitor intelligence isn't just knowing that something changed — it's understanding whether it matters and what to do next. CompetitorSignal pairs automated monitoring with AI-generated business context, so your team spends time on decisions instead of manually checking competitor sites.",
    highlights: [
      { title: "Built for founders and small teams", body: "No dedicated competitive-intelligence analyst required — the dashboard is designed to be understood in under 10 seconds." },
      { title: "Weekly digest, not noise", body: "A weekly summary built strictly from actual detected changes — if there were only two meaningful changes that week, it says so, instead of manufacturing insights to fill space." },
      { title: "Review workflow built in", body: "Mark changes reviewed, important, or ignored — ignored changes won't keep re-alerting you unless the underlying page changes again meaningfully." },
      { title: "Export and share", body: "CSV export of your change history for reports, board updates, or sharing with a broader team." },
    ],
    faqs: [
      { q: "Do I need a competitive intelligence background to use this?", a: "No — it's built for SaaS founders and small product/marketing teams who need signal, not a full CI analyst toolkit." },
      { q: "Can I search and filter the change history?", a: "Yes — by competitor, change type, importance, date range, and free-text search across summaries and pages." },
      { q: "Is there a free tier?", a: "Yes — Free covers 5 competitors and 20 monitored pages with no time limit and no credit card required." },
    ],
  },

  "competitor-price-tracking": {
    slug: "competitor-price-tracking",
    metaTitle: "Competitor Price Tracking",
    metaDescription:
      "Automatic competitor price tracking — CompetitorSignal detects pricing page changes, extracts old vs. new prices, and scores the business impact automatically.",
    eyebrow: "Competitor price tracking",
    h1: "Know the moment a competitor changes their price — and by how much",
    intro:
      "Pricing changes are some of the highest-impact moves a competitor can make, and CompetitorSignal treats them that way: pricing changes carry the highest base impact score of any change type, so a price move never gets buried under minor copy edits.",
    highlights: [
      { title: "Structured price extraction", body: "Pricing pages are parsed for plan names and prices, not just diffed as raw text — so \"Pro — $29/month → $39/month\" is shown clearly, before/after." },
      { title: "New and removed plans, too", body: "If a competitor adds a new tier or drops one, that's detected and reported distinctly from a same-plan price change." },
      { title: "Immediate context", body: "\"Your $35 plan is now cheaper than their Pro plan\" — the kind of framing that turns a price change into an actual decision (update a comparison page, adjust positioning) instead of just a fact." },
      { title: "High-impact alerts", body: "Pricing changes are weighted highest among page types in the impact score, and can trigger an immediate email alert rather than waiting for a weekly digest." },
    ],
    faqs: [
      { q: "Does it handle annual vs. monthly pricing?", a: "Yes — billing period (month/year) is captured alongside the price itself." },
      { q: "What if a competitor's pricing page has no clear plan names?", a: "The system won't invent a plan name if it can't confidently detect one — it reports the price change with what it can verify and flags uncertainty rather than guessing." },
      { q: "Can I see price history over time?", a: "Yes — the Reports page includes a pricing-changes-over-time view alongside feature and positioning changes." },
    ],
  },

  "competitor-feature-tracking": {
    slug: "competitor-feature-tracking",
    metaTitle: "Competitor Feature Tracking",
    metaDescription:
      "Track new competitor features automatically. CompetitorSignal monitors changelogs, feature pages, and product pages and flags new features as they ship.",
    eyebrow: "Competitor feature tracking",
    h1: "Find out when a competitor ships a new feature, not months later",
    intro:
      "New features usually show up first on a changelog, a features page, or a homepage before they're announced widely. CompetitorSignal watches those pages directly, so a new feature launch reaches your team the same day it's published, not whenever someone happens to notice.",
    highlights: [
      { title: "Changelog and release-notes monitoring", body: "Purpose-built page types for /changelog, /updates, and /releases pages, alongside features and product pages." },
      { title: "Honest about uncertainty", body: "If a new feature's name isn't clearly stated in the page content, the system won't invent one — it reports what changed without fabricating specifics it can't verify." },
      { title: "Classified separately from copy edits", body: "A genuine new feature is classified and scored differently from a minor wording change, so it doesn't get lost in day-to-day content noise." },
      { title: "Why it matters, not just what shipped", body: "AI-generated context connects the new feature to your own product category where relevant, using hedged, non-speculative language." },
    ],
    faqs: [
      { q: "Does it work if a competitor doesn't have a public changelog?", a: "Yes — you can also monitor their features, product, or homepage pages, or add any custom URL where they tend to announce things." },
      { q: "Will it alert me for every tiny wording change?", a: "No — a minimum change threshold filters out noise like whitespace, timestamps, and copy tweaks that don't reflect a real feature or content change." },
      { q: "Can I mark a feature change as already-known and stop alerts on it?", a: "Yes — mark it reviewed or ignored, and it won't keep re-alerting unless the page changes again meaningfully." },
    ],
  },

  "saas-competitor-monitoring": {
    slug: "saas-competitor-monitoring",
    metaTitle: "SaaS Competitor Monitoring",
    metaDescription:
      "SaaS competitor monitoring built for founders tracking 3–20 competitors. CompetitorSignal watches pricing, features, and positioning so you don't have to check manually.",
    eyebrow: "SaaS competitor monitoring",
    h1: "Competitor monitoring built around how SaaS founders actually work",
    intro:
      "Most SaaS founders don't have a competitive intelligence team — they have five minutes between customer calls to glance at what competitors are doing. CompetitorSignal is built for that reality: automatic monitoring, a dashboard you understand in seconds, and alerts that only fire for changes that actually matter to a company your size.",
    highlights: [
      { title: "Sized for founder-led teams", body: "The Free plan (5 competitors, 20 pages) and Pro plan (50 competitors, 500 pages) map to what an early- or growth-stage SaaS company actually needs to track, not enterprise-scale competitive intelligence tooling." },
      { title: "Onboarding in minutes", body: "Add a competitor's homepage URL, and pricing/features/changelog/blog pages are auto-suggested for you to approve — no manual URL hunting." },
      { title: "Weekly digest for busy founders", body: "One email summarizing the week's meaningful changes, so you don't need to check the dashboard daily to stay current." },
      { title: "Impact scoring tuned by page type", body: "Pricing and homepage changes are weighted higher than blog posts by default, matching what typically matters most to a SaaS business." },
    ],
    faqs: [
      { q: "How long does setup take?", a: "A few minutes per competitor — enter the URL, approve the suggested pages, choose daily or weekly checks, and monitoring starts immediately." },
      { q: "Is this useful for a solo founder, or only larger teams?", a: "It's built with solo/small-team SaaS founders as the primary use case — the weekly digest and dashboard are designed to be genuinely useful without a dedicated person watching them." },
      { q: "What if I only care about pricing, not everything else?", a: "You can filter the change feed by type (pricing, feature, positioning, etc.) and set per-severity email preferences in Settings." },
    ],
  },

  "ai-competitor-monitoring": {
    slug: "ai-competitor-monitoring",
    metaTitle: "AI Competitor Monitoring",
    metaDescription:
      "AI competitor monitoring that explains why a change matters and what to do about it — with a deterministic, backend-owned impact score the AI can't arbitrarily inflate.",
    eyebrow: "AI competitor monitoring",
    h1: "AI competitor monitoring — with the scoring kept out of the AI's hands",
    intro:
      "AI is genuinely useful here for one thing: turning a diff into a plain-English explanation of what changed and why it might matter. CompetitorSignal uses it for exactly that, and nothing more — the actual 0–100 impact score that decides what's \"critical\" is computed deterministically by the backend, not left for a language model to decide, because that number needs to mean the same thing every time.",
    highlights: [
      { title: "AI for explanation, not for scoring", body: "Change type, diff magnitude, and page importance combine into a fixed formula for the impact score; the AI only supplies the human-readable summary and recommended action." },
      { title: "Every AI response is schema-validated", body: "Output is checked against a strict schema before it's ever shown to you — malformed or incomplete AI output falls back to a clearly-labeled generic message instead of guessing." },
      { title: "No invented facts", body: "The AI is instructed to use only what's present in the actual diff and page content, use hedged language (\"this may indicate...\") instead of asserting certainty about a competitor's strategy, and it's held to that by validation, not just a prompt." },
      { title: "Swappable AI provider", body: "Built with a provider abstraction (OpenAI, Anthropic, or a no-key mock mode) — you're not locked to one vendor." },
    ],
    faqs: [
      { q: "Can the AI hallucinate a fake price or feature?", a: "The classifier is given only the actual diff and page content as input and instructed never to invent facts; combined with the fact that structured data like prices comes from direct page extraction (not the AI), this is specifically designed against." },
      { q: "Does the AI decide which changes are 'critical'?", a: "No — importance bands (critical/high/medium/low) are derived from the backend's deterministic 0–100 score, not from the AI's own judgment." },
      { q: "What happens if the AI service is down or returns bad output?", a: "A safe, clearly-labeled fallback explanation is used instead, so a change still gets flagged and scored correctly — it just won't have a full AI-written explanation for that one instance." },
    ],
  },

  "competitor-change-tracker": {
    slug: "competitor-change-tracker",
    metaTitle: "Competitor Change Tracker",
    metaDescription:
      "Looking for a competitor change tracker? CompetitorSignal monitors competitor websites automatically and turns detected changes into scored, explained alerts.",
    eyebrow: "Competitor change tracker",
    h1: "A competitor change tracker that tells you what to do next",
    intro:
      "A change tracker that only tells you \"this page is different now\" leaves the hard part — figuring out if it matters — entirely up to you. CompetitorSignal is built around a simple idea: monitoring should end in a decision, not a diff. Every detected change is classified, scored, explained, and paired with a recommended action.",
    highlights: [
      { title: "Before/after diff, clearly shown", body: "Additions, removals, and modifications are highlighted directly — added text in green, removed in red — on the change detail page." },
      { title: "Meaningful changes only", body: "Cookie banners, tracking IDs, timestamps, and other dynamic noise are filtered out before a change is even considered for scoring, so you're not alerted on nothing." },
      { title: "Full change history per competitor", body: "A timeline of every meaningful change detected for a competitor, alongside pages monitored and change counts." },
      { title: "Alerts you control", body: "Choose which severities trigger email vs. stay in-app-only, per your own risk tolerance." },
    ],
    faqs: [
      { q: "How often are pages checked?", a: "Daily or weekly, per page, with your choice at setup — daily is the default." },
      { q: "Can I export the change history?", a: "Yes — CSV export with competitor, page, change type, importance, impact score, summary, and detection date." },
      { q: "What counts as a 'meaningful' change?", a: "One that clears both a minimum change-magnitude threshold and either a minimum changed-word count or an actual structured field (price, heading, CTA) changing — not just any byte-level HTML difference." },
    ],
  },
};

export const ALTERNATIVES_PAGES: Record<string, SeoPageContent> = {
  "visualping-alternatives": {
    slug: "visualping-alternatives",
    metaTitle: "Visualping Alternative for Competitor Monitoring",
    metaDescription:
      "Comparing Visualping alternatives for competitor monitoring? See how CompetitorSignal adds business context — classification, impact scoring, and recommended actions — on top of change detection.",
    eyebrow: "Visualping alternative",
    h1: "Considering a Visualping alternative built specifically for competitor tracking",
    intro:
      "General-purpose website change detectors are built to watch any page on the web for any kind of change. CompetitorSignal is built for one job — tracking competitors — which means it goes further than detecting that a page changed: it classifies the change, scores its business impact, and explains why it matters specifically in a competitive context.",
    highlights: [
      { title: "Competitor-specific data model", body: "Competitors, monitored pages, and change history are first-class concepts — not just a list of watched URLs — so you get a competitor-level view (pages monitored, change count, high-impact changes) automatically." },
      { title: "Business context, not just a diff", body: "Every meaningful change gets an AI-generated \"why it matters\" and \"recommended action,\" grounded in the actual diff — turning a detected change into something you can act on." },
      { title: "Deterministic impact scoring", body: "A 0–100 score, page-type-weighted (pricing and homepage weighted highest), computed the same way every time — not a black box." },
      { title: "Built-in noise filtering", body: "Cookie banners, tracking IDs, and other dynamic page noise are filtered before anything is even considered a candidate change." },
    ],
    faqs: [
      { q: "Can I use CompetitorSignal for general website monitoring, not just competitors?", a: "It's purpose-built for competitor tracking — competitors, monitored pages, and change classification are the core model — so it's most useful when what you're watching is a competitor's site specifically." },
      { q: "Does it support daily and weekly checks?", a: "Yes, per monitored page, with sensible defaults and jittered scheduling so checks don't all fire at once." },
      { q: "Is there a free plan to try it?", a: "Yes — 5 competitors and 20 monitored pages, no credit card required." },
    ],
  },

  "competely-alternatives": {
    slug: "competely-alternatives",
    metaTitle: "Competely Alternative for Competitive Intelligence",
    metaDescription:
      "Looking for a Competely alternative? CompetitorSignal offers self-serve competitor monitoring with AI-explained impact — built for SaaS founders and small teams, not just enterprise CI teams.",
    eyebrow: "Competely alternative",
    h1: "A self-serve alternative built for founders, not just enterprise CI teams",
    intro:
      "CompetitorSignal is built to be set up by one person in a few minutes — no onboarding call, no CI-analyst learning curve. Add a competitor's website, approve the auto-suggested pages, and monitoring starts immediately, with a dashboard designed to be understood in under 10 seconds.",
    highlights: [
      { title: "Self-serve from day one", body: "Sign up, create a workspace, add a competitor — the whole flow is designed to work without any setup assistance." },
      { title: "Transparent, published pricing", body: "Free and Pro tiers with clearly stated limits (competitors, pages), visible on the pricing page — no \"contact sales\" required to see what it costs." },
      { title: "Founder-sized plans", body: "5 competitors free, 50 on Pro — sized for a founder or small team tracking a focused competitive set, not a sprawling watch-list." },
      { title: "Weekly digest by default", body: "A summary email that only reports what actually happened that week — built to be useful without checking the dashboard daily." },
    ],
    faqs: [
      { q: "Do I need to talk to sales to get started?", a: "No — Free and Pro are both self-serve; only the custom Business tier is contact-sales." },
      { q: "How is pricing structured?", a: "By number of competitors and monitored pages tracked, not by seats — see the pricing page for exact tiers." },
      { q: "Can I cancel or downgrade any time?", a: "Yes — downgrading to Free takes effect immediately from Settings, with no cancellation flow to navigate." },
    ],
  },

  "klue-alternatives": {
    slug: "klue-alternatives",
    metaTitle: "Klue Alternative for Competitor Tracking",
    metaDescription:
      "Exploring Klue alternatives? CompetitorSignal focuses on automated competitor website monitoring with AI-explained impact — a lighter-weight option for teams that don't need a full competitive enablement platform.",
    eyebrow: "Klue alternative",
    h1: "A lighter-weight alternative focused specifically on website monitoring",
    intro:
      "Full competitive enablement platforms are built for sales-enablement workflows, battlecards, and cross-team collaboration at scale. CompetitorSignal is intentionally narrower: it focuses on one job — automatically monitoring competitor websites and explaining what changed — for teams that want that specific capability without adopting a larger platform.",
    highlights: [
      { title: "Narrow, deep focus", body: "Monitoring, diffing, classification, and impact scoring for competitor web pages — pricing, features, positioning, changelogs, blogs — done thoroughly rather than spread across many use cases." },
      { title: "Fast to adopt", body: "No platform rollout — one person can set up monitoring for a first competitor in a few minutes." },
      { title: "AI-generated recommended actions", body: "Each meaningful change comes with a suggested next step (e.g. \"review your pricing comparison page\"), grounded in the diff rather than generic advice." },
      { title: "Straightforward, published pricing", body: "Free and Pro tiers with stated limits, visible without a sales conversation." },
    ],
    faqs: [
      { q: "Does CompetitorSignal include battlecards or sales-enablement features?", a: "No — it's focused on monitoring and alerting, not sales-enablement content management." },
      { q: "Can multiple team members use the same workspace?", a: "Yes — organizations support member roles (owner, admin, member), with plans to expand team features further." },
      { q: "What page types can I monitor?", a: "Homepage, pricing, features, product, changelog, blog, or any custom URL you add." },
    ],
  },
};
