from mercora.infra.seed_data import CATALOG


def test_all_ids_unique() -> None:
    ids = [p.id for p in CATALOG]
    assert len(ids) == len(set(ids))


def test_catalog_is_non_trivial() -> None:
    assert len(CATALOG) >= 8


def test_canonical_demo_item_exists() -> None:
    """Guards the README demo: 'a medium blue t-shirt under $30'."""
    matches = [
        p
        for p in CATALOG
        if p.attributes.get("color") == "blue"
        and p.attributes.get("size") == "M"
        and p.price.amount_cents < 3000
    ]
    assert matches
