"""Staff roles -> Django model permissions. Synced after every migrate (idempotent).

Permissions are listed as "<app_label>.<model>" (grants add/change/delete/view) or
"<app_label>.<model>:view" (read-only). Models that don't exist yet are skipped, so
roles grow automatically as later phases add apps.
"""

from django.apps import apps as global_apps

CATALOGUE = [
    "catalog.product",
    "catalog.productvariant",
    "catalog.productmedia",
    "catalog.productspecification",
    "catalog.sizechart",
    "catalog.sizechartrow",
    "catalog.measurementdefinition",
    "catalog.brand",
    "catalog.completethelook",
    "catalog.collectionproduct",
    "categories.category",
    "categories.collection",
    "attributes.fabric",
    "attributes.occasion",
    "attributes.fit",
    "attributes.pattern",
    "attributes.embroiderytype",
    "attributes.sleevetype",
    "attributes.colour",
    "attributes.sizesystem",
    "attributes.size",
]
INVENTORY = [
    "inventory.stocklocation",
    "inventory.stocklevel",
    "inventory.stockmovement:view",
    "inventory.stockreservation:view",
    "inventory.lowstockalert",
]
CUSTOMERS_VIEW = [
    "customers.customerprofile:view",
    "customers.address:view",
    "customers.measurementprofile:view",
    "accounts.user:view",
]
PRICING = ["pricing.taxclass", "pricing.taxrule"]

ROLES: dict[str, list[str]] = {
    "Owner": CATALOGUE
    + INVENTORY
    + PRICING
    + ["customers.customerprofile", "customers.address", "customers.measurementprofile", "accounts.user"],
    "Store Manager": CATALOGUE + INVENTORY + CUSTOMERS_VIEW + [p + ":view" for p in PRICING],
    "Catalogue Manager": [*CATALOGUE, "inventory.stocklevel:view"],
    "Inventory Manager": INVENTORY + [p + ":view" for p in CATALOGUE if p.startswith("catalog.product")],
    "Order Operations": [*CUSTOMERS_VIEW, "inventory.stocklevel:view"],
    "Customer Support": [*CUSTOMERS_VIEW, "customers.address", "customers.measurementprofile"],
    "Content Editor": ["catalog.productmedia", "categories.collection", "categories.category:view"],
    "Marketing": ["categories.collection", "catalog.product:view"],
    "Analyst": [p.split(":")[0] + ":view" for p in CATALOGUE + INVENTORY + CUSTOMERS_VIEW],
}


def _codenames(spec: str) -> tuple[str, str, list[str]]:
    target, _, mode = spec.partition(":")
    app_label, model = target.split(".")
    actions = ["view"] if mode == "view" else ["add", "change", "delete", "view"]
    return app_label, model, [f"{a}_{model}" for a in actions]


def sync_roles(apps=global_apps) -> None:
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")
    for role, specs in ROLES.items():
        group, _ = Group.objects.get_or_create(name=role)
        perms = []
        for spec in specs:
            app_label, _model, codenames = _codenames(spec)
            perms.extend(Permission.objects.filter(content_type__app_label=app_label, codename__in=codenames))
        group.permissions.set(perms)


def sync_roles_after_migrate(sender, **kwargs) -> None:
    """post_migrate fires per app after its permissions exist; re-sync after each local app (idempotent)."""
    if not getattr(sender, "name", "").startswith("apps."):
        return
    sync_roles()
