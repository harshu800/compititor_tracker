export function timeAgo(iso: string): string {
  const date = new Date(iso);
  const seconds = Math.floor((Date.now() - date.getTime()) / 1000);
  const units: [number, string][] = [
    [60, "second"], [60, "minute"], [24, "hour"], [7, "day"], [4.345, "week"], [12, "month"], [Infinity, "year"],
  ];
  let value = seconds;
  for (const [div, unit] of units) {
    if (value < div) return `${Math.max(1, Math.floor(value))} ${unit}${Math.floor(value) === 1 ? "" : "s"} ago`;
    value /= div;
  }
  return date.toLocaleDateString();
}

export function formatDate(iso: string): string {
  return new Date(iso).toLocaleString(undefined, {
    year: "numeric", month: "short", day: "numeric", hour: "2-digit", minute: "2-digit",
  });
}
