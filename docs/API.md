# Sotooh — API (v1)

Base URL: `/api/v1/` · Auth: session cookie (HttpOnly) + `X-CSRFToken` header on unsafe methods.
Interactive docs: **`/api/docs/`** (Swagger UI) · Schema: **`/api/schema/`** (OpenAPI 3).

Error envelope (all non-2xx):

```json
{ "error": { "code": "validation_error", "message": "...", "details": {"field": ["msg"]} } }
```

## Auth — `/auth/`

| Method | Path                    | Body                          |
| ------ | ----------------------- | ----------------------------- |
| POST   | `/auth/register/`       | `email, password, company_name` → creates user + org + 14-day trial, logs in |
| POST   | `/auth/login/`          | `email, password`             |
| POST   | `/auth/logout/`         | —                             |
| GET    | `/auth/csrf/`           | ensures CSRF cookie           |
| POST   | `/auth/password/reset/` | `email` (never reveals existence) |
| POST   | `/auth/password/reset/confirm/` | `uid, token, password` |
| POST   | `/auth/password/change/`| `current_password, new_password` |
| GET    | `/me/`                  | current user + org + role     |

## Organization — `/organization/`, `/members/`, `/subscription/`

- `GET|PATCH /organization/` (PATCH owner-only; multipart `logo` accepted)
- `GET|POST /members/` (owner-only add; plan `max_users` enforced)
- `GET /subscription/` — current plan/status/expiry

## Products — `/products/`

CRUD + `GET /products/categories/`.
List filters: `category`, `type`, `active`, `search` (ar/en/brand/model/sku), ordering, `page`, `page_size`.

## Customers — `/customers/`

CRUD + special actions:

- `GET /customers/followup_queue/` → `{overdue, today, upcoming}` — the "needs attention" lists
- `POST /customers/{id}/complete_follow_up/`
- `GET /customers/meta/` → source/stage choices
- `POST /customers/{stage}=lost` requires `lost_reason`

## Follow-ups — `/follow-ups/`

CRUD; `POST /follow-ups/` mirrors `scheduled_for` onto the customer;
`POST /follow-ups/{id}/complete/`.

## Quotations — `/quotes/`

- CRUD: `GET list` (filters `status`, `customer`, search, ordering), `POST`, `GET/PUT/PATCH {id}`, `DELETE {id}`
- Create/replace payload:

```json
{
  "customer": "<uuid>",
  "valid_until": "2026-10-01",
  "discount_percent": "5", "tax_percent": "0",
  "notes_ar": "...", "payment_terms": "...", "delivery_terms": "...",
  "items": [
    {"product": null, "description": "تركيب", "quantity": "1", "unit": "job", "unit_price": "400000", "discount_amount": "0"}
  ]
}
```

- `POST /quotes/{id}/status/` — `{"status": "sent|won|lost|..."}` (won/lost update CRM stage)
- `POST /quotes/{id}/pdf/` — generates + stores PDF, returns `{pdf_url}`
- `POST /quotes/{id}/share/` — `{share_url}`; `POST /quotes/{id}/revoke_share/`
- `POST /quotes/{id}/duplicate/`
- Totals are always computed server-side (Decimal); drafts only are editable.

## Public quote — `/public/quotes/{token}/`

`GET`, no auth, rate-limited. Returns customer-facing fields only and records a view
(count, first/last timestamps). 404 when revoked/unknown.

## Dashboard — `/dashboard/`

KPIs: leads/quotes this month, quote & won values, conversion, average quote,
overdue follow-ups, funnel (new→sent→won), needs-attention list, recent quotes.

## Health — outside the API

- `GET /health/` — liveness
- `GET /health/full/` — component statuses (postgres required; redis/s3/clickhouse degrade → HTTP 207)

## Analytics — `/metrics/summary/`

Staff-only event rollup from ClickHouse (`{"available": false}` when CH is down).
