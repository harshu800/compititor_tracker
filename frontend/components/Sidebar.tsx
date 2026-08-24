"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { UserButton } from "@clerk/nextjs";
import clsx from "clsx";
import { useOrganization } from "@/hooks/useOrganization";
import { SITE_NAME } from "@/lib/seo";

const NAV_ITEMS = [
  { href: "/dashboard", label: "Overview" },
  { href: "/competitors", label: "Competitors" },
  { href: "/changes", label: "Changes" },
  { href: "/alerts", label: "Alerts" },
  { href: "/reports", label: "Reports" },
  { href: "/settings", label: "Settings" },
];

export function Sidebar() {
  const pathname = usePathname();
  const { organizationName } = useOrganization();

  return (
    <aside className="w-60 shrink-0 border-r border-gray-200 bg-white flex flex-col h-screen sticky top-0">
      <div className="px-5 py-5 border-b border-gray-100">
        <div className="font-semibold text-gray-900">{SITE_NAME}</div>
        {organizationName && (
          <div className="text-xs text-gray-500 mt-0.5 truncate">{organizationName}</div>
        )}
      </div>
      <nav className="flex-1 px-3 py-4 space-y-1">
        {NAV_ITEMS.map((item) => {
          const active = pathname?.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={clsx(
                "block rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                active ? "bg-gray-900 text-white" : "text-gray-600 hover:bg-gray-100"
              )}
            >
              {item.label}
            </Link>
          );
        })}
      </nav>
      <div className="px-5 py-4 border-t border-gray-100 flex items-center gap-2">
        <UserButton afterSignOutUrl="/sign-in" />
        <span className="text-xs text-gray-500">Account</span>
      </div>
    </aside>
  );
}
