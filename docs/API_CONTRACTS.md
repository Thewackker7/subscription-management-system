# API Contracts - Backend Foundation

Base URL: `/api/v1`. Requests and responses are JSON. Protected routes require `Authorization: Bearer <access_token>`.

## Authentication and users

| Method | Path | Access | Purpose |
| --- | --- | --- | --- |
| `GET` | `/health/` | Public | Service readiness check |
| `POST` | `/auth/register/` | Public | Register a Customer account |
| `POST` | `/auth/login/` | Public | Obtain JWT access and refresh tokens |
| `POST` | `/auth/token/refresh/` | Public | Refresh an access token |
| `POST` | `/auth/password-reset/` | Public | Request a password-reset email without revealing account existence |
| `POST` | `/auth/password-reset/confirm/` | Public | Consume an expiring, single-use reset token |
| `POST` | `/users/staff/` | Admin | Create a Staff account |

`POST /auth/register/` request:

```json
{"email":"customer@example.com","password":"StrongPass!","first_name":"Asha","last_name":"Nair"}
```

The password must contain at least 9 characters, one uppercase letter, one lowercase letter, and one special character. Emails are normalized to lowercase and are unique. Registration always creates the `CUSTOMER` role; callers cannot choose a privileged role.

`POST /auth/login/` request and success response:

```json
{"email":"customer@example.com","password":"StrongPass!"}
```

```json
{"refresh":"<jwt>","access":"<jwt>","user":{"id":1,"email":"customer@example.com","role":"CUSTOMER"}}
```

`POST /users/staff/` accepts the same request body as registration and returns the created user with `role: "STAFF"`. It is forbidden for Staff and Customers.

`GET /health/` response:

```json
{"status":"ok"}
```

Password reset request:

```json
{"email":"customer@example.com"}
```

This always returns `202` with `{"detail":"If the email is registered, password reset instructions have been sent."}`. Configure SMTP with the environment fields in `backend/.env.example`; the server does not expose reset tokens in its API response. Confirm a reset with the `uid` and `token` from the emailed link:

```json
{"uid":"<uid>","token":"<token>","password":"NewPassword1!"}
```

## Catalog

All catalog endpoints below are Admin-only in this foundation. List endpoints are `GET`; detail endpoints append `/{id}/`. Create with `POST` to a list endpoint, replace/update with `PUT`/`PATCH` to a detail endpoint, and delete with `DELETE` to a detail endpoint.

| Resource | Path | Fields for create/update |
| --- | --- | --- |
| Product | `/catalog/products/` | `name`, `product_type` (`SERVICE`, `GOODS`, `DIGITAL`), `sales_price`, `cost_price`, `notes`, `is_active` |
| ProductVariant | `/catalog/variants/` | `product`, `label`, `extra_price`, `sku`, `is_active` |
| Plan | `/catalog/plans/` | `name`, `billing_interval` (`DAILY`, `WEEKLY`, `MONTHLY`, `YEARLY`), `interval_count`, `minimum_quantity`, `available_from`, `available_until`, `allow_pause`, `allow_renewal`, `is_active` |
| TaxRule | `/catalog/taxes/` | `name`, `rate`, `is_active`, `available_from`, `available_until` |

Example product create request:

```json
{"name":"Cloud Workspace","product_type":"SERVICE","sales_price":"1000.00","cost_price":"100.00","notes":"Base package","is_active":true}
```

Example variant response (computed `sales_price` is read-only):

```json
{"id":1,"product":1,"label":"Odoo brand","extra_price":"560.00","sales_price":"1560.00","sku":"ODOO-1","is_active":true}
```

Dates use ISO 8601 (`YYYY-MM-DD`). Monetary fields are decimal strings, never floats. A plan or tax rule with both availability dates must have `available_until >= available_from`; tax rates are constrained to `0.00` through `100.00`.

## Subscriptions and quotations

Admin and Staff can create and manage subscriptions and quotations. Customers may `GET` only their own subscriptions; another customer’s detail URL returns `404`.

| Method | Path | Access | Purpose |
| --- | --- | --- | --- |
| `GET`, `POST` | `/subscriptions/` | GET: authenticated; POST: Admin/Staff | List/create subscriptions |
| `GET`, `PATCH`, `DELETE` | `/subscriptions/{id}/` | GET: owner/Admin/Staff; write: Admin/Staff | Inspect/manage subscription |
| `POST` | `/subscriptions/{id}/transition/` | Admin/Staff | Advance lifecycle status |
| `POST` | `/subscriptions/{id}/pause/`, `/resume/`, `/renew/` | Admin/Staff | Plan-controlled lifecycle actions |
| `GET`, `POST` | `/subscriptions/quotation-templates/` | Admin/Staff | Reusable plan/product-line templates |
| `GET`, `POST` | `/subscriptions/quotations/` | Admin/Staff | Manage quotations |
| `POST` | `/subscriptions/quotations/{id}/convert/` | Admin/Staff | Convert one valid quotation exactly once |

Create a subscription with line snapshots. `unit_price` and `description` may be omitted: the current product/variant price and name are copied. Later catalog changes do not change saved subscription/invoice prices.

```json
{"customer":7,"plan":3,"start_date":"2026-11-01","expiry_date":"2027-10-31","payment_terms_days":15,"lines":[{"product":4,"variant":8,"quantity":2,"tax_rule":1}]}
```

Line quantity must meet the plan’s `minimum_quantity`; a variant must belong to its product. Lifecycle transitions are strictly `DRAFT -> QUOTATION -> CONFIRMED -> ACTIVE -> CLOSED`. `pause` requires `allow_pause`; `renew` requires a closed subscription with `allow_renewal` and a later expiry date.

Create a quotation from explicit lines, or use an active template (which supplies its plan, line items, and default validity):

```json
{"customer":7,"template":2}
```

```json
{"start_date":"2026-11-01","expiry_date":"2027-10-31","payment_terms_days":15}
```

The conversion call returns `201` with the new subscription, returns `400` for expired/invalid/repeated conversions, and is protected by a database one-to-one link.

## Billing and invoices

| Method | Path | Access | Purpose |
| --- | --- | --- | --- |
| `POST` | `/billing/generate/` | Admin/Staff | Generate invoice(s) due on or before `as_of` |
| `GET` | `/billing/invoices/` | Authenticated | Staff/Admin all invoices; customers only their own |
| `GET` | `/billing/invoices/{id}/` | Owner/Admin/Staff | Invoice with immutable line snapshots |
| `POST` | `/billing/invoices/{id}/confirm/`, `/cancel/`, `/send/` | Admin/Staff | Safe invoice actions |
| `GET` | `/billing/invoices/{id}/print_ready/` | Admin/Staff | Print-ready invoice JSON |

Generate a specific subscription or all due subscriptions:

```json
{"subscription_id":12,"as_of":"2026-11-01"}
```

The response has `generated` and `existing` arrays. Billing supports daily, weekly, monthly and yearly plan intervals; monthly/yearly dates are clamped safely (for example, 31 January plus one month is 28 February). Generation uses an atomic transaction, row locking where supported, and a unique database constraint over subscription and billing-period dates. Retried requests return the existing invoice rather than double-billing.

Invoices start as `DRAFT`; they may become `CONFIRMED`, `PAID` (reserved for Sabareesh’s payment module), or `CANCELLED`. A confirmed invoice can be sent/marked sent. Cancellation is rejected when payment allocation exists. Invoice `amount_paid`, `balance`, and `discount_total` deliberately remain compatible with Sabareesh’s payment/discount ownership.

## Current scope and coordination

The subscription, quotation and recurring-invoice foundation is implemented. Sabareesh owns payment recording, discount-rule behavior, and portal API behavior; no payment or discount endpoint has been duplicated here. Arya should use only documented endpoints and fields. Hawin can use the workflow tests as baseline QA scenarios: create template/quotation, convert once, activate, generate invoice, retry generation, and verify customer isolation.
