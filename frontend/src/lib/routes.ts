/** Storefront URL scheme (catalogue pages arrive in Phase 4; links are stable now). */
export const routes = {
  home: () => "/",
  category: (path: string) => `/${path.replace(/^\/+|\/+$/g, "")}`,
  collection: (slug: string) => `/collections/${slug}`,
  occasion: (slug: string) => `/search?occasion=${encodeURIComponent(slug)}`,
  product: (slug: string) => `/products/${slug}`,
  search: () => "/search",
  account: () => "/account",
  wishlist: () => "/account/wishlist",
  bag: () => "/cart",
} as const;

export function isExternal(href: string): boolean {
  return /^https?:\/\//.test(href);
}
