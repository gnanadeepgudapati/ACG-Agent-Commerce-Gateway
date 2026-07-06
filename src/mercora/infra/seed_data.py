from mercora.domain.money import Money
from mercora.domain.product import Product


def _usd(cents: int) -> Money:
    return Money(amount_cents=cents, currency="USD")


CATALOG: list[Product] = [
    Product(
        id="TSHIRT-BLUE-S",
        name="Classic Tee",
        description="A soft cotton crew-neck t-shirt.",
        price=_usd(2500),
        attributes={"color": "blue", "size": "S"},
        stock_qty=20,
    ),
    Product(
        id="TSHIRT-BLUE-M",
        name="Classic Tee",
        description="A soft cotton crew-neck t-shirt.",
        price=_usd(2500),
        attributes={"color": "blue", "size": "M"},
        stock_qty=20,
    ),
    Product(
        id="TSHIRT-BLUE-L",
        name="Classic Tee",
        description="A soft cotton crew-neck t-shirt.",
        price=_usd(2500),
        attributes={"color": "blue", "size": "L"},
        stock_qty=20,
    ),
    Product(
        id="TSHIRT-RED-M",
        name="Classic Tee",
        description="A soft cotton crew-neck t-shirt.",
        price=_usd(2400),
        attributes={"color": "red", "size": "M"},
        stock_qty=15,
    ),
    Product(
        id="TSHIRT-BLACK-M",
        name="Classic Tee",
        description="A soft cotton crew-neck t-shirt.",
        price=_usd(2400),
        attributes={"color": "black", "size": "M"},
        stock_qty=15,
    ),
    Product(
        id="HOODIE-GREY-M",
        name="Pullover Hoodie",
        description="A midweight fleece hoodie.",
        price=_usd(4500),
        attributes={"color": "grey", "size": "M"},
        stock_qty=10,
    ),
    Product(
        id="JEANS-BLUE-32",
        name="Straight Fit Jeans",
        description="Durable denim jeans, straight fit.",
        price=_usd(6000),
        attributes={"color": "blue", "size": "32"},
        stock_qty=8,
    ),
    Product(
        id="SNEAKERS-WHITE-10",
        name="Court Sneakers",
        description="Everyday low-top sneakers.",
        price=_usd(8000),
        attributes={"color": "white", "size": "10"},
        stock_qty=6,
    ),
    Product(
        id="CAP-BLACK-OS",
        name="Baseball Cap",
        description="Adjustable cotton baseball cap.",
        price=_usd(1800),
        attributes={"color": "black", "size": "OS"},
        stock_qty=25,
    ),
    Product(
        id="SOCKS-WHITE-OS",
        name="Crew Socks (3-Pack)",
        description="Cushioned cotton-blend crew socks.",
        price=_usd(1200),
        attributes={"color": "white", "size": "OS"},
        stock_qty=30,
    ),
]
