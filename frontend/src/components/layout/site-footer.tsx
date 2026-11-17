import Link from "next/link";
import { cacheLife } from "next/cache";
import { PlusIcon } from "lucide-react";

import { fallbackBrand, resolveBrand } from "@/config/brand";
import { getSiteSettings } from "@/lib/api/server";
import type { SiteSettings } from "@/lib/api/types";
import { isExternal } from "@/lib/routes";

async function currentYear() {
  "use cache";
  cacheLife("days");
  return new Date().getFullYear();
}

const NETWORK_LABEL: Record<string, string> = {
  instagram: "Instagram",
  youtube: "YouTube",
  facebook: "Facebook",
  pinterest: "Pinterest",
  whatsapp: "WhatsApp",
  x: "X",
};

function FooterLink({ href, label }: { href: string; label: string }) {
  const ext = isExternal(href);
  return (
    <Link
      href={href}
      className="inline-block py-1.5 text-body text-text-muted transition-colors hover:text-text"
      {...(ext ? { target: "_blank", rel: "noopener noreferrer" } : {})}
    >
      {label}
    </Link>
  );
}

function Columns({ columns }: { columns: SiteSettings["footer"]["columns"] }) {
  return (
    <>
      {/* mobile: native disclosure (no client JS), styled like the accordion */}
      <div className="md:hidden">
        {columns.map((col) => (
          <details key={col.title} className="group border-b">
            <summary className="eyebrow flex min-h-12 cursor-pointer list-none items-center justify-between gap-4 py-3 [&::-webkit-details-marker]:hidden">
              {col.title}
              <PlusIcon
                aria-hidden
                className="size-4 shrink-0 transition-transform duration-(--dur-base) ease-standard group-open:rotate-45"
              />
            </summary>
            <nav aria-label={col.title} className="pb-5">
              <ul>
                {col.links.map((l) => (
                  <li key={l.href + l.label}>
                    <FooterLink {...l} />
                  </li>
                ))}
              </ul>
            </nav>
          </details>
        ))}
      </div>
      {/* tablet+: columns */}
      <div className="hidden gap-gutter md:grid md:grid-cols-3">
        {columns.map((col) => (
          <nav key={col.title} aria-label={col.title}>
            <h2 className="eyebrow">{col.title}</h2>
            <ul className="mt-4">
              {col.links.map((l) => (
                <li key={l.href + l.label}>
                  <FooterLink {...l} />
                </li>
              ))}
            </ul>
          </nav>
        ))}
      </div>
    </>
  );
}

export async function SiteFooter() {
  const [settings, year] = await Promise.all([getSiteSettings(), currentYear()]);
  const brand = resolveBrand(settings);
  return <FooterFrame settings={settings} brandName={brand.name} tagline={brand.tagline} year={year} />;
}

export async function SiteFooterFallback() {
  const year = await currentYear();
  return (
    <FooterFrame settings={null} brandName={fallbackBrand.name} tagline={fallbackBrand.tagline} year={year} />
  );
}

function FooterFrame({
  settings,
  brandName,
  tagline,
  year,
}: {
  settings: SiteSettings | null;
  brandName: string;
  tagline: string;
  year: number;
}) {
  const legal = settings?.legal_name || brandName;
  return (
    <footer data-section="footer" className="surface-inverse">
      <div className="container-page grid-editorial gap-y-10 pt-section-sm pb-10">
        <div className="col-span-4 md:col-span-3 lg:col-span-5">
          <p className="font-display text-display-lg tracking-[0.08em] uppercase">{brandName}</p>
          {tagline && <p className="mt-4 max-w-xs text-body-lg text-text-muted">{tagline}</p>}
          <span aria-hidden className="mt-8 block h-px w-24 bg-ornament" />
          {settings && (settings.support_email || settings.support_phone) && (
            <address className="mt-8 space-y-1 text-body text-text-muted not-italic">
              {settings.support_email && (
                <a className="block hover:text-text" href={`mailto:${settings.support_email}`}>
                  {settings.support_email}
                </a>
              )}
              {settings.support_phone && (
                <a
                  className="block hover:text-text"
                  href={`tel:${settings.support_phone.replace(/\s/g, "")}`}
                >
                  {settings.support_phone}
                </a>
              )}
            </address>
          )}
        </div>
        <div className="col-span-4 md:col-span-5 lg:col-span-6 lg:col-start-7">
          {settings && settings.footer.columns.length > 0 && <Columns columns={settings.footer.columns} />}
        </div>
        <div className="col-span-full flex flex-col gap-4 border-t pt-8 text-caption text-text-muted md:flex-row md:items-center md:justify-between">
          <p>
            © {year} {legal}
            {settings?.footer.note ? ` · ${settings.footer.note}` : ""}
          </p>
          {settings && settings.social_links.length > 0 && (
            <ul className="flex gap-5" aria-label="Social">
              {settings.social_links.map((s) => (
                <li key={s.network}>
                  <a
                    href={s.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="eyebrow hover:text-text"
                  >
                    {NETWORK_LABEL[s.network] ?? s.network}
                  </a>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </footer>
  );
}
