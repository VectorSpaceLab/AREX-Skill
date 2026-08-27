# Jarbas API reference

Jarbas exposes read-oriented Django REST Framework endpoints under `/api/`. Anonymous callers can list and retrieve data; writes are not part of this sub-skill.

## Endpoint map

| Task | Method and path | Django route name | Main response |
| --- | --- | --- | --- |
| List reimbursements | `GET /api/chamber_of_deputies/reimbursement/` | `chamber_of_deputies:reimbursement-list` | Paginated `ReimbursementSerializer` results |
| Retrieve one reimbursement | `GET /api/chamber_of_deputies/reimbursement/<document_id>/` | `chamber_of_deputies:reimbursement-detail` | One `ReimbursementSerializer` object |
| Retrieve or fetch receipt URL | `GET /api/chamber_of_deputies/reimbursement/<document_id>/receipt/` | `chamber_of_deputies:reimbursement-receipt` | `{ "url": <string-or-null> }` |
| Same-day reimbursements | `GET /api/chamber_of_deputies/reimbursement/<document_id>/same_day/` | `chamber_of_deputies:reimbursement-same-day` | Paginated same-day reimbursement summaries |
| List applicants | `GET /api/chamber_of_deputies/applicant/` | `chamber_of_deputies:applicant-list` | Paginated distinct applicant IDs and names |
| List subquotas | `GET /api/chamber_of_deputies/subquota/` | `chamber_of_deputies:subquota-list` | Paginated distinct subquota IDs and descriptions |
| Retrieve company | `GET /api/company/<cnpj>/` | `core:company-detail` | One company object with nested activities |
| Service health | `GET /healthcheck/` | `healthcheck` | Empty response if Django and the DB respond |

`<document_id>` is the public reimbursement document identifier, not the database primary key. `<cnpj>` in the company endpoint must be 14 digits; Jarbas formats it internally before looking up the stored `Company.cnpj` value.

## Pagination

Jarbas uses DRF limit/offset pagination:

- Default page size: `7`.
- Pagination controls: `limit=<n>` and `offset=<n>`.
- List responses use the usual envelope: `count`, `next`, `previous`, `results`.
- If you see a valid envelope with `count: 0`, the API route probably works; check data loading, exact filters, and search-vector state before assuming routing is broken.

Example:

```text
GET /api/chamber_of_deputies/reimbursement/?limit=20&offset=40
```

## Reimbursement list filters

`GET /api/chamber_of_deputies/reimbursement/` accepts combinations of these filters. Filters are ANDed across parameter names. Values inside a single comma/space-separated parameter are ORed.

| Parameter | Behavior |
| --- | --- |
| `applicant_id` | Exact match; can contain multiple comma/space-separated applicant IDs. |
| `cnpj_cpf` | Exact match after CNPJ/CPF cleaning. Formatted CNPJ such as `07.575.651/0001-59` becomes `07575651000159`; formatted CPF such as `123.456.789-01` becomes `12345678901`. |
| `document_id` | Exact match; can contain multiple comma/space-separated document IDs. |
| `issue_date_start` | Inclusive lower bound: maps to `issue_date >= value`. Use ISO date strings such as `1970-01-01`. |
| `issue_date_end` | Exclusive upper bound: maps to `issue_date < value`. |
| `month` | Exact numeric month. |
| `subquota_number` | Exact numeric subquota ID. |
| `year` | Exact numeric year. |
| `state` | Case-insensitive exact state/UF match. |
| `suspicions` | Boolean filter over `suspicions` JSON nullness: `1` or `true` means rows with suspicions; any other present value means rows without suspicions. Omit the parameter for no suspicion filter. |
| `receipt_url` | Source-backed boolean filter over whether `receipt_url` is null. `1` or `true` means rows with a receipt URL; any other present value means rows without one. |
| `has_receipt` | Public documentation historically names this parameter, but the current view code reads `receipt_url`. If `has_receipt` is ignored, retry as `receipt_url`. |
| `order_by` | Only `order_by=probability` changes ordering. It sorts non-null probabilities first, highest probability first. Other values are ignored; default model ordering is newest year and issue date first. |
| `in_latest_dataset` | Public documentation lists this boolean parameter, but the current model/queryset surface does not provide the method/field needed by the view. Treat it as stale or deployment-specific; using it on the verified source can raise a server error. |
| `search` | PostgreSQL full-text search over the search vector. Requires PostgreSQL support and populated search vectors. See the search section below. |
| `limit`, `offset` | DRF pagination controls. |

### Multi-value filters

For filter parameters handled by Jarbas's tuple filter, pass multiple values as a single query value separated by commas or spaces:

```text
GET /api/chamber_of_deputies/reimbursement/?document_id=42,84+126,+168
```

After URL decoding, Jarbas splits on commas and spaces, so this matches document IDs `42`, `84`, `126`, and `168`. Repeating the same query parameter (`?document_id=42&document_id=84`) is not the intended interface because the view reads a single value per parameter.

### Difficult filtered reimbursement URL

Use this pattern for a request with multiple document IDs, a formatted CNPJ, only suspicious rows, and probability ordering:

```text
GET /api/chamber_of_deputies/reimbursement/?document_id=111111,222222&cnpj_cpf=07.575.651%2F0001-59&suspicions=true&order_by=probability
```

Equivalent normalized form:

```text
GET /api/chamber_of_deputies/reimbursement/?document_id=111111,222222&cnpj_cpf=07575651000159&suspicions=true&order_by=probability
```

The API cleans the CNPJ before filtering. `suspicions=true` means `suspicions` is not null; `order_by=probability` places non-null probabilities ahead of null values and then sorts descending by probability.

You can build and inspect the same URL without contacting a server:

```bash
python scripts/jarbas_api_probe.py build-reimbursement \
  --document-id 111111,222222 \
  --cnpj-cpf '07.575.651/0001-59' \
  --suspicions true \
  --order-by probability \
  --explain
```

Run the command from this sub-skill directory, or pass the script path explicitly.

## Search behavior

`search=<term>` uses PostgreSQL full-text search with the Portuguese configuration. The search vector is built from these fields:

- high weight: `congressperson_name`, `supplier`, `cnpj_cpf`, `party`
- medium weight: `state`, `receipt_text`
- lower weights: `passenger`, `leg_of_the_trip`, `subquota_description`, `subquota_group_description`

Important caveats:

1. Search is only trustworthy after a PostgreSQL-backed database has the search-vector maintenance command run against loaded data.
2. SQLite is not an adequate substitute for the `SearchVectorField`, `SearchQuery`, `SearchRank`, or PostgreSQL `JSONField` behavior.
3. The current queryset annotates a rank for search, but the intended `order_by('-rank')` is not assigned back to the queryset. If you need rank-sorted results, verify the deployed behavior or patch the queryset.
4. If `order_by=probability` is also present, probability ordering is applied after search filtering.

## Reimbursement detail response

`GET /api/chamber_of_deputies/reimbursement/<document_id>/` returns one object serialized from the reimbursement model. Notable conversions:

- Database `Decimal` values are converted to JSON numbers or `null`: `total_value`, `total_net_value`, `document_value`, `remark_value`, and `probability`.
- Stored `numbers` are exposed as `all_numbers`, a list of integers.
- `receipt_fetched` and `receipt_url` are not top-level fields; they are nested as `receipt: { "fetched": <bool>, "url": <string-or-null> }`.
- `rosies_tweet` is a tweet URL if a related tweet row exists; otherwise it is `null`.
- Detail retrieval does not attempt to fetch a missing receipt URL. Use the receipt endpoint for that.

## Receipt endpoint

`GET /api/chamber_of_deputies/reimbursement/<document_id>/receipt/` returns:

```json
{"url": "http://example.invalid/receipt.pdf"}
```

or:

```json
{"url": null}
```

Behavior:

- If `receipt_url` is already stored, Jarbas returns it without a network probe.
- If `receipt_fetched` is true and there is no URL, Jarbas returns `null` without retrying.
- If no prior fetch is recorded, Jarbas builds the expected Chamber of Deputies receipt URL, performs an HTTP `HEAD`, stores `receipt_fetched=True`, stores the URL only for 2xx/3xx responses, and saves the row.
- Adding any `force` query parameter, for example `?force=1` or `?force`, retries even when a previous missing receipt was recorded.

## Same-day reimbursement endpoint

`GET /api/chamber_of_deputies/reimbursement/<document_id>/same_day/` lists other reimbursements with the same `issue_date` and `applicant_id` as the target `document_id`. It excludes the target document itself.

Each result contains:

- `applicant_id`
- `city` from the matching company, formatted as `City, UF`, or `null`
- `document_id`
- `subquota_number`
- `subquota_description`
- `supplier`
- `total_net_value` as a JSON number or `null`
- `year`

Company lookup for `city` formats the reimbursement `cnpj_cpf` as a CNPJ and searches companies by that formatted value. CPF suppliers or missing company rows produce `city: null`.

## Applicant and subquota endpoints

Applicant endpoint:

```text
GET /api/chamber_of_deputies/applicant/
GET /api/chamber_of_deputies/applicant/?q=doe
```

Response rows contain `applicant_id` and `congressperson_name`. Results are distinct by those fields and ordered by `congressperson_name`. `q` applies case-insensitive containment to the name.

Subquota endpoint:

```text
GET /api/chamber_of_deputies/subquota/
GET /api/chamber_of_deputies/subquota/?q=meal
```

Response rows contain `subquota_number` and `subquota_description`. Results are distinct by those fields and ordered by `subquota_description`. `q` applies case-insensitive containment to the description.

## Company endpoint

```text
GET /api/company/07575651000159/
```

The path must contain exactly 14 digits. Jarbas formats the value as `07.575.651/0001-59` internally before looking up `Company.cnpj`.

The response excludes the database `id` and includes nested `main_activity` and `secondary_activity` arrays. Activity objects contain `code` and `description`.

A non-existent company returns `404`.
