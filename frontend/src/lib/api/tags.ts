/** Cache tags. Mirrored by Django (apps/cms/services.py) which calls /api/revalidate on publish. */
export const TAGS = {
  siteSettings: "cms:site-settings",
  navigation: "cms:navigation",
  page: (slug: string) => `cms:page:${slug}`,
} as const;
