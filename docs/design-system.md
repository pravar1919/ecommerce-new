# Design System

Theme: **Direction B, "Quiet Heirloom" (approved 2026-11-17)**, theme key `heirloom` (see `brand-identity.md`). Every value below is a token. Components consume **semantic** tokens only, so a different approved direction changes tokens, not components.

Implementation: Tailwind CSS v4 `@theme` tokens in `frontend/src/styles/tokens.css`, theme overrides in `frontend/src/styles/themes/*.css` selected by `data-theme` on `<html>`, and primitives in `frontend/src/components/ui/` (shadcn/ui-based and restyled).

## 1. Principles

1. **The garment is the loudest thing on the page.** UI recedes: no decorative gradients, no glass, no drop shadows on product imagery.
2. **Editorial, not template.** Use an asymmetric grid, oversized display type, generous negative space and full-bleed photography. Never repeat the same three-up card row on a page.
3. **Craft in the details.** Hairline rules, tabular numerals for prices, small-caps labels, the "thread" line motif.
4. **Motion has a job.** It reveals, orients or gives feedback. Never motion for its own sake, and always respect `prefers-reduced-motion`.
5. **Mobile is the primary canvas.** Over 75% of Indian fashion traffic is mobile. Design at 375px first, then compose up.

## 2. Colour

### Palette (primitive tokens)
| Token | Hex | Use |
|---|---|---|
| `--ivory-50` | `#FCFAF6` | Raised surfaces (sheets, menus) |
| `--ivory-100` | `#F8F4EC` | **Default page background** |
| `--sand-200` | `#E9E1D3` | Dividers, skeletons, subtle fills |
| `--stone-500` | `#6B655C` | Muted text (on ivory only) |
| `--charcoal-900` | `#242323` | Primary text, dark surfaces |
| `--burgundy-700` | `#651E35` | Brand primary, primary buttons |
| `--royal-700` | `#263E80` | Campaign accent, links in campaign context |
| `--emerald-800` | `#174B3B` | Campaign accent, success states |
| `--marigold-400` | `#E5A52B` | Celebration highlight, badges on dark |
| `--gold-300` | `#C5A46D` | Premium details: rules, icons, numerals on dark |
| `--error-700` | `#9B2C2C` | Error text/borders |

### Semantic tokens
| Token | Light value |
|---|---|
| `--color-bg` | ivory-100 |
| `--color-surface` | ivory-50 |
| `--color-surface-inverse` | charcoal-900 |
| `--color-text` | charcoal-900 |
| `--color-text-muted` | stone-500 |
| `--color-text-inverse` | ivory-100 |
| `--color-border` | sand-200 |
| `--color-border-strong` | charcoal-900 |
| `--color-primary` / `-fg` | burgundy-700 / ivory-100 |
| `--color-accent` | per campaign (CMS `accent`: emerald / royal / burgundy) |
| `--color-ornament` | gold-300 |
| `--color-highlight` | marigold-400 |
| `--color-focus` | royal-700 (2px outline + 2px offset) |

The storefront is light-first by intent. Dark sections are a **composition** tool (inverse surfaces for campaign bands and the footer), not an OS dark mode. The Next.js admin supports system dark mode.

### Contrast rules (measured, WCAG 2.2)
| Foreground → background | Ratio | Allowed |
|---|---|---|
| Charcoal on Ivory | 14.3 | All text |
| Burgundy on Ivory | 10.7 | All text |
| Royal Blue on Ivory | 9.2 | All text |
| Emerald on Ivory | 9.1 | All text |
| Stone on Ivory | 5.3 | Body/muted text (AA). **Not on Sand** (4.4). |
| Ivory on Burgundy | 10.7 | All text |
| Marigold on Charcoal | 7.3 | All text |
| Gold on Charcoal | 6.6 | All text |
| Gold on Burgundy | 5.0 | Text ≥ 14px |
| **Marigold or Gold on Ivory** | **2.0 / 2.1** | **Never for text or meaningful icons.** Decorative rules only. |

## 3. Typography

| Role | Family | Fallback |
|---|---|---|
| Display | **Bodoni Moda** (variable, optical size axis) | `"Didot", "Bodoni 72", Georgia, serif` |
| Body / UI | **Hanken Grotesk** (variable) | `system-ui, sans-serif` |
| Devanagari accent | **Tiro Devanagari Hindi** | `"Noto Serif Devanagari", serif` |

Fonts load through `next/font/google` (self-hosted at build, `display: swap`, subset `latin`, with `latin-ext` where needed). Devanagari loads only on pages that use it.

### Fluid type scale (`clamp`, 375 → 1440px)
| Token | Size | Line height | Use |
|---|---|---|---|
| `display-2xl` | 56 → 168px | 0.92 | Hero campaign headline |
| `display-xl` | 44 → 112px | 0.95 | Section openers |
| `display-lg` | 34 → 64px | 1.0 | Category titles |
| `display-md` | 28 → 40px | 1.1 | Editorial subheads |
| `heading` | 20 → 24px | 1.25 | Card groups, PDP title (sans 500) |
| `body-lg` | 17 → 19px | 1.6 | Editorial paragraphs |
| `body` | 15 → 16px | 1.55 | Default |
| `label` | 12 → 13px, +0.12em tracking, uppercase | 1.3 | Nav, eyebrows, buttons |
| `caption` | 12px | 1.4 | Meta, legal |

Prices use `font-variant-numeric: tabular-nums lining-nums`. INR is formatted with `Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 })`, which gives Indian digit grouping (₹1,24,500).

## 4. Space, grid, shape

- **Spacing scale (4px base):** 4, 8, 12, 16, 24, 32, 48, 64, 96, 128, 192. Section rhythm is 96 (mobile 64) to 192 (desktop).
- **Grid:** 4 columns (mobile, 16px gutters, 16px margins) → 8 (tablet) → 12 (desktop, 24px gutters, max content 1440px, full-bleed allowed).
- **Editorial layouts:** asymmetric spans such as 7/5, 5/7, 8/4 and offset 1/6/1/4, plus "overlap" compositions where type crosses an image edge by one column.
- **Radius:** `0` by default. `2px` for inputs and buttons. `999px` only for colour swatches and pills. No large rounded cards.
- **Borders:** 1px hairlines in `--color-border`. Emphasis uses `--color-border-strong`.
- **Elevation:** none on content. Overlays (drawer, modal, quick view) use a single soft shadow `0 24px 64px -24px rgb(36 35 35 / .25)` plus a scrim.

## 5. Imagery

| Context | Ratio | Notes |
|---|---|---|
| Product card / PDP gallery | **4:5** | Consistent across catalogue. Neutral background. Shot standard enforced at upload (min 2000×2500). |
| PDP detail / fabric macro | 1:1 | |
| Campaign hero | 21:9 desktop / 4:5 mobile | Art-directed: separate mobile crop or focal point set in CMS |
| Editorial pairs | 3:4 + 2:3 | Asymmetric |
| Instagram gallery | 1:1 | |

- `next/image` handles everything, with explicit `sizes`, AVIF/WebP and a blur placeholder from a stored `blurhash`/LQIP. Only the hero (LCP) gets `priority`. Everything below the fold is lazy.
- Every media asset stores `alt_text` (required), a `focal_point` (x,y) for responsive cropping, `credit` and `usage_rights`.
- **Product imagery is only real product photography from the catalogue.** Campaign and editorial assets live in the CMS media library, flagged `is_product_photo=false`, and are never attached to products. Development placeholders are labelled as such.

## 6. Motion

### Tokens
| Token | Value |
|---|---|
| `--ease-out-expo` | `cubic-bezier(0.16, 1, 0.3, 1)` (reveals) |
| `--ease-in-out-quart` | `cubic-bezier(0.76, 0, 0.24, 1)` (page/curtain transitions) |
| `--ease-standard` | `cubic-bezier(0.2, 0, 0, 1)` (UI) |
| `--dur-fast` | 150ms (hover, press) |
| `--dur-base` | 250ms (menus, toggles) |
| `--dur-slow` | 600ms (reveals) |
| `--dur-cinematic` | 1000–1400ms (hero only) |
| Stagger | 60ms per item, max 8 items |

### Rules
- Animate `transform`, `opacity` and `clip-path` only. Never layout properties.
- Scroll effects use `IntersectionObserver` / Framer Motion `whileInView` with `once: true`. Parallax is capped at ±8% translate and disabled on touch-coarse devices if INP suffers.
- **Reduced motion:** a global `MotionConfig reducedMotion="user"` plus a `useReducedMotion` guard in every React Bits wrapper. Reveals become instant opacity, parallax and marquees stop, video heroes show a poster frame.
- Motion must never delay interactivity. Content is in the DOM and readable before any animation runs (SSR first, animate on hydration). No text is hidden behind a JS-only reveal for crawlers.
- Budget: motion libraries load client-side only in the components that need them (`dynamic(() => import(...), { ssr: false })` for WebGL/GSAP pieces).

### React Bits selection
Installed per component through the shadcn registry: `npx shadcn@latest add @react-bits/<Name>-TS-TW`. Each one is wrapped in `src/components/motion/` so the vendored source stays untouched and the reduced-motion and SSR fallbacks live in one place. Dependencies are confirmed at install time and recorded in `PROJECT_STATUS.md`.

| Component | Where | Why |
|---|---|---|
| **Split Text** | Hero headline, section openers | Line/word reveal of display type, which carries the campaign "moment" |
| **Blur Text** | Supporting lines, testimonials | Softer secondary reveal |
| **Scroll Reveal** | Craftsmanship storytelling paragraph | Ties reading to scroll |
| **Fade Content / Animated Content** | Section and product-grid entrances | Light, staggered entrances |
| **Masonry** | Instagram / lookbook gallery | Mixed-ratio editorial grid |
| **Flowing Menu** | Desktop mega-menu category list (optional) | Image-reveal hover on category names |
| **Image Trail** (evaluate) | Editorial campaign band only | One "signature" interactive moment. Desktop only. |
| **Noise** | Very low-opacity film grain on campaign bands | Photographic texture, not decoration |
| **Count Up** | Craft stats ("120 hours of hand embroidery") | Storytelling numerals |
| **Magnet** | Primary hero CTA only | Subtle tactile feedback, pointer:fine only |

Rejected for this brand: Silk, Aurora, Iridescence and similar gradient/WebGL backgrounds (against the "no excessive gradients" rule and the photography-first principle), Glass Surface / Fluid Glass (glassmorphism), Splash/Blob cursors (gimmicky, and an accessibility cost).

### Signature interactions (original)
1. **Thread line.** A 1px line that "stitches" in under headings and the active nav item (SVG `stroke-dashoffset`).
2. **Curtain transition.** A burgundy panel wipe (clip-path) between campaign slides and on the route change into a collection. 600ms, skipped on reduced motion.
3. **Fabric hover.** Product cards cross-reveal the second image with a diagonal clip-path, like turning a fold of fabric.
4. **Zoom loupe.** On PDP desktop a pointer-tracked loupe on high-res imagery. On mobile, pinch-zoom in a full-screen gallery.

## 7. Component inventory

**Primitives (shadcn/ui-based):** Button (primary / secondary / ghost / link, sizes sm/md/lg, loading state), IconButton, Input, Textarea, Select, Checkbox, Radio, Switch, Label, FormField (label, hint, error, `aria-describedby`), Dialog, Sheet/Drawer, Popover, Tooltip, Tabs, Accordion, Toast (sonner), Skeleton, Badge, Separator, Breadcrumb, Pagination.

**Commerce:** Price (MRP strike-through, sale, "incl. of all taxes"), ProductCard, ProductGrid, ColourSwatch, SizeSelector (unavailable state, "only 2 left"), QuantityStepper, AddToBagButton, WishlistToggle, SizeGuideDialog (garment chart and how-to-measure tabs), MeasurementForm (MTM), PincodeChecker, FilterPanel (mobile sheet / desktop rail), SortMenu, SearchCommand (suggestions), QuickViewDialog, Gallery + Zoom, CartDrawer, OrderSummary, CouponField, AddressForm (Indian state select, pincode autofill), CheckoutStepper, OrderTimeline.

**Editorial (CMS-driven):** AnnouncementBar, SiteHeader / MegaMenu / MobileNav, CampaignHero, CategoryMosaic, CollectionFeature, ProductRail, OccasionTiles, EditorialSplit, CraftStory, Testimonials, InstagramGallery, NewsletterSignup, SiteFooter.

Each CMS block maps 1:1 to a `cms.ContentBlock.type` with a typed config schema (see `api-contracts.md`).

## 8. Accessibility (WCAG 2.2 AA target)

- Semantic landmarks, one `h1` per page, skip link.
- All interactive elements are keyboard reachable with a visible `--color-focus` ring. Focus is trapped and restored in dialogs and drawers (Radix).
- Hit targets ≥ 44×44px on touch.
- Colour is never the only signal: swatches carry names, and sold-out sizes show strike-through plus "Sold out" text.
- Form errors are announced via `aria-live`, with inline messages linked to fields.
- Alt text is required at upload and decorative images use `alt=""`.
- Video has captions/poster, autoplays only muted, and has a pause control.

## 9. Performance budgets (storefront, mobile, 4G)

| Metric | Budget |
|---|---|
| LCP | ≤ 2.5s (target 1.8s) |
| INP | ≤ 200ms |
| CLS | ≤ 0.05 |
| JS (first load, route) | ≤ 170KB gzip on home/PLP/PDP |
| Hero image | ≤ 180KB AVIF at 4:5 mobile |
