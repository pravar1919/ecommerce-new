import pytest

from apps.catalog.models import Product
from apps.inventory.models import StockLevel

pytestmark = pytest.mark.django_db
URL = "/api/v1/catalog/products/"


def names(r):
    assert r.status_code == 200, r.json()
    return [p["name"] for p in r.json()["results"]]


@pytest.fixture
def shop(catalog):
    c = catalog
    return {
        "ivory": c.product(
            "Ivory Zardozi Sherwani",
            colours=("Ivory", "Burgundy"),
            mrp=120_000_00,
            occasions=[c.wedding],
            fabric=c.silk,
            embroidery=c.zardozi,
            fulfilment="both",
            rank=1,
        ),
        "burgundy": c.product(
            "Burgundy Velvet Sherwani",
            colours=("Burgundy",),
            mrp=90_000_00,
            sale=80_000_00,
            occasions=[c.wedding],
            fabric=c.silk,
            rank=2,
            days_ago=60,
        ),
        "haldi": c.product(
            "Marigold Haldi Kurta",
            category=c.kurta_sets,
            colours=("Emerald",),
            mrp=8_000_00,
            occasions=[c.haldi],
            fabric=c.linen,
            stock=0,
            rank=3,
        ),
        "draft": c.product("Secret Draft Sherwani", publish=False),
    }


def test_listing_excludes_unpublished_and_inactive(api, shop, catalog):
    assert "Secret Draft Sherwani" not in names(api.get(URL))
    catalog.kurtas.is_active = False
    catalog.kurtas.save()
    catalog.kurta_sets.is_active = False
    catalog.kurta_sets.save()
    assert "Marigold Haldi Kurta" not in names(api.get(URL))


def test_card_shape_and_prices(api, shop):
    cards = {p["name"]: p for p in api.get(URL).json()["results"]}
    b = cards["Burgundy Velvet Sherwani"]
    assert b["price"]["current"] == {"amount": 8_000_000, "currency": "INR", "formatted": "₹80,000"}
    assert b["price"]["mrp"]["formatted"] == "₹90,000" and b["price"]["discount_percent"] == 11
    assert "sale" in b["badges"] and "new" not in b["badges"]
    iv = cards["Ivory Zardozi Sherwani"]
    assert iv["is_mtm_available"] and "made_to_measure" in iv["badges"] and "new" in iv["badges"]
    assert [c["slug"] for c in iv["colours"]] == ["ivory", "burgundy"]
    assert iv["primary_image"]["alt"] == "Ivory Zardozi Sherwani front"
    assert iv["category"]["path"] == "sherwanis"
    assert "sold_out" in cards["Marigold Haldi Kurta"]["badges"]


def test_category_filter_includes_descendants(api, shop):
    assert names(api.get(URL, {"category": "kurtas"})) == ["Marigold Haldi Kurta"]
    assert names(api.get(URL, {"category": "kurtas/kurta-sets"})) == ["Marigold Haldi Kurta"]
    assert set(names(api.get(URL, {"category": "sherwanis"}))) == {
        "Ivory Zardozi Sherwani",
        "Burgundy Velvet Sherwani",
    }


def test_attribute_filters(api, shop):
    assert names(api.get(URL, {"occasion": "haldi"})) == ["Marigold Haldi Kurta"]
    assert set(names(api.get(URL, {"occasion": "haldi,wedding"}))) == {
        "Ivory Zardozi Sherwani",
        "Burgundy Velvet Sherwani",
        "Marigold Haldi Kurta",
    }
    assert names(api.get(URL, {"embroidery": "zardozi"})) == ["Ivory Zardozi Sherwani"]
    assert names(api.get(URL, {"fabric": "linen"})) == ["Marigold Haldi Kurta"]
    assert names(api.get(URL, {"fulfilment": "made_to_measure"})) == ["Ivory Zardozi Sherwani"]


def test_variant_conditions_must_match_the_same_variant(api, shop):
    from apps.catalog.models import ProductVariant

    # Ivory sherwani: every ivory ready-to-wear size sells out; burgundy/40 still in stock.
    StockLevel.objects.filter(variant__product=shop["ivory"], variant__colour__slug="ivory").update(on_hand=0)
    # ivory + 40 + in stock must be satisfied by ONE variant -> none qualifies (MTM variant has no size)
    assert "Ivory Zardozi Sherwani" not in names(
        api.get(URL, {"colour": "ivory", "size": "40", "in_stock": "true"})
    )
    assert "Ivory Zardozi Sherwani" in names(
        api.get(URL, {"colour": "burgundy", "size": "40", "in_stock": "true"})
    )
    # without a size, the made-to-measure ivory variant is always available
    assert "Ivory Zardozi Sherwani" in names(api.get(URL, {"colour": "ivory", "in_stock": "true"}))
    ProductVariant.objects.filter(product=shop["ivory"], size__isnull=True).update(is_active=False)
    assert "Ivory Zardozi Sherwani" not in names(api.get(URL, {"colour": "ivory", "in_stock": "true"}))


def test_in_stock_ignores_reserved_units(api, shop):
    StockLevel.objects.filter(variant__product=shop["burgundy"]).update(on_hand=2, reserved=2)
    assert "Burgundy Velvet Sherwani" not in names(api.get(URL, {"in_stock": "true"}))


def test_price_filter_and_sorting(api, shop):
    got = names(api.get(URL, {"price_min": 8_000_00, "price_max": 85_000_00, "ordering": "price_asc"}))
    assert got == ["Marigold Haldi Kurta", "Burgundy Velvet Sherwani"]
    assert names(api.get(URL, {"ordering": "price_desc"}))[0] == "Ivory Zardozi Sherwani"
    assert names(api.get(URL, {"ordering": "featured"})) == [
        "Ivory Zardozi Sherwani",
        "Burgundy Velvet Sherwani",
        "Marigold Haldi Kurta",
    ]
    assert names(api.get(URL, {"ordering": "newest"}))[-1] == "Burgundy Velvet Sherwani"


def test_invalid_query_params(api, shop):
    r = api.get(URL, {"ordering": "cheapest"})
    assert r.status_code == 400 and "ordering" in r.json()["error"]["fields"]
    assert api.get(URL, {"price_min": -1}).status_code == 400


def test_facets_are_disjunctive(api, shop):
    f = api.get(URL + "facets/", {"category": "sherwanis", "colour": "ivory"}).json()
    colours = {c["slug"]: c["count"] for c in f["colour"]}
    assert colours == {"ivory": 1, "burgundy": 2}  # colour facet ignores its own selection
    assert {s["label"]: s["count"] for s in f["size"]} == {"38": 1, "40": 1, "42": 1}
    assert f["price"] == {"min": 120_000_00, "max": 120_000_00}
    assert {o["slug"]: o["count"] for o in f["occasion"]} == {"wedding": 1}


def test_search_fulltext_and_typo_tolerance(api, shop):
    assert names(api.get("/api/v1/catalog/search/", {"q": "zardozi"})) == ["Ivory Zardozi Sherwani"]
    assert set(names(api.get("/api/v1/catalog/search/", {"q": "sherwani"}))) == {
        "Ivory Zardozi Sherwani",
        "Burgundy Velvet Sherwani",
    }
    assert "Burgundy Velvet Sherwani" in names(api.get("/api/v1/catalog/search/", {"q": "velvett"}))
    assert names(api.get("/api/v1/catalog/search/", {"q": "Secret Draft"})) == []
    s = api.get("/api/v1/catalog/search/suggest/", {"q": "zard"}).json()
    assert s["products"][0]["name"] == "Ivory Zardozi Sherwani" and "Zardozi" in s["queries"]
    assert api.get("/api/v1/catalog/search/suggest/", {"q": "z"}).json()["products"] == []


def test_product_detail_with_stock_statuses(api, shop, settings):
    settings.LOW_STOCK_DISPLAY_THRESHOLD = 3
    p = shop["ivory"]
    levels = StockLevel.objects.filter(variant__product=p, variant__colour__slug="ivory").order_by(
        "variant__sku"
    )
    levels.filter(variant__size__label="38").update(on_hand=0)
    levels.filter(variant__size__label="40").update(on_hand=3, reserved=1)
    d = api.get(f"{URL}{p.slug}/").json()
    status = {(v["colour"], v["size"]): (v["stock_status"], v["low_stock_quantity"]) for v in d["variants"]}
    assert status[("ivory", "38")] == ("out_of_stock", None)
    assert status[("ivory", "40")] == ("low_stock", 2)
    assert status[("ivory", "42")] == ("in_stock", None)
    assert status[("ivory", None)] == ("made_to_order", None)
    assert d["fabric"] == {"slug": "raw-silk", "name": "Raw Silk"} and d["mtm_lead_time_days"] == 21
    assert d["seo"]["title"] == p.name
    assert api.get(f"{URL}{shop['draft'].slug}/").status_code == 404


def test_related_and_complete_the_look(api, shop):
    from apps.catalog.models import CompleteTheLook

    CompleteTheLook.objects.create(product=shop["ivory"], related_product=shop["haldi"], kind="complete_look")
    look = api.get(f"{URL}{shop['ivory'].slug}/complete-the-look/").json()
    assert [p["name"] for p in look] == ["Marigold Haldi Kurta"]
    related = [p["name"] for p in api.get(f"{URL}{shop['ivory'].slug}/related/").json()]
    assert related == ["Burgundy Velvet Sherwani"]


def test_category_tree_and_detail(api, shop):
    tree = api.get("/api/v1/catalog/categories/").json()
    assert {c["slug"] for c in tree} == {"sherwanis", "kurtas"}
    kurtas = next(c for c in tree if c["slug"] == "kurtas")
    assert [c["slug"] for c in kurtas["children"]] == ["kurta-sets"]
    d = api.get("/api/v1/catalog/categories/kurtas/kurta-sets/").json()
    assert [b["slug"] for b in d["breadcrumbs"]] == ["kurtas"]
    assert api.get("/api/v1/catalog/categories/nope/").status_code == 404


def test_listing_query_count_is_bounded(api, shop, catalog, django_assert_max_num_queries):
    for i in range(10):
        catalog.product(f"Extra {i}", colours=("Ivory", "Emerald"))
    with django_assert_max_num_queries(6):
        r = api.get(URL)
    assert r.json()["count"] == 13
    assert Product.objects.count() == 14
