import type { Block } from "@/lib/api/types";

import { CampaignHero } from "./campaign-hero";
import { CategoryMosaic } from "./category-mosaic";
import { CollectionFeature } from "./collection-feature";
import { CraftStory } from "./craft-story";
import { EditorialSplit } from "./editorial-split";
import { InstagramGallery } from "./instagram-gallery";
import { NewsletterSignup } from "./newsletter-signup";
import { OccasionTiles } from "./occasion-tiles";
import { ProductRail } from "./product-rail";
import { RichText } from "./rich-text";
import { sectionId } from "./section";
import { Testimonials } from "./testimonials";

/** Maps each CMS block type 1:1 to its editorial component. Unknown types render nothing. */
export function BlockRenderer({ block }: { block: Block }) {
  switch (block.type) {
    case "hero":
      return <CampaignHero config={block.config} />;
    case "category_grid":
      return <CategoryMosaic block={block} />;
    case "product_rail":
      return <ProductRail block={block} />;
    case "collection_feature":
      return <CollectionFeature block={block} />;
    case "occasion_tiles":
      return <OccasionTiles block={block} />;
    case "editorial_split":
      return <EditorialSplit block={block} />;
    case "craft_story":
      return <CraftStory block={block} />;
    case "testimonials":
      return <Testimonials block={block} />;
    case "instagram_gallery":
      return <InstagramGallery block={block} />;
    case "newsletter": {
      const id = sectionId(block.id);
      return (
        <section data-section="newsletter" aria-labelledby={id} className="border-t bg-surface py-section">
          <div className="container-page">
            <NewsletterSignup
              headingId={id}
              headline={block.config.headline}
              body={block.config.body}
              eyebrow={block.config.eyebrow}
              consentText={block.config.consent_text}
            />
          </div>
        </section>
      );
    }
    case "rich_text":
      return <RichText block={block} />;
    default:
      return null;
  }
}
