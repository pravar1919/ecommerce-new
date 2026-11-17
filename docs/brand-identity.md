# Brand Identity — Discovery

> Status: **Direction B, "Quiet Heirloom", APPROVED (2026-11-17).** Brand **name** not yet chosen, so no name is hardcoded anywhere in the codebase.
> All brand-facing strings resolve from configuration (see [Configurable brand metadata](#configurable-brand-metadata)).
> Until a direction is approved the platform runs under the neutral **development identity** described at the end of this file.

## Brief recap

A premium Indian menswear house for grooms, wedding guests and festive shoppers. It joins Indian craft (zardozi, aari, resham, chikankari, bandhgala tailoring, handloom silks) with the restraint and editorial confidence of international fashion. The shared palette from the brief (Ivory, Burgundy, Royal Blue, Emerald, Marigold, Champagne Gold, Charcoal) sits underneath all three directions. Each direction weights it differently.

All three directions are built on the same token system (`docs/design-system.md`). Switching between them means changing theme tokens and brand metadata, not rewriting components.

---

## Direction A — "Darbar Modern"

**Personality:** Regal, ceremonious, assured. Heritage without nostalgia. It speaks in the voice of a master tailor whose family has dressed grooms for generations, and who now works with a modern atelier.

**Suggested names** (unverified, see [Naming due diligence](#naming-due-diligence)):
- **Vastrakar**: "maker of garments"
- **Kulvansh**: "lineage"
- **Raajsutra**: "the royal thread"

**Logo concept:** A monogram set inside a *jharokha* (arched Rajput window) outline, drawn as one continuous gold hairline. The wordmark is in spaced capitals beneath it. The arch doubles as a frame device in the UI for collection banners and the size-guide modal. Brand assets use foil-gold on burgundy; digital uses Champagne Gold `#C5A46D`.

**Colour palette:**
| Role | Colour | Hex |
|---|---|---|
| Primary surface | Ivory | `#F8F4EC` |
| Brand primary | Burgundy | `#651E35` |
| Ornament / accent | Champagne Gold | `#C5A46D` |
| Text | Charcoal | `#242323` |
| Supporting | Emerald | `#174B3B` |
| Sparing highlight | Marigold | `#E5A52B` |

**Typography:** *Cormorant Garamond* (display, 500–600, generous tracking in caps) with *Manrope* (body/UI). Accent lines in *Tiro Devanagari Hindi* for occasional bilingual flourishes (e.g. "शुभ विवाह").

**Photography direction:** Warm tungsten and late-afternoon light. Havelis, courtyards, carved stone and brass, with candlelit interiors for reception wear. Mostly full-length portraits at a slight low angle so the groom reads as heroic. Macro craft studies (zardozi, buttons, safa folds) printed as full-bleed interstitials.

**Target customer:** Grooms aged 28–40 and their families, planning destination and heritage-venue weddings. They value lineage, craftsmanship and the "once-in-a-lifetime" outfit, and they usually buy in high-consideration sessions with family on WhatsApp.

**Visual identity examples:**
- Homepage hero: a full-bleed portrait in a haveli doorway, with the headline in Cormorant caps set inside a gold hairline arch.
- Product card: ivory ground, a 4:5 image and a thin gold rule between name and price. On hover the card cross-fades to an embroidery macro.
- Packaging: a burgundy garment box with a foil jharokha monogram and an ivory muslin garment bag.
- Email header: a centred monogram with a single gold rule and no imagery above the fold.

**Risk:** Easy to tip into "wedding-card kitsch" if ornament is overused. It needs strict rules on how much ornament is allowed.

---

## Direction B — "Quiet Heirloom" (recommended)

**Personality:** Contemporary, editorial, quietly confident. Indian craft presented the way a Paris or Milan house presents its atelier, with craft as the luxury rather than the decoration. Restrained layouts let the clothing do the talking.

**Suggested names** (unverified):
- **Saanjh**: "dusk", the hour of the baraat and the reception
- **Anvay**: "connection, lineage"
- **Varan**: from *varmala*, the garland exchange

**Logo concept:** A high-contrast didone wordmark in caps, with a single "thread" stroke (*sui-dhaga*) crossing through the counter of one letter. The stroke appears again as a 1px animated underline in navigation and as the loading indicator. The secondary mark is a two-letter monogram for woven labels, buttons and favicon.

**Colour palette:**
| Role | Colour | Hex |
|---|---|---|
| Primary surface | Ivory | `#F8F4EC` |
| Text / dark surface | Charcoal | `#242323` |
| Brand primary | Burgundy | `#651E35` |
| Campaign accent 1 | Emerald | `#174B3B` |
| Campaign accent 2 | Royal Blue | `#263E80` |
| Detail / premium cues | Champagne Gold | `#C5A46D` |
| Celebration highlight | Marigold | `#E5A52B` |

Mostly ivory and charcoal, with burgundy for brand moments. Emerald and Royal Blue belong to campaigns: each campaign "owns" one accent, and the CMS sets it per campaign. Gold and marigold appear only as small details on dark grounds (see the contrast rules in the design system).

**Typography:** *Bodoni Moda* (display, optical sizes, used large: 64–180px) with *Hanken Grotesk* (body/UI). *Tiro Devanagari Hindi* for rare bilingual accents.

**Photography direction:** Editorial, art-directed and cinematic. Muted architectural backdrops (lime plaster, terrazzo, stepwells, modernist Chandigarh concrete) set against rich garments, so the garment is always the most saturated thing in the frame. Asymmetric crops, negative space and environmental portraits mixed with flat-lay fabric studies. Natural light, controlled shadows, no heavy grading. A 4:5 product standard and 3:2 / 21:9 campaign formats.

**Target customer:** Urban grooms and wedding guests aged 26–38 in metros and the NRI diaspora. They shop for themselves, follow international fashion and want Indian occasion wear that doesn't look like costume. Mobile-first, research-heavy, willing to pay for fit and fabric.

**Visual identity examples:**
- Homepage hero: a split-screen campaign. A tight crop of a sherwani collar sits on the left and the full-length groom on the right. "THE ART OF BEING THE GROOM" is set in Bodoni at 160px and reveals line by line. The thread line draws in underneath.
- Product card: zero radius, a 4:5 image with no frame and the name in small caps sans. Price sits on a second line in tabular numerals. Hover reveals a second image via a clip-path wipe.
- Category page: an editorial header with an asymmetric 7/5 image pair and a short paragraph of craft copy before the grid.
- Packaging: a charcoal box, an ivory tissue-wrapped garment and a burgundy thread tie with a card that names the karigar (artisan).

**Why recommended:** It fits the brief's "Indian craftsmanship + contemporary international fashion" most closely. It ages well and sets this brand apart from the ornate competitive field. It can also carry Directions A and C as *campaigns* (a heritage wedding edit, a festive edit) without the brand breaking.

---

## Direction C — "Baraat Electric"

**Personality:** Joyful, bold, colour-forward and social. The energy of the baraat, the sangeet dance floor and the haldi morning. Confident young menswear that is made to be photographed.

**Suggested names** (unverified):
- **Gendaa**: "marigold"
- **Mehfil House**: "gathering"
- **Baraati Club**

**Logo concept:** A heavy serif wordmark with a roundel monogram built from a stylised marigold (concentric petals that also read as a *chakra*). The roundel spins on interaction (motion respects reduced-motion). It stickers well on social content.

**Colour palette:**
| Role | Colour | Hex |
|---|---|---|
| Brand primary | Marigold | `#E5A52B` (on dark only for text) |
| Primary dark | Royal Blue | `#263E80` |
| Surface | Ivory | `#F8F4EC` |
| Supporting | Burgundy | `#651E35` |
| Supporting | Emerald | `#174B3B` |
| Text | Charcoal | `#242323` |

**Typography:** *Gloock* (display) with *Instrument Sans* (body/UI).

**Photography direction:** Bright flash and daylight, with movement, groups of friends, dancing and confetti. Saturated colour-blocked sets and street-style shots at the baraat. More video and short-form content, often vertical 9:16.

**Target customer:** Wedding guests and festive shoppers aged 21–32 buying multiple looks per season for sangeet, mehendi, cocktail and Diwali. Instagram-led discovery and price-aware. Wants trend-led indo-western pieces.

**Visual identity examples:**
- Homepage hero: a looping vertical video mosaic with oversized headline type over it.
- Product card: a colour-blocked background behind a cut-out product with a playful "Sangeet-ready" badge.
- Packaging: a marigold mailer box with a royal blue interior print.

**Risk:** It sits closer to the mass-market festive retailers and dilutes "premium". The groom segment (the highest AOV) may find it too casual.

---

## Comparison

| | A · Darbar Modern | B · Quiet Heirloom | C · Baraat Electric |
|---|---|---|---|
| Premium signal | High | **Highest** | Medium |
| Differentiation from competitors | Medium | **High** | Medium |
| Groom segment fit | **High** | High | Low |
| Guest / festive fit | Medium | High | **High** |
| Longevity | High | **High** | Medium |
| Photography cost | High (venues) | Medium | Medium |
| Can host the other directions as campaigns | Partially | **Yes** | No |

## Naming due diligence

None of the suggested names has been checked. Before adoption:
1. Search the IP India trademark registry (Class 25 clothing and Class 35 retail) for conflicts.
2. Check `.com` / `.in` domains and Instagram / YouTube handles.
3. Run a native-speaker connotation check across Hindi, Punjabi, Gujarati, Marathi, Bengali, Tamil and Telugu.
4. Get legal clearance before the name appears in any production config.

## Configurable brand metadata

Brand identity is **data, not code**:

- **Backend:** the `cms.SiteSettings` singleton stores `brand_name`, `legal_name`, `tagline`, `logo` (SVG media asset), `monogram`, `theme_key`, `seller_gstin`, `support_email`, `support_phone`, `social_links`, and the announcement bar. Admins edit it from the Next.js admin. Env vars seed it on first boot only.
- **Frontend:** `frontend/src/config/brand.ts` exports a typed `BrandConfig` resolved from `GET /api/v1/cms/site-settings/` (cached with ISR revalidation). The `NEXT_PUBLIC_BRAND_*` env vars act as a build-time fallback.
- **Theme:** `theme_key` selects a token set (`heirloom` | `darbar` | `baraat` | `dev`) defined in `frontend/src/styles/themes/`. Components only reference semantic tokens.

## Development identity (temporary)

| Field | Value |
|---|---|
| `brand_name` | `ATELIER` (shown with a "DEV" pill in non-production environments) |
| `tagline` | "Occasion wear, crafted." |
| Logo | Plain wordmark set in the display font. No symbol. |
| `theme_key` | `heirloom` (approved Direction B tokens) |

The dev identity must never ship to production. `ENVIRONMENT=production` with `BRAND_NAME=ATELIER` fails the backend startup check (`checks.brand_identity_approved`).

## Decision log

| Date | Decision |
|---|---|
| 2026-11-17 | **Direction B "Quiet Heirloom" approved** as the brand system. A's heritage language may be used for the Groom wedding campaign, and C's marigold energy for festive campaigns, as campaign accents only. |
| — | Brand name: **pending.** Shortlist from Saanjh / Anvay / Varan (or new) and run the naming due diligence above. |
