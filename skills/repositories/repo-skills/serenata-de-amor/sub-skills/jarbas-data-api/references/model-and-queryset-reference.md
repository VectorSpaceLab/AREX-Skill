# Model, serializer, and queryset reference

This reference distills the API-facing model and queryset behavior needed to reason about Jarbas results without reopening the source checkout.

## Reimbursement model field families

A reimbursement is the central API object and is publicly addressed by `document_id`.

| Family | Fields and meaning |
| --- | --- |
| Identity and update | `document_id` public document identifier; `last_update` auto-updated timestamp; `year`; `applicant_id`. |
| Congressional person | `congressperson_id`, `congressperson_name`, `congressperson_document`, `party`, `state`, `term_id`, `term`. Many of these can be null. |
| Subquota/category | `subquota_number`, `subquota_description`, `subquota_group_id`, `subquota_group_description`. |
| Supplier/document | `supplier`, `cnpj_cpf`, `document_type`, `document_number`, `document_value`, `issue_date`, `month`, `batch_number`. `cnpj_cpf` is stored as digits when loaded through the expected pipeline. |
| Monetary values | `total_value`, `total_net_value`, `document_value`, `remark_value`, and `installment`. Decimal values are rendered as JSON numbers by the API serializers. |
| Reimbursement numbers | `numbers` is a PostgreSQL array of string values. The API exposes it as `all_numbers`, converted to integers and omitting `None`. |
| Travel details | `passenger`, `leg_of_the_trip`. |
| Rosie suspicion data | `probability` and `suspicions` JSON. `probability` can be null when no suspicion score was loaded. A related tweet, when present, is exposed as `rosies_tweet`. Rosie generation/loading is owned by `rosie-suspicion-pipeline` and `deployment-and-data-ops`; this sub-skill only explains API behavior once values exist. |
| Receipt/search | `receipt_fetched`, `receipt_url`, `receipt_text`, `search_vector`. The serializer hides the first two as top-level fields and exposes them as the nested `receipt` object. `search_vector` is PostgreSQL full-text search state and is not part of normal API output. |

Database-specific fields include PostgreSQL `ArrayField`, `JSONField`, `SearchVectorField`, and a GIN index over the search vector. SQLite can be useful for limited import or parser checks but is not equivalent for full API behavior.

Default model ordering is newest data first: descending `year`, then descending `issue_date`.

## Company and Activity model field families

`Company` records Brazilian company registration and location data. The company endpoint accepts a 14-digit CNPJ path value but looks up the stored formatted CNPJ.

| Family | Fields and meaning |
| --- | --- |
| Identity | `cnpj` stored in formatted CNPJ form, for example `07.575.651/0001-59`. |
| Registration | `opening`, `legal_entity`, `trade_name`, `name`, `type`, `status`, `situation`, `situation_reason`, `situation_date`, `special_situation`, `special_situation_date`, `responsible_federative_entity`. |
| Activities | `main_activity` and `secondary_activity` many-to-many relations to `Activity`. Activity rows serialize as `{ "code": ..., "description": ... }`. |
| Address/contact | `address`, `number`, `additional_address_details`, `neighborhood`, `zip_code`, `city`, `state`, `email`, `phone`. |
| Geocoding/update | `latitude`, `longitude`, `last_updated`. |

`CompanySerializer` excludes the database `id` and includes nested activities.

## Serializer conversions and output contracts

### `ReimbursementSerializer`

Used by the reimbursement list and detail endpoints.

- Excludes database `id`, raw `numbers`, raw `receipt_fetched`, and raw `receipt_url`.
- Adds `all_numbers`: `numbers` converted to integer values.
- Converts `total_value`, `total_net_value`, `document_value`, `remark_value`, and `probability` from Decimal to JSON float or `null`.
- Adds `receipt`: `{ "fetched": <receipt_fetched>, "url": <receipt_url> }`.
- Adds `rosies_tweet`: related tweet URL when present, otherwise `null`.
- Leaves most string/date/integer fields in their normal Django REST Framework representation.

### `ReceiptSerializer`

Used only by the receipt endpoint. It returns `url`, sourced from `receipt_url`, after the view has optionally called receipt-fetching logic.

### `SameDayReimbursementSerializer`

Used by the same-day endpoint. It returns a compact summary:

- `applicant_id`
- `city`
- `document_id`
- `subquota_number`
- `subquota_description`
- `supplier`
- `total_net_value` as float or `null`
- `year`

`city` is looked up by formatting the reimbursement `cnpj_cpf` as a CNPJ and finding a matching company. Missing companies, CPF suppliers, or companies without city/state return `null`.

### `ApplicantSerializer` and `SubquotaSerializer`

These are simple distinct-list serializers:

- Applicant: `applicant_id`, `congressperson_name`.
- Subquota: `subquota_number`, `subquota_description`.

### `CompanySerializer`

Returns company fields except database `id`, with nested `main_activity` and `secondary_activity` arrays.

## CNPJ/CPF helpers

### `clean_cnpj_cpf(value)`

The reimbursement list view cleans the `cnpj_cpf` query parameter before filtering. The cleaning logic scans for CPF/CNPJ-looking substrings of the expected formatted lengths and strips non-digits from those substrings.

Examples:

| Input | Cleaned output |
| --- | --- |
| `12.345.678/9012-34` | `12345678901234` |
| `12345678901234` | `12345678901234` |
| `020.020.020-02` | `02002002002` |
| `02002002002` | `02002002002` |

Unmasked digit-only values are already valid and stay unchanged. If a string contains multiple formatted documents, each matching substring is cleaned in place.

### `format_cnpj(cnpj)`

Formats the first 14 characters of a value as `NN.NNN.NNN/NNNN-NN`. Jarbas uses this when:

- retrieving a company from `/api/company/<14 digits>/`; and
- enriching same-day reimbursement rows with company city/state.

Do not pass an 11-digit CPF to logic that expects a CNPJ format; it will not correspond to a valid stored company CNPJ.

## Reimbursement queryset methods

### `same_day_as(document_id)`

Returns reimbursements whose `issue_date` and `applicant_id` match the target `document_id`, excluding the target document itself. If no target document exists, the result is empty. If duplicate rows share a document ID, the method effectively uses the set of matching dates and applicants.

### `order_by_probability()`

Orders rows so that non-null `probability` values come first, then highest probability first. Rows without probabilities are left after scored rows. This is used only when the list endpoint receives `order_by=probability`.

### `list_distinct(field, order_by_field, query=None)`

Used by applicant and subquota endpoints. It optionally filters `order_by_field__icontains=query`, selects only the requested pair of fields, orders by the text field, and returns distinct pairs. Distinctness is by both selected fields, so two names/descriptions with different IDs remain separate.

### `suspicions(boolean)`

Filters on JSON nullness:

- `True` -> `suspicions IS NOT NULL`.
- `False` -> `suspicions IS NULL`.

The boolean parser in the view treats only `1` and `true` (case-insensitive) as true. Any other present value is false.

### `has_receipt_url(boolean)`

Filters on `receipt_url` nullness:

- `True` -> `receipt_url IS NOT NULL`.
- `False` -> `receipt_url IS NULL`.

The view names the public query parameter `receipt_url`; some public prose refers to `has_receipt`. When debugging, prefer `receipt_url` for this source version.

### `tuple_filter(**kwargs)`

Used for ordinary exact filters. Behavior:

1. Renames selected keys: `issue_date_start` -> `issue_date__gte`; `issue_date_end` -> `issue_date__lt`; `state` -> `state__iexact`.
2. Splits each string value on commas and spaces.
3. ORs values within each parameter.
4. ANDs different parameters by applying each filter in sequence.

Example:

```text
?document_id=42,84+126,+168&state=sp
```

becomes logically:

```text
(document_id = 42 OR document_id = 84 OR document_id = 126 OR document_id = 168)
AND state ILIKE EXACT 'sp'
```

### `search_vector(search_term)`

Uses PostgreSQL `SearchQuery(search_term, config='portuguese')` and `SearchRank` against `search_vector`, then filters rows matching the query. Full correctness requires PostgreSQL and populated search-vector data.

Known debugging nuance: the code computes `self.order_by('-rank')` when it thinks the queryset was not ordered, but does not assign the returned queryset. That means rank ordering may not actually take effect in the verified source. If result order matters, explicitly test the deployed service or patch the queryset.

### `in_latest_dataset`

The public API prose lists an `in_latest_dataset` boolean filter and the view attempts to call it when the parameter is present. In the verified source surface, the model field and queryset method are absent. If this parameter raises an error or has no effect, treat it as a stale API contract from an earlier schema and remove the parameter unless your deployment has restored support.

## Receipt URL internals

Jarbas builds receipt URLs from reimbursement fields:

- Electronic receipt (`document_type == 4`):

  ```text
  https://www.camara.leg.br/cota-parlamentar/nota-fiscal-eletronica?ideDocumentoFiscal=<document_id>
  ```

- Other receipt types:

  ```text
  http://www.camara.gov.br/cota-parlamentar/documentos/publ/<applicant_id>/<year>/<document_id>.pdf
  ```

`get_receipt_url(force=False, bulk=False)` behavior:

1. If `receipt_url` already exists, return it immediately.
2. If `receipt_fetched` is true and `force` is false, return `None` without network access.
3. Otherwise, build the expected URL and make an HTTP `HEAD` request.
4. Status codes from 200 through 399 are considered existing receipts; other status codes leave `receipt_url` null.
5. `receipt_fetched` is set true.
6. With `bulk=True`, the object is returned unsaved for caller-managed bulk persistence. Otherwise the row is saved.

Receipt network errors propagate unless the caller handles them.
