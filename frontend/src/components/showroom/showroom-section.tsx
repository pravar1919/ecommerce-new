import Image from "next/image";
import Link from "next/link";

import { SectionHeading } from "@/components/editorial/section";
import { getCategoryProducts } from "@/lib/api/server";
import { focalPosition } from "@/lib/media";
import { toLite } from "@/lib/product-lite";
import { routes } from "@/lib/routes";

import { ShowroomIsland } from "./showroom-island";
import type { ShowroomWall } from "./types";
import "./showroom.css";

/**
 * Walls of the salon, in walking order. A frontend placeholder until the CMS gains a "showroom"
 * block, at which point editors choose these.
 */
const WALLS = [
  { path: "sherwanis", label: "Sherwanis" },
  { path: "kurtas", label: "Kurtas" },
  { path: "suits-blazers", label: "Suits" },
  { path: "accessories", label: "Accessories" },
] as const;

const TITLE = "Step inside the salon";

/**
 * Homepage virtual salon. The server renders the first wall flat (real links, readable without
 * JS); the 3D room replaces it as the section nears the viewport. Empty categories are left out,
 * and the section disappears entirely if the catalogue is unavailable.
 */
export async function ShowroomSection() {
  const walls: ShowroomWall[] = (
    await Promise.all(
      WALLS.map(async (w) => ({ ...w, products: (await getCategoryProducts(w.path, 4)).map(toLite) })),
    )
  ).filter((w) => w.products.length > 0);
  if (walls.length < 2) return null;

  const id = "s-showroom";
  const first = walls[0];
  return (
    <section data-section="showroom" aria-labelledby={id} className="surface-inverse pt-section-sm">
      <div className="container-page">
        <SectionHeading
          id={id}
          eyebrow="Virtual salon"
          title={TITLE}
          cta={{ label: "Browse every category", href: routes.search() }}
        />
        <p className="mt-6 max-w-lg text-body-lg text-text-muted" data-reveal suppressHydrationWarning>
          Turn between the walls, then step up to a piece to see it closer.
        </p>
      </div>
      <div className="mt-10 md:mt-14">
        <ShowroomIsland walls={walls} title={TITLE}>
          <div className="sr-wrap">
            <div className="sr-stage">
              <div className="sr-hud top-5 left-[var(--page-margin)] md:top-8">
                <p className="eyebrow text-ornament">Wall 01 / {String(walls.length).padStart(2, "0")}</p>
                <p className="mt-2 font-display text-display-md">{first.label}</p>
              </div>
              <ul className="sr-hang" aria-label={first.label}>
                {first.products.map((p) => (
                  <li key={p.id}>
                    <Link href={routes.product(p.slug)} className="sr-frame block" aria-label={p.name}>
                      <span className="sr-frame-img block">
                        {p.primary_image && (
                          <Image
                            src={p.primary_image.url}
                            alt=""
                            fill
                            sizes="(min-width: 768px) 360px, 240px"
                            className="object-cover"
                            style={{
                              objectPosition: focalPosition(p.primary_image.focal_x, p.primary_image.focal_y),
                            }}
                          />
                        )}
                      </span>
                    </Link>
                  </li>
                ))}
              </ul>
              <nav
                aria-label="Salon walls"
                className="sr-hud inset-x-0 bottom-5 flex justify-center px-3 md:bottom-8"
              >
                <ul className="sr-pills no-scrollbar max-w-full overflow-x-auto">
                  {walls.map((w) => (
                    <li key={w.path}>
                      <Link href={routes.category(w.path)} className="sr-pill inline-flex items-center">
                        {w.label}
                      </Link>
                    </li>
                  ))}
                </ul>
              </nav>
            </div>
          </div>
        </ShowroomIsland>
      </div>
    </section>
  );
}
