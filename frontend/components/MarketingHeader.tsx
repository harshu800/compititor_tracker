import Link from "next/link";
import { SignedIn, SignedOut, UserButton } from "@clerk/nextjs";
import { SITE_NAME } from "@/lib/seo";

export function MarketingHeader() {
  return (
    <header className="border-b border-gray-100">
      <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
        <Link href="/" className="font-semibold text-gray-900">
          {SITE_NAME}
        </Link>
        <nav className="flex items-center gap-6 text-sm">
          <Link href="/pricing" className="text-gray-600 hover:text-gray-900">Pricing</Link>
          <SignedOut>
            <Link href="/sign-in" className="text-gray-600 hover:text-gray-900">Sign in</Link>
            <Link href="/sign-up" className="bg-gray-900 text-white rounded-lg px-4 py-2 font-medium hover:bg-gray-800">
              Get started
            </Link>
          </SignedOut>
          <SignedIn>
            <Link href="/dashboard" className="bg-gray-900 text-white rounded-lg px-4 py-2 font-medium hover:bg-gray-800">
              Go to dashboard
            </Link>
            <UserButton afterSignOutUrl="/" />
          </SignedIn>
        </nav>
      </div>
    </header>
  );
}
