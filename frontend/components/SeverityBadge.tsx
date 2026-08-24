import { Importance } from "@/types";
import clsx from "clsx";

const CONFIG: Record<Importance, { label: string; dot: string; text: string; bg: string; emoji: string }> = {
  critical: { label: "Critical", dot: "bg-red-600", text: "text-red-800", bg: "bg-red-50", emoji: "🔴" },
  high: { label: "High", dot: "bg-orange-500", text: "text-orange-800", bg: "bg-orange-50", emoji: "🟠" },
  medium: { label: "Medium", dot: "bg-yellow-500", text: "text-yellow-800", bg: "bg-yellow-50", emoji: "🟡" },
  low: { label: "Low", dot: "bg-gray-400", text: "text-gray-700", bg: "bg-gray-50", emoji: "⚪" },
};

/** Severity is ALWAYS shown with color + text label together —
 * never color alone (accessibility requirement, spec section 42). */
export function SeverityBadge({ importance }: { importance: Importance }) {
  const cfg = CONFIG[importance];
  return (
    <span className={clsx("inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium", cfg.bg, cfg.text)}>
      <span className={clsx("h-1.5 w-1.5 rounded-full", cfg.dot)} aria-hidden />
      {cfg.label} Impact
    </span>
  );
}

export function SeverityEmoji({ importance }: { importance: Importance }) {
  return <span aria-hidden>{CONFIG[importance].emoji}</span>;
}
