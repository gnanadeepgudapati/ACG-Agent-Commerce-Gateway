from sqlalchemy.ext.asyncio import AsyncSession

from mercora.infra.orm import IdempotencyKeyORM


class IdempotencyRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, key: str) -> str | None:
        row = await self._session.get(IdempotencyKeyORM, key)
        return row.order_id if row else None

    async def record(self, key: str, order_id: str) -> None:
        self._session.add(IdempotencyKeyORM(key=key, order_id=order_id))
        await self._session.commit()
