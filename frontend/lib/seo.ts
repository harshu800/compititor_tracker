/**
 * Shared SEO constants. Every page's metadata (root layout default, marketing
 * pages, and the keyword landing pages under app/(seo)/) pulls from here so
 * the brand name, base description, and keyword set stay in one place
 * instead of drifting across a dozen separate page.tsx files.
 */

export const SITE_NAME = "CompetitorSignal";

export const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL || "https://competitorsignal.com";

export const DEFAULT_DESCRIPTION =
  "CompetitorSignal monitors your competitors' pricing, features, and positioning across their public web pages, and turns every meaningful change into a scored, explained, actionable alert.";

// Primary keyword set this app is built to rank for — used across page
// metadata `keywords` fields and woven into landing-page copy. Modern search
// engines largely ignore the <meta keywords> tag itself, but the list still
// drives which pages exist and what their titles/descriptions/headings
// target, which is where the actual ranking signal comes from.
export const TARGET_KEYWORDS = [
  "competitor monitoring software",
  "competitor intelligence software",
  "competitor tracking software",
  "competitor analysis tool",
  "competitor website monitoring",
  "competitor price tracking",
  "competitor pricing monitoring",
  "competitor feature tracking",
  "competitor change tracker",
  "SaaS competitor monitoring",
  "AI competitor monitoring",
];
