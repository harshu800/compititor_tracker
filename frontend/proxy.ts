import { clerkMiddleware, createRouteMatcher } from "@clerk/nextjs/server";
import { SEO_PAGES, ALTERNATIVES_PAGES } from "@/lib/seoContent";

// Public marketing + SEO pages don't require auth. Everything else —
// dashboard, competitors, changes, etc. — stays behind Clerk
// (auth.protect() below). SEO page slugs are pulled directly from
// lib/seoContent.ts rather than hardcoded here, so a new SEO page added
// to that file is automatically public — forgetting to list it here
// separately previously caused every SEO landing page to 307-redirect to
// sign-in instead of being visible to visitors or crawlable by search
// engines, which defeats the entire point of an SEO page.
const seoSlugs = [...Object.keys(SEO_PAGES), ...Object.keys(ALTERNATIVES_PAGES)];

const isPublicRoute = createRouteMatcher([
  "/",
  "/pricing",
  "/bot",
  "/sign-in(.*)",
  "/sign-up(.*)",
  ...seoSlugs.map((slug) => `/${slug}`),
]);

export default clerkMiddleware(async (auth, req) => {
  if (!isPublicRoute(req)) {
    await auth.protect();
  }
});

export const config = {
  matcher: ["/((?!_next|.*\\..*).*)", "/", "/(api|trpc)(.*)"],
};
