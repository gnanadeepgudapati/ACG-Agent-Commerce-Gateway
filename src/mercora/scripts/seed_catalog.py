import asyncio

from mercora.core.config import settings
from mercora.infra.db import create_engine_and_sessionmaker, init_db
from mercora.infra.product_repository import ProductRepository
from mercora.infra.seed_data import CATALOG


async def seed() -> None:
    engine, session_maker = create_engine_and_sessionmaker(settings.database_dsn)
    await init_db(engine)
    async with session_maker() as session:
        repo = ProductRepository(session)
        added = 0
        for product in CATALOG:
            if await repo.get(product.id) is None:
                await repo.add(product)
                added += 1
    await engine.dispose()
    print(f"Seeded {added} new product(s); {len(CATALOG) - added} already present.")


def main() -> None:
    asyncio.run(seed())


if __name__ == "__main__":
    main()
