import { ChangeType } from "@/types";

const LABELS: Record<ChangeType, string> = {
  pricing: "Pricing", feature: "Feature", positioning: "Positioning", product: "Product",
  offer: "Offer", cta: "CTA", content: "Content", messaging: "Messaging",
  legal: "Legal", design: "Design", other: "Other",
};

export function ChangeTypeBadge({ type }: { type: ChangeType }) {
  return (
    <span className="inline-flex items-center rounded-md bg-gray-100 px-2 py-1 text-xs font-medium text-gray-700">
      {LABELS[type] ?? type}
    </span>
  );
}
