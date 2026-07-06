from typing import Any

import httpx


class MercoraApiError(Exception):
    def __init__(self, status_code: int, detail: Any) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"Mercora API error {status_code}: {detail}")


class MercoraClient:
    def __init__(self, http_client: httpx.AsyncClient) -> None:
        self._http = http_client

    async def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        resp = await self._http.request(method, path, **kwargs)
        if resp.status_code >= 400:
            try:
                detail = resp.json().get("detail", resp.text)
            except ValueError:
                detail = resp.text
            raise MercoraApiError(resp.status_code, detail)
        return resp.json()

    async def search_products(
        self,
        q: str | None = None,
        color: str | None = None,
        size: str | None = None,
        max_price_cents: int | None = None,
    ) -> list[dict[str, Any]]:
        params = {
            k: v
            for k, v in {
                "q": q,
                "color": color,
                "size": size,
                "max_price_cents": max_price_cents,
            }.items()
            if v is not None
        }
        result: list[dict[str, Any]] = await self._request("GET", "/v1/products", params=params)
        return result

    async def get_product(self, product_id: str) -> dict[str, Any]:
        result: dict[str, Any] = await self._request("GET", f"/v1/products/{product_id}")
        return result

    async def create_cart(self) -> dict[str, Any]:
        result: dict[str, Any] = await self._request("POST", "/v1/carts")
        return result

    async def add_item(self, cart_id: str, sku: str, quantity: int) -> dict[str, Any]:
        result: dict[str, Any] = await self._request(
            "POST", f"/v1/carts/{cart_id}/items", json={"sku": sku, "quantity": quantity}
        )
        return result

    async def view_cart(self, cart_id: str) -> dict[str, Any]:
        result: dict[str, Any] = await self._request("GET", f"/v1/carts/{cart_id}")
        return result

    async def checkout(
        self, cart_id: str, address: dict[str, Any], payment_token: str, idempotency_key: str
    ) -> dict[str, Any]:
        result: dict[str, Any] = await self._request(
            "POST",
            "/v1/checkout",
            json={
                "cart_id": cart_id,
                "address": address,
                "payment_token": payment_token,
                "idempotency_key": idempotency_key,
            },
        )
        return result

    async def get_order_status(self, order_id: str) -> dict[str, Any]:
        result: dict[str, Any] = await self._request("GET", f"/v1/orders/{order_id}")
        return result
