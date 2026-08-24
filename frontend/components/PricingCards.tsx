import Link from "next/link";
import clsx from "clsx";
import { SignedIn, SignedOut } from "@clerk/nextjs";

export interface PricingTier {
  name: string;
  price: string;
  period?: string;
  description: string;
  features: string[];
  cta: { label: string; href: string };
  highlighted?: boolean;
}

export const PRICING_TIERS: PricingTier[] = [
  {
    name: "Free",
    price: "$0",
    period: "/month",
    description: "Try it out on a handful of competitors.",
    features: [
      "5 competitors",
      "20 monitored pages",
      "Daily checks",
      "In-app alerts",
      "7-day change history",
    ],
    cta: { label: "Start free", href: "/sign-up" },
  },
  {
    name: "Pro",
    price: "$29",
    period: "/month",
    description: "For founders and teams actively tracking the market.",
    features: [
      "50 competitors",
      "500 monitored pages",
      "Daily checks",
      "Email + in-app alerts",
      "Weekly digest email",
      "CSV export",
      "Full change history",
    ],
    cta: { label: "Start free trial", href: "/sign-up" },
    highlighted: true,
  },
  {
    name: "Business",
    price: "Custom",
    description: "For agencies and competitive intelligence teams.",
    features: [
      "Unlimited competitors",
      "Unlimited monitored pages",
      "Daily checks",
      "Email + in-app alerts",
      "Weekly digest email",
      "CSV export",
      "Priority support",
    ],
    cta: { label: "Contact sales", href: "mailto:sales@example.com" },
  },
];

function ctaButtonClass(highlighted?: boolean) {
  return clsx(
    "text-center rounded-lg px-4 py-2.5 text-sm font-medium transition-colors",
    highlighted ? "bg-gray-900 text-white hover:bg-gray-800" : "border border-gray-300 text-gray-900 hover:bg-gray-50"
  );
}

function TierCta({ tier }: { tier: PricingTier }) {
  // Business is always contact-sales, signed in or not — no self-serve
  // checkout for it (see backend billing_service.SUPPORTED_UPGRADE_PLANS).
  if (tier.name === "Business") {
    return (
      <Link href={tier.cta.href} className={ctaButtonClass(tier.highlighted)}>
        {tier.cta.label}
      </Link>
    );
  }

  return (
    <>
      <SignedOut>
        <Link href={tier.cta.href} className={ctaButtonClass(tier.highlighted)}>
          {tier.cta.label}
        </Link>
      </SignedOut>
      <SignedIn>
        {tier.name === "Pro" ? (
          <Link href="/settings" className={ctaButtonClass(tier.highlighted)}>
            Upgrade in Settings
          </Link>
        ) : (
          <Link href="/dashboard" className={ctaButtonClass(tier.highlighted)}>
            Go to dashboard
          </Link>
        )}
      </SignedIn>
    </>
  );
}

export function PricingCards() {
  return (
    <div className="grid md:grid-cols-3 gap-6 max-w-5xl mx-auto">
      {PRICING_TIERS.map((tier) => (
        <div
          key={tier.name}
          className={clsx(
            "rounded-2xl border p-6 flex flex-col",
            tier.highlighted ? "border-gray-900 shadow-sm ring-1 ring-gray-900" : "border-gray-200"
          )}
        >
          {tier.highlighted && (
            <span className="self-start bg-gray-900 text-white text-xs font-medium px-2.5 py-1 rounded-full mb-3">
              Most popular
            </span>
          )}
          <h3 className="text-lg font-semibold text-gray-900">{tier.name}</h3>
          <p className="text-sm text-gray-500 mt-1 mb-4">{tier.description}</p>
          <div className="mb-6">
            <span className="text-3xl font-semibold text-gray-900">{tier.price}</span>
            {tier.period && <span className="text-gray-500 text-sm">{tier.period}</span>}
          </div>
          <ul className="space-y-2.5 mb-6 flex-1">
            {tier.features.map((f) => (
              <li key={f} className="flex items-start gap-2 text-sm text-gray-700">
                <span className="text-gray-400 mt-0.5" aria-hidden>✓</span>
                {f}
              </li>
            ))}
          </ul>
          <TierCta tier={tier} />
        </div>
      ))}
    </div>
  );
}
