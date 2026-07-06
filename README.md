# Mercora — Agentic Commerce Gateway (ACG)

> An MCP-fronted commerce orchestration platform that lets autonomous AI agents discover
> products, build carts, and complete real purchases across multiple downstream services —
> through a single, secure, contract-driven API.

![status](https://img.shields.io/badge/status-active-success)
![python](https://img.shields.io/badge/python-3.12-blue)
![framework](https://img.shields.io/badge/framework-FastAPI-009688)
![protocol](https://img.shields.io/badge/protocol-MCP-black)
![license](https://img.shields.io/badge/license-MIT-green)

---

## Table of Contents

- [What is Mercora?](#what-is-mercora)
- [Why it exists](#why-it-exists)
- [Key capabilities](#key-capabilities)
- [System architecture](#system-architecture)
- [How a purchase flows through the system](#how-a-purchase-flows-through-the-system)
- [The MCP tool layer](#the-mcp-tool-layer)
- [REST API reference](#rest-api-reference)
- [Authentication & authorization model](#authentication--authorization-model)
- [Orchestration & the checkout saga](#orchestration--the-checkout-saga)
- [Integration adapters (no point-to-point)](#integration-adapters-no-point-to-point)
- [Testing strategy for agentic variability](#testing-strategy-for-agentic-variability)
- [Observability](#observability)
- [Tech stack](#tech-stack)
- [Project structure](#project-structure)
- [Getting started](#getting-started)
- [Configuration](#configuration)
- [Roadmap](#roadmap)
- [License](#license)

---

## What is Mercora?

**Mercora** is an agentic commerce gateway: a backend platform that exposes an enterprise-grade
REST commerce API, composes several independent downstream services (catalog, inventory,
pricing/tax, payment, shipping, orders) into cohesive business flows, and fronts the whole thing
with a **Model Context Protocol (MCP) server** so that any AI agent — Claude, GPT, or a custom
agent loop — can transact against it using well-typed tools.

The canonical demo: an agent is given a plain-English instruction —

> *"Buy me a medium blue t-shirt under $30 and ship it to my saved address."*

— and Mercora's MCP tools drive the entire transaction end to end: `search_products` →
`add_item` → `checkout`, with inventory reservation, payment authorization, and order
creation orchestrated behind a single call, and automatic rollback if any step fails.

## Why it exists

AI agents are becoming first-class buyers, but most commerce backends are built for human
browsers, not autonomous tool-callers. Mercora is a reference implementation of the missing
middle layer:

- **API-first** — every capability is a documented, versioned REST endpoint before it is a tool.
- **Agent-ready** — a thin MCP shim turns those endpoints into agent-consumable tools with
  concise, deterministic contracts and agent-friendly error semantics.
- **Partner-ready** — third-party integrations are modelled on emerging agentic-commerce
  standards (Agentic Commerce Protocol / universal-commerce-platform concepts) and isolated
  behind adapters, so onboarding a new partner is a new adapter — not a rewrite.

Mercora is deliberately built as a **POC → production** artifact: it starts as something you can
spin up in minutes for a partner proof-of-concept, but ships with the auth, testing, and
observability needed to graduate to production.

## Key capabilities

- **Secure REST commerce API** for catalog, cart, checkout, payment, and order status.
- **Orchestration/composition layer** that fans a single `checkout()` out across inventory,
  pricing/tax, payment, and order services with a **saga + compensation** rollback model.
- **MCP server** exposing purchase capabilities as agent tools with typed schemas.
- **OAuth2 authorization** (client-credentials) with **scoped, per-partner tokens** for
  first-party and third-party consumers.
- **Adapter-based third-party integrations** — pluggable, contract-tested, no brittle
  point-to-point coupling.
- **Agentic test harness** — evaluates non-deterministic agent flows, not just deterministic
  unit outputs.
- **Full observability** — structured logs + OpenTelemetry traces spanning MCP → orchestration
  → every downstream call.

---

## System architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                          AI AGENT (client)                            │
│                Claude · GPT · custom agent loop                       │
└─────────────────────────────────┬────────────────────────────────────┘
                                  │  MCP: tools/list · tools/call
                                  ▼
┌──────────────────────────────────────────────────────────────────────┐
│                        MCP SERVER  (agent shim)                       │
│   search_products · get_product · create_cart · add_item · view_cart  │
│   checkout · get_order_status                                         │
│   → validates args · calls REST API · shapes concise agent responses  │
└─────────────────────────────────┬────────────────────────────────────┘
                                  │  HTTPS + OAuth2 Bearer (scoped JWT)
                                  ▼
┌──────────────────────────────────────────────────────────────────────┐
│                    COMMERCE GATEWAY  (FastAPI, REST)                   │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │  Edge: auth middleware · scope check · rate limit · idempotency │   │
│  └────────────────────────────────────────────────────────────────┘   │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │  ORCHESTRATION / COMPOSITION LAYER                              │   │
│  │  checkout(): reserve inventory → price+tax → authorize payment │   │
│  │              → create order → emit order.created  (saga/rollback)│  │
│  └────────────────────────────────────────────────────────────────┘   │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │  INTEGRATION ADAPTERS  (contract-based, pluggable)             │   │
│  │   CatalogAdapter · PaymentAdapter · ShippingAdapter · TaxAdapter│   │
│  └────────────────────────────────────────────────────────────────┘   │
└──────┬───────────────┬────────────────┬───────────────┬───────────────┘
       ▼               ▼                ▼               ▼
  Catalog Svc    Payment (Stripe   Inventory/Order   Shipping (mock
  (Postgres)      test mode)        (Postgres+Redis)  partner adapter)

        Cross-cutting: Redis (cart sessions + reservation locks) ·
        Postgres (orders, inventory) · OpenTelemetry + OTLP collector ·
        Event bus (order.created / order.failed)
```

Two design decisions carry the architecture:

1. **The orchestration layer with a saga/compensation pattern.** `checkout()` is not a single
   database write. It reserves inventory, computes price and tax, authorizes payment, and creates
   the order — and if any downstream step fails, previously completed steps are compensated
   (reservation released, payment voided). This is what "composition of multiple downstream
   services into cohesive business flows" looks like in practice.

2. **The adapter pattern behind integration contracts.** Every external system sits behind an
   interface. Swapping a payment or shipping provider is a new adapter implementing the same
   contract — never a rewrite of business logic. This is the direct answer to "robust integration
   patterns; avoid brittle point-to-point."

---

## How a purchase flows through the system

```
Agent            MCP Server        Gateway/Orchestrator      Downstream
  │  checkout()      │                    │                       │
  ├─────────────────▶│  POST /checkout    │                       │
  │                  ├───────────────────▶│  1. reserve inventory ├──▶ Inventory
  │                  │                    │  2. price + tax       ├──▶ Tax/Pricing
  │                  │                    │  3. authorize payment ├──▶ Stripe
  │                  │                    │  4. create order      ├──▶ Orders
  │                  │                    │  5. emit order.created├──▶ Event bus
  │                  │◀───────────────────┤  order confirmation   │
  │◀─────────────────┤  concise result    │                       │
  │                  │                    │  (any failure → compensate steps 1–3)
```

Every checkout is **idempotent** (client-supplied idempotency key) so an agent that retries a
tool call after a timeout never double-charges or double-orders.

---

## The MCP tool layer

The MCP server is a thin shim — no business logic lives here. It validates arguments, forwards to
the REST API with a scoped token, and reshapes responses into concise, agent-friendly payloads
(agents pay for tokens, so tool output is trimmed to what the model needs to decide the next step).

| Tool | Purpose | Backing endpoint |
|------|---------|------------------|
| `search_products(query, filters)` | Find products by text + structured filters | `GET /v1/products` |
| `get_product(id)` | Fetch full product detail | `GET /v1/products/{id}` |
| `create_cart()` | Start a new cart session | `POST /v1/carts` |
| `add_item(cart_id, sku, qty)` | Add a line item | `POST /v1/carts/{id}/items` |
| `view_cart(cart_id)` | Inspect current cart + totals | `GET /v1/carts/{id}` |
| `checkout(cart_id, address, payment_token)` | Orchestrated purchase | `POST /v1/checkout` |
| `get_order_status(order_id)` | Track fulfillment | `GET /v1/orders/{id}` |

Tool contracts are aligned to **Agentic Commerce Protocol / universal-commerce-platform**
concepts so the gateway can, in principle, be consumed by external agent platforms without a
bespoke integration per partner.

---

## REST API reference

| Method | Path | Scope | Description |
|--------|------|-------|-------------|
| `GET` | `/v1/products` | `catalog:read` | Search/list products |
| `GET` | `/v1/products/{id}` | `catalog:read` | Product detail |
| `POST` | `/v1/carts` | `cart:write` | Create cart |
| `GET` | `/v1/carts/{id}` | `cart:read` | View cart + totals |
| `POST` | `/v1/carts/{id}/items` | `cart:write` | Add line item |
| `DELETE` | `/v1/carts/{id}/items/{sku}` | `cart:write` | Remove line item |
| `POST` | `/v1/checkout` | `checkout:write` | Orchestrated checkout (saga) |
| `GET` | `/v1/orders/{id}` | `orders:read` | Order status |
| `GET` | `/healthz` · `/readyz` | — | Liveness / readiness |
| `GET` | `/docs` | — | Auto-generated OpenAPI (Swagger UI) |

Interactive OpenAPI docs are served at `/docs` (FastAPI/Swagger) and `/redoc`.

---

## Authentication & authorization model

Mercora uses **OAuth2 client-credentials** with **scoped JWTs**, modelling both first-party and
third-party partner access:

- Each consumer (the first-party MCP server, or an external partner) is a **client** with its own
  `client_id` / `client_secret`.
- Tokens are minted with **least-privilege scopes**. A partner integration might receive only
  `catalog:read` + `checkout:write`, while an internal admin client receives broader scopes.
- Every endpoint declares the scope it requires; the auth middleware rejects tokens missing it.
- Tokens carry a `partner_id` claim used for **per-partner rate limiting and multi-tenant
  isolation** of carts and orders.

Auth can run against an embedded issuer (Authlib/`python-jose`) for local development or a
containerized **Keycloak** for a production-grade identity provider.

---

## Orchestration & the checkout saga

The checkout saga is the heart of the system:

| Step | Action | Compensation on later failure |
|------|--------|-------------------------------|
| 1 | Reserve inventory (Redis lock + Postgres decrement) | Release reservation |
| 2 | Compute price + tax via TaxAdapter | — (idempotent read) |
| 3 | Authorize payment via PaymentAdapter (Stripe) | Void/refund authorization |
| 4 | Persist order (Postgres) | Mark order `failed` |
| 5 | Emit `order.created` event | Emit `order.failed` |

Failures are surfaced to the agent as **structured, actionable errors** (`OUT_OF_STOCK`,
`PAYMENT_DECLINED`, `ADDRESS_INVALID`) rather than raw stack traces, so the agent can adapt its
next tool call.

---

## Integration adapters (no point-to-point)

Every downstream dependency implements a Python `Protocol` interface:

```python
class PaymentAdapter(Protocol):
    async def authorize(self, amount: Money, token: str, idem_key: str) -> Authorization: ...
    async def void(self, authorization_id: str) -> None: ...

class ShippingAdapter(Protocol):
    async def quote(self, address: Address, items: list[LineItem]) -> ShippingQuote: ...
    async def create_shipment(self, order_id: str) -> Shipment: ...
```

Concrete implementations (`StripePaymentAdapter`, `MockShippingAdapter`, `FakeStoreCatalogAdapter`)
are wired in via dependency injection and configuration. Adding a partner = writing an adapter +
a contract test. Business logic never changes.

---

## Testing strategy for agentic variability

Agents are non-deterministic — the same instruction can produce different tool-call orderings —
so testing goes beyond deterministic unit assertions:

- **Unit tests** (`pytest`) — orchestration logic, saga compensation, scope enforcement.
- **Contract / property tests** (`schemathesis`) — fuzz the OpenAPI surface for spec compliance.
- **Integration tests** — full checkout against mocked downstreams + Stripe test mode.
- **Agentic eval harness** — run an LLM through the end-to-end purchase flow **N times** and
  assert on the **final invariant** (order created, correct SKU, amount within budget) rather than
  on an exact tool-call transcript. An **LLM-as-judge** grades whether the agent honored the
  user's constraints (e.g., "under $30"). Results are emitted as a pass-rate table in CI.

This proves the system is robust to the variability the JD explicitly calls out.

---

## Observability

- **Structured JSON logging** with request/trace correlation IDs.
- **OpenTelemetry** traces exported via OTLP: a single checkout produces one trace spanning
  MCP call → gateway → inventory → tax → payment → order, so you can see the entire fan-out and
  its latency budget in one waterfall.
- **Prometheus-style metrics** for request rate, saga success/rollback counts, and per-partner
  usage.

---

## Tech stack

| Layer | Technology |
|-------|------------|
| Language | Python 3.12 |
| API framework | FastAPI + Pydantic v2 |
| MCP | Official MCP Python SDK |
| Auth | OAuth2 client-credentials, scoped JWT (Authlib / Keycloak) |
| Datastores | PostgreSQL (orders, inventory) · Redis (cart sessions, reservation locks) |
| Payments | Stripe (test mode) |
| Catalog | Seeded Postgres catalog / FakeStore adapter |
| Async | `asyncio`, `httpx` for downstream calls |
| Testing | pytest, schemathesis, LLM-as-judge eval harness |
| Observability | OpenTelemetry, structured logging, Prometheus metrics |
| Packaging | Docker + Docker Compose |
| CI | GitHub Actions (lint, type-check, tests, eval gate) |
| Tooling | ruff, mypy, pre-commit |

---

## Project structure

```
mercora/
├── docker-compose.yml
├── pyproject.toml
├── README.md
├── src/
│   └── mercora/
│       ├── api/                 # FastAPI routers (products, carts, checkout, orders)
│       ├── core/                # config, auth middleware, scopes, idempotency
│       ├── orchestration/       # checkout saga + compensation
│       ├── adapters/            # payment, shipping, catalog, tax adapters + Protocols
│       ├── domain/              # Pydantic domain models (Cart, Order, Money, ...)
│       ├── infra/               # db, redis, event bus, telemetry
│       └── mcp_server/          # MCP tool definitions (thin shim over REST)
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── contract/                # schemathesis
│   └── agentic/                 # LLM eval harness + LLM-as-judge
└── .github/workflows/ci.yml
```

---

## Getting started

**Prerequisites:** Docker + Docker Compose, a Stripe test API key.

```bash
# 1. Clone
git clone https://github.com/<you>/mercora.git
cd mercora

# 2. Configure
cp .env.example .env       # add STRIPE_TEST_KEY, JWT secrets, etc.

# 3. Launch the full stack (gateway + MCP + Postgres + Redis + Keycloak + OTel)
docker compose up --build

# 4. Explore the REST API
open http://localhost:8000/docs

# 5. Seed the catalog
docker compose exec gateway python -m mercora.scripts.seed_catalog
```

**Connect an agent to the MCP server** (example MCP client config):

```json
{
  "mcpServers": {
    "mercora": {
      "command": "python",
      "args": ["-m", "mercora.mcp_server"],
      "env": { "MERCORA_API_URL": "http://localhost:8000", "MERCORA_CLIENT_ID": "agent-demo" }
    }
  }
}
```

Then ask the agent: *"Find a blue t-shirt under $30 and buy it, ship to my saved address."*

**Run the tests + agentic eval:**

```bash
pytest tests/unit tests/integration           # deterministic suite
pytest tests/agentic --runs 20                 # agentic eval (pass-rate report)
```

---

## Configuration

| Variable | Description |
|----------|-------------|
| `MERCORA_API_URL` | Base URL of the gateway |
| `STRIPE_TEST_KEY` | Stripe test-mode secret key |
| `JWT_ISSUER` / `JWT_AUDIENCE` | Token issuer/audience |
| `POSTGRES_DSN` | Postgres connection string |
| `REDIS_URL` | Redis connection string |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | Trace collector endpoint |

---

## Roadmap

- [ ] Multi-tenant partner onboarding CLI (mint scoped client + adapter scaffold)
- [ ] Event-driven fulfillment worker consuming `order.created`
- [ ] Streaming MCP tool responses for long-running checkouts
- [ ] Conformance test suite against Agentic Commerce Protocol contracts
- [ ] Rate-limit dashboards per partner

---

## License

MIT — see [LICENSE](LICENSE).
