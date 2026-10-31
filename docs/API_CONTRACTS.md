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

The subscription, quotation and recurring-invoice foundation is implemented. The following payment, discount, portal and reporting additions are owned by Sabareesh. Arya should use only documented endpoints and fields.

## Payments

| Method | Path | Access | Purpose |
| --- | --- | --- | --- |
| `GET` | `/payments/` | Authenticated | Admin/Staff see all; customer sees only own invoice payments |
| `POST` | `/payments/` | Admin/Staff | Record a payment against a confirmed invoice |
| `GET` | `/payments/{id}/` | Owner/Admin/Staff | Payment detail |

Create a payment:

```json
{"invoice":12,"method":"UPI","amount":"500.00","payment_date":"2026-11-01","note":"Received at counter","external_reference":"upi-transaction-id"}
```

`method` is one of `CASH`, `CARD`, `BANK_TRANSFER`, `UPI`, or `OTHER`. Amounts are Decimal strings, must be positive, and cannot exceed the current invoice `balance`. An optional `external_reference` is unique when supplied, preventing duplicate gateway/manual imports. Payments are append-only: multiple partial payments are supported. Each record locks the invoice, updates `amount_paid`, and changes status to `PAID` only once the total is fully settled. Invalid invoice state, excess amount, or duplicate reference returns `400`.

## Discounts

| Method | Path | Access | Purpose |
| --- | --- | --- | --- |
| `GET`, `POST` | `/discounts/` | Admin | List/create discount rules |
| `GET`, `PATCH`, `DELETE` | `/discounts/{id}/` | Admin | Manage a rule |

Example product-specific percentage rule:

```json
{"name":"Workspace launch","discount_type":"PERCENTAGE","value":"10.00","scope":"PRODUCT","products":[4],"minimum_purchase_amount":"100.00","minimum_quantity":1,"starts_on":"2026-11-01","ends_on":"2026-11-30","maximum_uses":100,"is_active":true}
```

Rules may be `FIXED` or `PERCENTAGE`; scope is `SUBSCRIPTION` or `PRODUCT`. Product rules require a non-empty `products` list. Rules are evaluated exactly once when a new invoice is generated, based on its issue date. Dates, amount/quantity thresholds, active state, and remaining `maximum_uses` are enforced under row locks; `DiscountApplication` records the rule and amount for auditability. Discount is capped at eligible subtotal and tax is recalculated after discount. Invoice responses now include `discount_total` and `discount_applications`.

## Customer portal

All portal endpoints require the `CUSTOMER` role. Every queryset is scoped to `request.user`; direct access to another customer’s object returns `404`.

| Method | Path | Purpose |
| --- | --- | --- |
| `GET`, `PATCH` | `/portal/profile/` | Current customer profile (email is read-only) |
| `GET` | `/portal/subscriptions/`, `/portal/subscriptions/{id}/` | Own subscriptions and line/status data |
| `GET` | `/portal/invoices/`, `/portal/invoices/{id}/` | Own invoices, discounts, totals and balance |
| `GET` | `/portal/payments/` | Own payment history |
| `GET` | `/portal/summary/` | Active subscription count, outstanding balance, paid and overdue counts |

## Payment reporting

`GET /reports/payment-summary/` is Admin/Staff-only and returns:

```json
{"received":"500.00","outstanding":"750.00","paid_invoice_count":1,"overdue_invoice_count":1,"discount_total":"30.00"}
```

This is a payment-focused reporting foundation for Aswin’s dashboard aggregation; it does not introduce a competing dashboard endpoint. Hawin QA scenarios: record partial then final payment, reject an overpayment, create a product discount and confirm tax-after-discount, retry billing without a second discount application, and test Customer A against Customer B portal URLs.
