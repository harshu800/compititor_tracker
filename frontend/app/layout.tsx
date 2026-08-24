import type { Metadata } from "next";
import "./globals.css";
import { Providers } from "./providers";
import { SITE_NAME, SITE_URL, DEFAULT_DESCRIPTION, TARGET_KEYWORDS } from "@/lib/seo";

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: {
    default: `${SITE_NAME} — Competitor Monitoring & Intelligence Software`,
    template: `%s | ${SITE_NAME}`,
  },
  description: DEFAULT_DESCRIPTION,
  keywords: TARGET_KEYWORDS,
  openGraph: {
    siteName: SITE_NAME,
    title: `${SITE_NAME} — Competitor Monitoring & Intelligence Software`,
    description: DEFAULT_DESCRIPTION,
    type: "website",
    url: SITE_URL,
  },
  twitter: {
    card: "summary_large_image",
    title: `${SITE_NAME} — Competitor Monitoring & Intelligence Software`,
    description: DEFAULT_DESCRIPTION,
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="antialiased">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
