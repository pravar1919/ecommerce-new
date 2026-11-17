import datetime as dt
import uuid
from unittest import mock

import pytest
from django.core import mail
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.catalog.models import CollectionProduct
from apps.categories.models import Collection
from apps.cms import selectors, services
from apps.cms.blocks import BlockConfigError, validate_config
from apps.cms.models import (
    ContentBlock,
    MediaAsset,
    NavigationFeature,
    NewsletterSubscriber,
    Page,
    PageVersion,
    SiteSettings,
)
from apps.cms.models import (
    Testimonial as QuoteRow,
)
from conftest import make_user

pytestmark = pytest.mark.django_db


def media(alt="Campaign image", **kw) -> MediaAsset:
    m = MediaAsset(alt_text=alt, width=1600, height=2000, **kw)
    m.file.save("x.png", ContentFile(b"png"), save=False)
    m.save()
    return m


def page_with(blocks: list[tuple[str, dict]], *, slug="home", publish=True) -> PageVersion:
    page, _ = Page.objects.get_or_create(slug=slug, defaults={"title": slug.title(), "template": "home"})
    v = PageVersion.objects.create(page=page)
    for i, (t, c) in enumerate(blocks):
        ContentBlock.objects.create(page_version=v, type=t, position=i, config=c)
    if publish:
        services.publish_version(v)
    return v


# ---------- block config validation ----------------------------------------------------------------
class TestBlockValidation:
    def test_hero_normalises_defaults(self):
        mid = str(uuid.uuid4())
        out = validate_config("hero", {"slides": [{"headline": "Hello", "media": mid}]})
        assert out["slides"][0]["accent"] == "burgundy"
        assert out["slides"][0]["theme"] == "dark"
        assert out["slides"][0]["media"] == mid

    @pytest.mark.parametrize(
        "href", ["javascript:alert(1)", "//evil.example", "http://plain.example", "relative"]
    )
    def test_links_must_be_site_paths_or_https(self, href):
        with pytest.raises(BlockConfigError) as exc:
            validate_config(
                "hero",
                {
                    "slides": [
                        {"headline": "H", "media": str(uuid.uuid4()), "cta": {"label": "Go", "href": href}}
                    ]
                },
            )
        assert "slides" in exc.value.messages

    def test_unknown_type(self):
        with pytest.raises(BlockConfigError):
            validate_config("carousel", {})

    def test_product_rail_requires_source_specific_fields(self):
        with pytest.raises(BlockConfigError) as exc:
            validate_config("product_rail", {"title": "T", "source": "collection"})
        assert "collection_id" in exc.value.messages
        with pytest.raises(BlockConfigError) as exc:
            validate_config("product_rail", {"title": "T", "source": "manual"})
        assert "product_ids" in exc.value.messages

    def test_rich_text_is_sanitised(self):
        out = validate_config(
            "rich_text",
            {
                "html": '<p onclick="x()">Hi<script>alert(1)</script> '
                '<a href="javascript:x">x</a></p><img src=x>'
            },
        )
        assert "script" not in out["html"]
        assert "onclick" not in out["html"]
        assert "javascript" not in out["html"]
        assert "<img" not in out["html"]

    def test_model_clean_reports_config_errors(self):
        v = page_with([], publish=False)
        block = ContentBlock(page_version=v, type="newsletter", config={})
        with pytest.raises(ValidationError) as exc:
            block.clean()
        assert "config" in exc.value.message_dict


# ---------- model constraints -----------------------------------------------------------------------
class TestConstraints:
    def test_media_alt_required_unless_decorative(self):
        with pytest.raises(IntegrityError), transaction.atomic():
            media(alt="")
        assert media(alt="", is_decorative=True).pk

    def test_media_can_never_be_product_photo(self):
        m = media()
        with pytest.raises(IntegrityError), transaction.atomic():
            MediaAsset.objects.filter(pk=m.pk).update(is_product_photo=True)

    def test_one_published_version_per_page(self):
        v1 = page_with([])
        v2 = PageVersion.objects.create(page=v1.page)
        with pytest.raises(IntegrityError), transaction.atomic():
            PageVersion.objects.filter(pk=v2.pk).update(status="published")

    def test_site_settings_is_a_singleton(self):
        SiteSettings(brand_name="A").save()
        SiteSettings(brand_name="B").save()  # save() pins pk=1
        assert SiteSettings.objects.count() == 1
        assert SiteSettings.objects.get().brand_name == "B"

    def test_published_testimonial_needs_consent(self):
        with pytest.raises(IntegrityError), transaction.atomic():
            QuoteRow.objects.create(name="A", quote="Q", is_published=True)
        now = timezone.now()
        QuoteRow.objects.create(name="A", quote="Q", is_published=True, consent_recorded_at=now)


# ---------- publishing --------------------------------------------------------------------------------
class TestPublishing:
    def test_publish_archives_previous_and_numbers_versions(self):
        v1 = page_with([("newsletter", {"headline": "One"})])
        v2 = services.create_draft(v1.page, from_version=v1)
        assert (v1.version, v2.version) == (1, 2)
        assert v2.blocks.count() == 1
        services.publish_version(v2)
        v1.refresh_from_db()
        assert v1.status == PageVersion.Status.ARCHIVED
        assert selectors.published_version("home").pk == v2.pk

    def test_publish_rejects_invalid_blocks(self):
        v = page_with([("newsletter", {})], publish=False)
        with pytest.raises(services.InvalidBlockConfig) as exc:
            services.publish_version(v)
        assert "newsletter#0" in exc.value.fields
        v.refresh_from_db()
        assert v.status == PageVersion.Status.DRAFT

    def test_publish_queues_revalidation(self, django_capture_on_commit_callbacks):
        v = page_with([("newsletter", {"headline": "Hi"})], publish=False)
        with (
            mock.patch("common.tasks.revalidate_frontend.delay") as delay,
            django_capture_on_commit_callbacks(execute=True),
        ):
            services.publish_version(v)
        delay.assert_called_once_with(["cms:page:home"])

    def test_revalidation_posts_tags_with_secret(self, settings):
        settings.FRONTEND_REVALIDATE_URL = "http://frontend:3000/api/revalidate"
        settings.REVALIDATE_SECRET = "s3cret"
        from common.tasks import revalidate_frontend

        with mock.patch("common.tasks.urllib.request.urlopen") as urlopen:
            urlopen.return_value.__enter__.return_value.status = 200
            revalidate_frontend(["cms:page:home"])
        req = urlopen.call_args.args[0]
        assert req.full_url == "http://frontend:3000/api/revalidate"
        assert req.headers["X-revalidate-secret"] == "s3cret"
        assert b"cms:page:home" in req.data

    def test_revalidation_skipped_without_config(self, settings):
        settings.FRONTEND_REVALIDATE_URL = ""
        from common.tasks import revalidate_frontend

        with mock.patch("common.tasks.urllib.request.urlopen") as urlopen:
            revalidate_frontend(["x"])
        urlopen.assert_not_called()

    def test_scheduled_versions_publish_when_due(self):
        v1 = page_with([("newsletter", {"headline": "Now"})])
        later = services.create_draft(v1.page, from_version=v1)
        services.schedule_version(later, publish_at=timezone.now() + dt.timedelta(minutes=5))
        assert services.publish_due_versions() == 0
        assert services.publish_due_versions(now=timezone.now() + dt.timedelta(minutes=6)) == 1
        later.refresh_from_db()
        assert later.status == PageVersion.Status.PUBLISHED

    def test_schedule_rejects_past_and_non_drafts(self):
        v = page_with([("newsletter", {"headline": "Now"})])
        with pytest.raises(services.InvalidOperation):
            services.schedule_version(v, publish_at=timezone.now() + dt.timedelta(hours=1))
        draft = services.create_draft(v.page)
        with pytest.raises(services.InvalidOperation):
            services.schedule_version(draft, publish_at=timezone.now() - dt.timedelta(minutes=1))


# ---------- resolution --------------------------------------------------------------------------------
class TestResolution:
    def test_missing_references_are_dropped_and_empty_blocks_omitted(self, catalog):
        m = media()
        v = page_with(
            [
                (
                    "hero",
                    {
                        "slides": [
                            {"headline": "Kept", "media": str(m.id)},
                            {"headline": "Gone", "media": str(uuid.uuid4())},
                        ]
                    },
                ),
                ("editorial_split", {"headline": "H", "body": "B", "media": [str(uuid.uuid4())]}),
                (
                    "category_grid",
                    {
                        "title": "T",
                        "items": [
                            {"category_id": str(catalog.root.id), "media": str(m.id)},
                            {"category_id": str(uuid.uuid4()), "media": str(m.id)},
                        ],
                    },
                ),
            ]
        )
        blocks = selectors.page_dict(v)["blocks"]
        assert [b["type"] for b in blocks] == ["hero"]  # editorial (no media) + grid (<2 items) omitted
        assert [s["headline"] for s in blocks[0]["config"]["slides"]] == ["Kept"]
        assert "/cms/" in blocks[0]["config"]["slides"][0]["media"]["url"]

    def test_visibility_window(self):
        v = page_with([("newsletter", {"headline": "Live"}), ("newsletter", {"headline": "Later"})])
        later = v.blocks.get(position=1)
        later.visible_from = timezone.now() + dt.timedelta(days=1)
        later.save()
        assert [b["config"]["headline"] for b in selectors.page_dict(v)["blocks"]] == ["Live"]

    def test_product_rail_sources(self, catalog):
        old = catalog.product("Old Sherwani", days_ago=60, rank=1)
        new = catalog.product("New Sherwani", days_ago=1, rank=2)
        draft = catalog.product("Draft Sherwani", publish=False)
        col = Collection.objects.create(name="Edit", slug="edit", is_published=True)
        CollectionProduct.objects.create(collection=col, product=old, position=0)
        v = page_with(
            [
                ("product_rail", {"title": "New", "source": "new_arrivals"}),
                ("product_rail", {"title": "Col", "source": "collection", "collection_id": str(col.id)}),
                (
                    "product_rail",
                    {
                        "title": "Manual",
                        "source": "manual",
                        "product_ids": [str(new.id), str(draft.id), str(old.id)],
                    },
                ),
            ]
        )
        rails = {b["config"]["title"]: b["config"] for b in selectors.page_dict(v)["blocks"]}
        assert [p["slug"] for p in rails["New"]["products"]] == ["new-sherwani", "old-sherwani"]
        assert [p["slug"] for p in rails["Col"]["products"]] == ["old-sherwani"]
        assert rails["Col"]["collection_slug"] == "edit"
        assert [p["slug"] for p in rails["Manual"]["products"]] == ["new-sherwani", "old-sherwani"]

    def test_unpublished_collection_hides_feature(self):
        m = media()
        col = Collection.objects.create(name="Hidden", slug="hidden", is_published=False)
        v = page_with(
            [
                (
                    "collection_feature",
                    {"collection_id": str(col.id), "layout": "split_left", "media": [str(m.id)]},
                )
            ]
        )
        assert selectors.page_dict(v)["blocks"] == []

    def test_testimonials_only_published(self):
        live = QuoteRow.objects.create(name="A", quote="Q", is_published=True, is_placeholder=True)
        hidden = QuoteRow.objects.create(name="B", quote="Q")
        v = page_with([("testimonials", {"testimonial_ids": [str(hidden.id), str(live.id)]})])
        items = selectors.page_dict(v)["blocks"][0]["config"]["items"]
        assert [i["name"] for i in items] == ["A"]
        assert items[0]["is_placeholder"] is True

    def test_instagram_handle_optional(self):
        ms = [str(media().id) for _ in range(3)]
        v = page_with(
            [("instagram_gallery", {"media": ms}), ("instagram_gallery", {"media": ms, "handle": "@house"})]
        )
        a, b = (x["config"] for x in selectors.page_dict(v)["blocks"])
        assert a["handle"] is None and a["profile_url"] is None
        assert b["profile_url"] == "https://www.instagram.com/house/"

    def test_decorative_media_has_empty_alt(self):
        m = media(alt="", is_decorative=True)
        assert selectors.media_dict(m)["alt"] == ""

    def test_queries_are_batched(self, catalog, django_assert_max_num_queries):
        ms = [media() for _ in range(6)]
        v = page_with(
            [("hero", {"slides": [{"headline": f"S{i}", "media": str(m.id)} for i, m in enumerate(ms[:3])]})]
            + [("editorial_split", {"headline": "H", "body": "B", "media": [str(m.id)]}) for m in ms]
        )
        with django_assert_max_num_queries(8):
            selectors.page_dict(v)


# ---------- API -------------------------------------------------------------------------------------
class TestApi:
    def test_site_settings_seeded_from_env(self, api, settings):
        settings.BRAND_NAME = "ATELIER"
        settings.BRAND_TAGLINE = "Occasion wear, crafted."
        r = api.get("/api/v1/cms/site-settings/")
        assert r.status_code == 200
        body = r.json()
        assert body["brand_name"] == "ATELIER"
        assert body["is_dev_identity"] is True
        assert body["tagline"] == "Occasion wear, crafted."
        assert body["announcement"] == {"enabled": False, "accent": "charcoal", "messages": []}

    def test_site_settings_filters_unsafe_social_links(self, api):
        SiteSettings(
            brand_name="House",
            social_links={"instagram": "https://instagram.com/x", "x": "javascript:alert(1)"},
            announcement={
                "enabled": True,
                "accent": "neon",
                "messages": [{"text": "Hi"}, {"href": "/no-text"}],
            },
        ).save()
        body = api.get("/api/v1/cms/site-settings/").json()
        assert body["social_links"] == [{"network": "instagram", "url": "https://instagram.com/x"}]
        assert body["announcement"] == {
            "enabled": True,
            "accent": "charcoal",
            "messages": [{"text": "Hi", "href": None}],
        }
        assert body["is_dev_identity"] is False

    def test_navigation(self, api, catalog):
        m = media()
        NavigationFeature.objects.create(category_path="kurtas", title="Edit", href="/collections/x", media=m)
        Collection.objects.create(name="Live", slug="live", is_published=True)
        body = api.get("/api/v1/cms/navigation/").json()
        kurtas = next(i for i in body["items"] if i["path"] == "kurtas")
        assert [c["path"] for c in kurtas["children"]] == ["kurtas/kurta-sets"]
        assert kurtas["features"][0]["title"] == "Edit"
        assert body["collections"] == [{"name": "Live", "slug": "live", "accent": "burgundy"}]

    def test_nav_feature_href_must_be_site_path(self):
        with pytest.raises(IntegrityError), transaction.atomic():
            NavigationFeature.objects.create(
                category_path="x", title="T", href="https://evil.example", media=media()
            )

    def test_page(self, api):
        page_with([("newsletter", {"headline": "Letters"})])
        r = api.get("/api/v1/cms/pages/home/")
        assert r.status_code == 200
        body = r.json()
        assert body["version"] == 1 and body["status"] == "published"
        assert body["blocks"][0]["type"] == "newsletter"
        assert body["blocks"][0]["config"]["headline"] == "Letters"

    def test_page_404(self, api):
        assert api.get("/api/v1/cms/pages/nope/").json()["error"]["code"] == "not_found"
        page_with([("newsletter", {"headline": "Draft"})], slug="draft-only", publish=False)
        assert api.get("/api/v1/cms/pages/draft-only/").status_code == 404

    def test_preview_is_staff_only(self, api):
        v = page_with([("newsletter", {"headline": "Draft"})], publish=False)
        url = f"/api/v1/cms/pages/home/?version={v.id}"
        assert api.get(url).status_code == 404
        api.force_authenticate(make_user("cust@example.com"))
        assert api.get(url).status_code == 404
        api.force_authenticate(make_user("staff@example.com", is_staff=True))
        r = api.get(url)
        assert r.status_code == 200
        assert r.json()["status"] == "draft"
        assert r["Cache-Control"] == "private, no-store"
        assert api.get("/api/v1/cms/pages/home/?version=not-a-uuid").status_code == 404


# ---------- newsletter --------------------------------------------------------------------------------
class TestNewsletter:
    def _signup(self, api, email="Asha@Example.com", **extra):
        return api.post("/api/v1/cms/newsletter/", {"email": email, "consent": True, **extra}, format="json")

    def test_double_opt_in(self, api, django_capture_on_commit_callbacks):
        with django_capture_on_commit_callbacks(execute=True):
            r = self._signup(api, source="home")
        assert r.status_code == 202
        sub = NewsletterSubscriber.objects.get()
        assert (sub.email, sub.status, sub.source) == ("asha@example.com", "pending", "home")
        assert len(mail.outbox) == 1
        token = mail.outbox[0].body.split("token=")[1].split()[0]
        r = api.post("/api/v1/cms/newsletter/confirm/", {"token": token}, format="json")
        assert r.json() == {"status": "confirmed"}
        sub.refresh_from_db()
        assert sub.confirmed_at is not None

    def test_consent_required(self, api):
        r = api.post("/api/v1/cms/newsletter/", {"email": "a@example.com", "consent": False}, format="json")
        assert r.status_code == 400
        assert "consent" in r.json()["error"]["fields"]

    def test_no_enumeration_and_no_resend_when_confirmed(self, api, django_capture_on_commit_callbacks):
        NewsletterSubscriber.objects.create(email="asha@example.com", status="confirmed")
        with django_capture_on_commit_callbacks(execute=True):
            r = self._signup(api)
        assert r.status_code == 202 and r.json() == {"status": "pending"}
        assert mail.outbox == []

    def test_bad_and_cross_purpose_tokens(self, api):
        sub = NewsletterSubscriber.objects.create(email="a@example.com")
        assert (
            api.post("/api/v1/cms/newsletter/confirm/", {"token": "nope"}, format="json").status_code == 400
        )
        unsub = services.unsubscribe_token(sub)
        r = api.post("/api/v1/cms/newsletter/confirm/", {"token": unsub}, format="json")
        assert r.json()["error"]["code"] == "invalid_token"
        r = api.post("/api/v1/cms/newsletter/unsubscribe/", {"token": unsub}, format="json")
        assert r.json() == {"status": "unsubscribed"}

    def test_resubscribe_after_unsubscribe(self, api, django_capture_on_commit_callbacks):
        NewsletterSubscriber.objects.create(email="asha@example.com", status="unsubscribed")
        with django_capture_on_commit_callbacks(execute=True):
            self._signup(api)
        assert NewsletterSubscriber.objects.get().status == "pending"
        assert len(mail.outbox) == 1

    def test_csrf_enforced_for_anonymous(self, csrf_api):
        r = csrf_api.post(
            "/api/v1/cms/newsletter/", {"email": "a@example.com", "consent": True}, format="json"
        )
        assert r.status_code == 403
