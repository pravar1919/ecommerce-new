"""Development seed data. Idempotent. Refuses to run in production.

All product imagery created here is a generated, clearly labelled DEV PLACEHOLDER
(ProductMedia.is_placeholder=True) — never real or AI-generated product photography.
"""

import datetime as dt
import io
import random
import secrets

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.postgres.fields.ranges import DateRange
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify

from apps.attributes.models import (
    Colour,
    EmbroideryType,
    Fabric,
    Fit,
    Occasion,
    Pattern,
    Size,
    SizeSystem,
    SleeveType,
)
from apps.catalog import services as catalog_services
from apps.catalog.models import (
    CollectionProduct,
    CompleteTheLook,
    MeasurementDefinition,
    Product,
    ProductMedia,
    ProductSpecification,
    ProductVariant,
    SizeChart,
    SizeChartRow,
)
from apps.categories.models import Category, Collection
from apps.inventory import services as inventory_services
from apps.inventory.models import StockLevel, StockLocation, StockMovement
from apps.pricing.models import TaxClass, TaxRule

R = 100  # paise per rupee

OCCASIONS = ["Wedding", "Reception", "Engagement", "Sangeet", "Mehendi", "Haldi", "Cocktail", "Festive"]
FABRICS = {
    "Raw Silk": "100% raw silk",
    "Jacquard Silk": "70% silk, 30% viscose",
    "Velvet": "Micro velvet, viscose blend",
    "Brocade": "Silk brocade with zari",
    "Chanderi": "Chanderi silk-cotton",
    "Linen": "100% linen",
    "Cotton Silk": "60% cotton, 40% silk",
    "Wool Blend": "70% wool, 30% polyester",
    "Terry Rayon": "Terry rayon",
}
FITS = ["Slim", "Tailored", "Regular", "Relaxed"]
PATTERNS = ["Solid", "Jacquard", "Brocade", "Printed", "Textured"]
EMBROIDERY = {
    "Zardozi": "Metallic thread and bead work",
    "Aari": "Fine chain-stitch hook work",
    "Resham": "Silk thread embroidery",
    "Chikankari": "Lucknowi shadow work",
    "Sequin": "Sequin and cut-dana work",
    "Threadwork": "Tonal thread embroidery",
    "None": "",
}
SLEEVES = ["Full", "Three-quarter", "Half", "Sleeveless"]
COLOURS = [
    ("Ivory", "#F2EBDD", "neutral"),
    ("Champagne", "#D9C3A0", "neutral"),
    ("Onyx", "#1E1D1D", "black"),
    ("Burgundy", "#651E35", "red"),
    ("Royal Blue", "#263E80", "blue"),
    ("Midnight Navy", "#1D2742", "blue"),
    ("Emerald", "#174B3B", "green"),
    ("Sage", "#9AAA8C", "green"),
    ("Marigold", "#E5A52B", "yellow"),
    ("Blush", "#E8C4C0", "pink"),
    ("Charcoal", "#3A3938", "grey"),
    ("White", "#FAFAF7", "neutral"),
]

MEASUREMENTS = [  # key, label, applies_to, min, max, guide
    ("chest", "Chest", "both", 76, 150, "Measure around the fullest part of the chest, under the arms."),
    (
        "waist",
        "Waist",
        "both",
        60,
        140,
        "Measure around your natural waist, keeping the tape comfortably loose.",
    ),
    ("hip", "Hip", "both", 76, 150, "Measure around the fullest part of the hips."),
    ("shoulder", "Shoulder", "both", 36, 60, "Measure across the back from one shoulder tip to the other."),
    ("sleeve_length", "Sleeve length", "both", 50, 75, "From the shoulder tip down to the wrist bone."),
    ("neck", "Neck", "both", 32, 50, "Around the base of the neck; keep one finger under the tape."),
    ("bicep", "Bicep", "body", 24, 50, "Around the fullest part of the upper arm."),
    ("inseam", "Inseam", "body", 60, 95, "From the crotch seam to the ankle."),
    (
        "garment_length",
        "Garment length",
        "garment",
        60,
        130,
        "Finished length from the highest shoulder point.",
    ),
]

CATEGORIES = [  # path parts, name, description
    (["sherwanis"], "Sherwanis", "Heirloom sherwanis, hand-finished for the groom and his closest circle."),
    (
        ["kurtas"],
        "Kurtas",
        "Kurtas and kurta sets for every ceremony, from haldi mornings to reception nights.",
    ),
    (["kurtas", "wedding-kurtas"], "Wedding Kurtas", "Embellished kurtas made for the wedding day."),
    (["kurtas", "kurta-sets"], "Kurta Sets", "Coordinated kurta, churidar and dupatta sets."),
    (["indo-western"], "Indo-Western", "Contemporary silhouettes cut with Indian craft."),
    (["suits-blazers"], "Suits & Blazers", "Tailoring for receptions and cocktail evenings."),
    (["suits-blazers", "wedding-suits"], "Wedding Suits", "Three-piece and tuxedo suits for the reception."),
    (["suits-blazers", "blazers"], "Blazers", "Bandhgalas and dinner jackets."),
    (["shirts"], "Shirts", "Occasion shirts in fine cottons and silks."),
    (["trousers"], "Trousers", "Churidars, pyjamas and tailored trousers."),
    (["festive"], "Festive", "Festive dressing for Diwali, Eid and family celebrations."),
    (["accessories"], "Accessories", "The finishing pieces: safas, stoles, mojaris and brooches."),
    (["accessories", "safas"], "Safas", "Hand-tied and pre-draped wedding turbans."),
    (["accessories", "stoles"], "Stoles", "Embroidered stoles and dupattas."),
    (["accessories", "mojaris"], "Mojaris", "Hand-crafted leather mojaris."),
]

CHEST = ["36", "38", "40", "42", "44", "46", "48"]
WAIST = ["28", "30", "32", "34", "36", "38", "40"]
UK = ["6", "7", "8", "9", "10", "11"]
FREE = ["Free size"]

# name, category, fabric, embroidery, pattern, fit, sleeve, colours, mrp (₹), sale (₹ or None), sizes, occasions,
# fulfilment, tax class, hsn
PRODUCTS = [
    (
        "Ivory Zardozi Raw Silk Sherwani",
        "sherwanis",
        "Raw Silk",
        "Zardozi",
        "Solid",
        "Tailored",
        "Full",
        ["Ivory", "Champagne"],
        124500,
        None,
        "chest",
        ["Wedding", "Engagement"],
        "both",
        "apparel",
        "6203",
    ),
    (
        "Burgundy Velvet Heirloom Sherwani",
        "sherwanis",
        "Velvet",
        "Zardozi",
        "Solid",
        "Tailored",
        "Full",
        ["Burgundy"],
        98500,
        88500,
        "chest",
        ["Wedding", "Reception"],
        "both",
        "apparel",
        "6203",
    ),
    (
        "Emerald Brocade Achkan Sherwani",
        "sherwanis",
        "Brocade",
        "Resham",
        "Brocade",
        "Tailored",
        "Full",
        ["Emerald", "Midnight Navy"],
        76500,
        None,
        "chest",
        ["Wedding"],
        "both",
        "apparel",
        "6203",
    ),
    (
        "Champagne Aari Jacquard Sherwani",
        "sherwanis",
        "Jacquard Silk",
        "Aari",
        "Jacquard",
        "Slim",
        "Full",
        ["Champagne"],
        68500,
        None,
        "chest",
        ["Engagement", "Reception"],
        "ready_to_wear",
        "apparel",
        "6203",
    ),
    (
        "Onyx Sequin Cocktail Sherwani",
        "sherwanis",
        "Velvet",
        "Sequin",
        "Solid",
        "Slim",
        "Full",
        ["Onyx"],
        58500,
        49500,
        "chest",
        ["Cocktail", "Reception"],
        "ready_to_wear",
        "apparel",
        "6203",
    ),
    (
        "Ivory Chikankari Wedding Kurta",
        "kurtas/wedding-kurtas",
        "Cotton Silk",
        "Chikankari",
        "Textured",
        "Regular",
        "Full",
        ["Ivory", "White"],
        14500,
        None,
        "chest",
        ["Wedding", "Mehendi"],
        "ready_to_wear",
        "apparel",
        "6211",
    ),
    (
        "Marigold Resham Haldi Kurta",
        "kurtas/wedding-kurtas",
        "Chanderi",
        "Resham",
        "Solid",
        "Relaxed",
        "Full",
        ["Marigold"],
        8900,
        6900,
        "chest",
        ["Haldi", "Mehendi"],
        "ready_to_wear",
        "apparel",
        "6211",
    ),
    (
        "Sage Threadwork Kurta Set",
        "kurtas/kurta-sets",
        "Cotton Silk",
        "Threadwork",
        "Solid",
        "Regular",
        "Full",
        ["Sage", "Blush"],
        12800,
        None,
        "chest",
        ["Mehendi", "Sangeet"],
        "ready_to_wear",
        "apparel",
        "6211",
    ),
    (
        "Royal Blue Jacquard Kurta Set",
        "kurtas/kurta-sets",
        "Jacquard Silk",
        "None",
        "Jacquard",
        "Regular",
        "Full",
        ["Royal Blue", "Burgundy"],
        16500,
        13900,
        "chest",
        ["Sangeet", "Festive"],
        "ready_to_wear",
        "apparel",
        "6211",
    ),
    (
        "Linen Pintuck Festive Kurta",
        "festive",
        "Linen",
        "None",
        "Textured",
        "Relaxed",
        "Full",
        ["White", "Sage", "Charcoal"],
        4900,
        None,
        "chest",
        ["Festive"],
        "ready_to_wear",
        "apparel",
        "6211",
    ),
    (
        "Chanderi Mirror Festive Kurta",
        "festive",
        "Chanderi",
        "Threadwork",
        "Printed",
        "Regular",
        "Three-quarter",
        ["Blush", "Marigold"],
        6500,
        5200,
        "chest",
        ["Festive", "Mehendi"],
        "ready_to_wear",
        "apparel",
        "6211",
    ),
    (
        "Midnight Draped Indo-Western Set",
        "indo-western",
        "Terry Rayon",
        "Threadwork",
        "Solid",
        "Slim",
        "Full",
        ["Midnight Navy", "Onyx"],
        42500,
        None,
        "chest",
        ["Sangeet", "Cocktail"],
        "both",
        "apparel",
        "6203",
    ),
    (
        "Ivory Asymmetric Jacket Set",
        "indo-western",
        "Raw Silk",
        "Aari",
        "Solid",
        "Slim",
        "Full",
        ["Ivory", "Emerald"],
        52500,
        46500,
        "chest",
        ["Engagement", "Sangeet"],
        "both",
        "apparel",
        "6203",
    ),
    (
        "Charcoal Three-Piece Wedding Suit",
        "suits-blazers/wedding-suits",
        "Wool Blend",
        "None",
        "Solid",
        "Tailored",
        "Full",
        ["Charcoal", "Midnight Navy"],
        38500,
        None,
        "chest",
        ["Reception", "Cocktail"],
        "both",
        "apparel",
        "6203",
    ),
    (
        "Onyx Shawl-Lapel Tuxedo",
        "suits-blazers/wedding-suits",
        "Wool Blend",
        "None",
        "Solid",
        "Slim",
        "Full",
        ["Onyx"],
        44500,
        39900,
        "chest",
        ["Reception", "Cocktail"],
        "ready_to_wear",
        "apparel",
        "6203",
    ),
    (
        "Royal Blue Jodhpuri Bandhgala",
        "suits-blazers/blazers",
        "Jacquard Silk",
        "None",
        "Jacquard",
        "Tailored",
        "Full",
        ["Royal Blue", "Burgundy", "Ivory"],
        28500,
        None,
        "chest",
        ["Reception", "Festive"],
        "both",
        "apparel",
        "6203",
    ),
    (
        "Emerald Velvet Dinner Jacket",
        "suits-blazers/blazers",
        "Velvet",
        "None",
        "Solid",
        "Slim",
        "Full",
        ["Emerald", "Burgundy"],
        24500,
        21500,
        "chest",
        ["Cocktail", "Reception"],
        "ready_to_wear",
        "apparel",
        "6203",
    ),
    (
        "Silk Mandarin Collar Shirt",
        "shirts",
        "Cotton Silk",
        "None",
        "Solid",
        "Slim",
        "Full",
        ["Ivory", "Champagne", "Onyx"],
        5900,
        None,
        "chest",
        ["Cocktail", "Festive"],
        "ready_to_wear",
        "apparel",
        "6205",
    ),
    (
        "Raw Silk Churidar",
        "trousers",
        "Raw Silk",
        "None",
        "Solid",
        "Slim",
        "Full",
        ["Ivory", "Champagne"],
        3900,
        None,
        "waist",
        ["Wedding", "Festive"],
        "ready_to_wear",
        "apparel",
        "6203",
    ),
    (
        "Tailored Wool Trouser",
        "trousers",
        "Wool Blend",
        "None",
        "Solid",
        "Tailored",
        "Full",
        ["Charcoal", "Onyx", "Midnight Navy"],
        6900,
        5900,
        "waist",
        ["Reception"],
        "ready_to_wear",
        "apparel",
        "6203",
    ),
    (
        "Hand-Tied Bandhani Safa",
        "accessories/safas",
        "Chanderi",
        "None",
        "Printed",
        "Regular",
        "Sleeveless",
        ["Marigold", "Burgundy", "Blush"],
        4500,
        None,
        "free",
        ["Wedding"],
        "ready_to_wear",
        "apparel",
        "6505",
    ),
    (
        "Zardozi Wedding Stole",
        "accessories/stoles",
        "Raw Silk",
        "Zardozi",
        "Solid",
        "Regular",
        "Sleeveless",
        ["Ivory", "Burgundy"],
        7900,
        None,
        "free",
        ["Wedding", "Engagement"],
        "ready_to_wear",
        "apparel",
        "6214",
    ),
    (
        "Embroidered Leather Mojari",
        "accessories/mojaris",
        "Raw Silk",
        "Zardozi",
        "Solid",
        "Regular",
        "Sleeveless",
        ["Ivory", "Onyx", "Champagne"],
        5500,
        4700,
        "uk",
        ["Wedding", "Festive"],
        "ready_to_wear",
        "footwear",
        "6403",
    ),
]

LOOKS = {
    "Ivory Zardozi Raw Silk Sherwani": [
        "Hand-Tied Bandhani Safa",
        "Zardozi Wedding Stole",
        "Embroidered Leather Mojari",
        "Raw Silk Churidar",
    ],
    "Burgundy Velvet Heirloom Sherwani": ["Zardozi Wedding Stole", "Embroidered Leather Mojari"],
    "Royal Blue Jodhpuri Bandhgala": ["Tailored Wool Trouser", "Silk Mandarin Collar Shirt"],
}

COLLECTIONS = [
    (
        "The Groom Edit",
        "burgundy",
        "Heirloom sherwanis and the pieces that finish them.",
        [
            "Ivory Zardozi Raw Silk Sherwani",
            "Burgundy Velvet Heirloom Sherwani",
            "Emerald Brocade Achkan Sherwani",
            "Champagne Aari Jacquard Sherwani",
            "Hand-Tied Bandhani Safa",
            "Zardozi Wedding Stole",
        ],
    ),
    (
        "Sangeet Nights",
        "royal",
        "Movement, colour and shine for the night before.",
        [
            "Royal Blue Jacquard Kurta Set",
            "Midnight Draped Indo-Western Set",
            "Onyx Sequin Cocktail Sherwani",
            "Sage Threadwork Kurta Set",
        ],
    ),
    (
        "The Festive Edit",
        "emerald",
        "Considered festive dressing for the season of celebrations.",
        [
            "Linen Pintuck Festive Kurta",
            "Chanderi Mirror Festive Kurta",
            "Royal Blue Jodhpuri Bandhgala",
            "Emerald Velvet Dinner Jacket",
        ],
    ),
]


def placeholder_png(
    label: str, hex_colour: str, index: int, size=(1600, 2000), note="not product photography"
) -> bytes:
    from PIL import Image, ImageDraw, ImageFont

    w, h = size
    rgb = tuple(int(hex_colour[i : i + 2], 16) for i in (1, 3, 5))
    light = sum(rgb) / 3 > 140
    fg = (36, 35, 35) if light else (248, 244, 236)
    img = Image.new("RGB", (w, h), rgb)
    d = ImageDraw.Draw(img)
    d.rectangle([60, 60, w - 60, h - 60], outline=fg, width=4)
    scale = min(w, h) / 1600
    big, small = ImageFont.load_default(size=int(96 * scale)), ImageFont.load_default(size=int(56 * scale))
    d.text((w / 2, h / 2 - 120 * scale), "DEV PLACEHOLDER", fill=fg, font=big, anchor="mm")
    d.text((w / 2, h / 2 + 20 * scale), label[:48], fill=fg, font=small, anchor="mm")
    d.text((w / 2, h / 2 + 110 * scale), f"image {index + 1} · {note}", fill=fg, font=small, anchor="mm")
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


class Command(BaseCommand):
    help = "Seed development data (idempotent). Never runs in production."

    def add_arguments(self, parser):
        parser.add_argument("--no-images", action="store_true", help="Skip placeholder image upload")
        parser.add_argument("--admin-email", default="admin@localhost")

    def handle(self, *args, **opts):
        if settings.ENVIRONMENT == "production":
            raise CommandError("seed_dev refuses to run with ENVIRONMENT=production.")
        rng = random.Random(42)
        with transaction.atomic():
            self.taxes()
            location = self.location()
            attrs = self.attributes()
            self.measurements_and_charts(attrs)
            cats = self.categories()
            products = self.products(cats, attrs, rng)
        # stock + images outside the big transaction (services manage their own; S3 upload is slow)
        self.stock(products, location, rng)
        if not opts["no_images"]:
            self.images(products)
        with transaction.atomic():
            self.looks_and_collections(products)
            for p in products.values():
                if p.status != Product.Status.PUBLISHED and p.media.exists():
                    catalog_services.publish_product(p)
        catalog_services.update_search_vectors([p.pk for p in products.values()])
        from devtools.cms_seed import seed_cms

        seed_cms(images=not opts["no_images"], placeholder_png=placeholder_png, log=self.stdout.write)
        self.admin_user(opts["admin_email"])
        self.stdout.write(self.style.SUCCESS(f"Seeded {len(products)} products."))

    # ---------------------------------------------------------------------------------------------
    def taxes(self):
        # GST rationalisation effective 22 Sep 2025: ≤ ₹2,500 per piece 5%, above 18%. CONFIRM WITH CA.
        for code, name in (("apparel", "Apparel & made-up textiles"), ("footwear", "Footwear")):
            tc, _ = TaxClass.objects.get_or_create(code=code, defaults={"name": name})
            if not tc.rules.exists():
                TaxRule.objects.create(
                    tax_class=tc,
                    threshold_paise=2500 * R,
                    rate_below_bp=500,
                    rate_above_bp=1800,
                    effective=DateRange(dt.date(2025, 9, 22), None),
                    notification_ref="DEV SEED — confirm with CA",
                )

    def location(self):
        loc, _ = StockLocation.objects.get_or_create(
            code="main",
            defaults={"name": "Main warehouse", "state_code": settings.SELLER_STATE_CODE, "is_default": True},
        )
        return loc

    def attributes(self):
        out = {
            "occasion": {},
            "fabric": {},
            "fit": {},
            "pattern": {},
            "embroidery": {},
            "sleeve": {},
            "colour": {},
        }
        for i, n in enumerate(OCCASIONS):
            out["occasion"][n], _ = Occasion.objects.get_or_create(
                slug=slugify(n), defaults={"name": n, "position": i}
            )
        for n, comp in FABRICS.items():
            out["fabric"][n], _ = Fabric.objects.get_or_create(
                slug=slugify(n), defaults={"name": n, "composition": comp}
            )
        for model, key, names in (
            (Fit, "fit", FITS),
            (Pattern, "pattern", PATTERNS),
            (SleeveType, "sleeve", SLEEVES),
        ):
            for n in names:
                out[key][n], _ = model.objects.get_or_create(slug=slugify(n), defaults={"name": n})
        for n, desc in EMBROIDERY.items():
            out["embroidery"][n], _ = EmbroideryType.objects.get_or_create(
                slug=slugify(n), defaults={"name": n, "description": desc}
            )
        for n, hx, fam in COLOURS:
            out["colour"][n], _ = Colour.objects.get_or_create(
                slug=slugify(n), defaults={"name": n, "hex": hx, "family": fam}
            )
        systems = {}
        for key, name, labels in (
            ("chest", "Menswear chest (in)", CHEST),
            ("waist", "Trouser waist (in)", WAIST),
            ("uk", "Footwear UK", UK),
            ("free", "One size", FREE),
        ):
            sys_, _ = SizeSystem.objects.get_or_create(slug=slugify(name), defaults={"name": name})
            systems[key] = {"system": sys_, "sizes": {}}
            for i, lab in enumerate(labels):
                systems[key]["sizes"][lab], _ = Size.objects.get_or_create(
                    system=sys_, label=lab, defaults={"sort_order": i}
                )
        out["sizes"] = systems
        return out

    def measurements_and_charts(self, attrs):
        defs = {}
        for i, (key, label, applies, lo, hi, guide) in enumerate(MEASUREMENTS):
            defs[key], _ = MeasurementDefinition.objects.get_or_create(
                key=key,
                defaults={
                    "label": label,
                    "applies_to": applies,
                    "min_cm": lo,
                    "max_cm": hi,
                    "guide_text": guide,
                    "position": i,
                },
            )
        chest_sys = attrs["sizes"]["chest"]
        chart, created = SizeChart.objects.get_or_create(
            name="Sherwanis & kurtas — garment measurements",
            defaults={
                "size_system": chest_sys["system"],
                "notes": "Garment measurements in cm, laid flat and doubled. Allow 8–10 cm ease over body chest.",
            },
        )
        if created:
            for i, lab in enumerate(CHEST):
                chest_in = int(lab)
                vals = {
                    "chest": chest_in * 2.54 + 10,
                    "waist": chest_in * 2.54 + 2,
                    "shoulder": 42 + i * 1.5,
                    "sleeve_length": 62 + i * 0.8,
                    "garment_length": 104 + i * 1.5,
                }
                for key, v in vals.items():
                    SizeChartRow.objects.create(
                        size_chart=chart,
                        size=chest_sys["sizes"][lab],
                        measurement=defs[key],
                        value_cm=round(v, 1),
                    )
        attrs["size_chart"] = chart

    def categories(self):
        cats = {}
        for i, (parts, name, desc) in enumerate(CATEGORIES):
            parent = cats.get("/".join(parts[:-1])) if len(parts) > 1 else None
            cat, _ = Category.objects.get_or_create(
                slug=parts[-1], defaults={"name": name, "parent": parent, "description": desc, "position": i}
            )
            cats["/".join(parts)] = cat
        return cats

    def products(self, cats, attrs, rng):
        out = {}
        tax = {tc.code: tc for tc in TaxClass.objects.all()}
        now = timezone.now()
        for idx, row in enumerate(PRODUCTS):
            (
                name,
                cat,
                fabric,
                emb,
                pattern,
                fit,
                sleeve,
                colours,
                mrp,
                sale,
                sizes,
                occ,
                fulfil,
                tclass,
                hsn,
            ) = row
            kind = cats[cat].name.lower().rstrip("s")
            p, created = Product.objects.get_or_create(
                slug=slugify(name),
                defaults=dict(
                    name=name,
                    category=cats[cat],
                    fabric=attrs["fabric"][fabric],
                    embroidery=attrs["embroidery"][emb],
                    pattern=attrs["pattern"][pattern],
                    fit=attrs["fit"][fit],
                    sleeve_type=attrs["sleeve"][sleeve],
                    fulfilment_type=fulfil,
                    mtm_lead_time_days=21 if fulfil != "ready_to_wear" else None,
                    size_chart=attrs["size_chart"] if sizes == "chest" else None,
                    tax_class=tax[tclass],
                    hsn_code=hsn,
                    short_description=(
                        f"{fabric} {kind} with {emb.lower()} detailing."
                        if emb != "None"
                        else f"Clean-lined {fabric.lower()} {kind}."
                    ),
                    description=(
                        f"[DEV SEED COPY] Cut in {FABRICS[fabric].lower()}, finished by hand in our atelier. "
                        f"Designed for {', '.join(o.lower() for o in occ)} — an heirloom piece made to be "
                        "worn again."
                    ),
                    care_instructions="Dry clean only. Store in the muslin garment bag provided, away from direct sun.",
                    merch_rank=(idx + 1) * 10,
                    is_returnable=not cat.startswith("accessories/safas"),
                ),
            )
            if created:
                p.occasions.set([attrs["occasion"][o] for o in occ])
                ProductSpecification.objects.bulk_create(
                    [
                        ProductSpecification(product=p, key="Fabric", value=FABRICS[fabric], position=0),
                        ProductSpecification(product=p, key="Fit", value=fit, position=1),
                        ProductSpecification(product=p, key="Origin", value="Made in India", position=2),
                    ]
                )
                size_map = attrs["sizes"][sizes]["sizes"]
                code = "".join(w[0] for w in name.split()[:4]).upper()
                for ci, colour in enumerate(colours):
                    cc = slugify(colour)[:3].upper()
                    for si, label in enumerate(size_map):
                        ProductVariant.objects.create(
                            product=p,
                            sku=f"{code}-{idx:02d}-{cc}-{slugify(label).upper()}",
                            colour=attrs["colour"][colour],
                            size=size_map[label],
                            mrp_paise=mrp * R,
                            sale_price_paise=sale * R if sale else None,
                            position=ci * 100 + si,
                        )
                    if fulfil != "ready_to_wear":
                        ProductVariant.objects.create(
                            product=p,
                            sku=f"{code}-{idx:02d}-{cc}-MTM",
                            colour=attrs["colour"][colour],
                            size=None,
                            inventory_policy=ProductVariant.InventoryPolicy.MADE_TO_ORDER,
                            mrp_paise=round(mrp * 1.12) * R,
                            position=ci * 100 + 99,
                        )
                # stagger publish dates so "newest" and "new" badges are meaningful
                p.published_at = now - dt.timedelta(days=rng.randint(1, 90))
                p.save(update_fields=["published_at"])
            out[name] = p
        return out

    def stock(self, products, location, rng):
        for p in products.values():
            for v in p.variants.filter(inventory_policy=ProductVariant.InventoryPolicy.TRACK):
                if StockLevel.objects.filter(variant=v, location=location).exists():
                    continue
                qty = rng.choice([0, 1, 2, 3, 5, 8, 12, 12, 20])
                StockLevel.objects.create(variant=v, location=location, on_hand=0)
                if qty:
                    inventory_services.adjust_stock(
                        variant_id=v.pk,
                        delta=qty,
                        reason=StockMovement.Reason.RECEIPT,
                        location=location,
                        note="dev seed",
                    )

    def images(self, products):
        for p in products.values():
            if p.media.exists():
                continue
            colours = list(dict.fromkeys(v.colour for v in p.variants.select_related("colour")))
            n = 0
            for colour in colours:
                for j in range(2 if colour == colours[0] else 1):
                    m = ProductMedia(
                        product=p,
                        colour=colour,
                        role="primary" if n == 0 else "gallery",
                        alt_text=f"Development placeholder for {p.name} in {colour.name}",
                        width=1600,
                        height=2000,
                        position=n,
                        is_placeholder=True,
                    )
                    m.file.save(
                        f"dev-placeholder-{slugify(colour.name)}-{j + 1}.png",
                        ContentFile(placeholder_png(f"{p.name} · {colour.name}", colour.hex, n)),
                        save=False,
                    )
                    m.save()
                    n += 1
            self.stdout.write(f"  images: {p.name} ({n})")

    def looks_and_collections(self, products):
        for src, targets in LOOKS.items():
            for i, t in enumerate(targets):
                CompleteTheLook.objects.get_or_create(
                    product=products[src],
                    related_product=products[t],
                    kind="complete_look",
                    defaults={"position": i},
                )
        for i, (name, accent, desc, items) in enumerate(COLLECTIONS):
            col, _ = Collection.objects.get_or_create(
                slug=slugify(name),
                defaults={
                    "name": name,
                    "accent": accent,
                    "description": desc,
                    "is_published": True,
                    "position": i,
                },
            )
            for j, pname in enumerate(items):
                CollectionProduct.objects.get_or_create(
                    collection=col, product=products[pname], defaults={"position": j}
                )

    def admin_user(self, email):
        User = get_user_model()
        if User.objects.filter(email__iexact=email).exists():
            return
        password = secrets.token_urlsafe(12)
        user = User.objects.create_superuser(
            email=email, password=password, first_name="Dev", last_name="Admin"
        )
        user.groups.add(Group.objects.get(name="Owner"))
        self.stdout.write(self.style.WARNING(f"Created dev superuser {email} / {password}  (shown once)"))
