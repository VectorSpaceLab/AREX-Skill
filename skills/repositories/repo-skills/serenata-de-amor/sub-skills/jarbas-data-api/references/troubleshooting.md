# Jarbas data API troubleshooting

Use this guide when the API imports, endpoints, or results do not match expectations.

## Django import and settings failures

### `AppRegistryNotReady: Apps aren't loaded yet`

Typical cause: a script imports Jarbas models, serializers, or views before Django has initialized its app registry.

Safe pattern for an inspection script that needs Django objects:

```python
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "jarbas.settings")
os.environ.setdefault("SECRET_KEY", "dummy-for-local-checks")

import django

django.setup()

from jarbas.chamber_of_deputies.models import Reimbursement
```

Do not call `django.setup()` after importing model modules. If you only need to build URLs or reason about query strings, prefer `scripts/jarbas_api_probe.py`; it is self-contained and does not import Django.

### Missing `SECRET_KEY`

Jarbas settings require `SECRET_KEY`. For local import or `manage.py check` style diagnostics, use a non-secret dummy value:

```bash
DJANGO_SETTINGS_MODULE=jarbas.settings SECRET_KEY=dummy-for-local-checks python manage.py check
```

Real deployment secrets and environment-file setup are owned by `deployment-and-data-ops`; do not place secret values in skill notes, scripts, command history, or issue reports.

### Missing `DJANGO_SETTINGS_MODULE`

Django commands run through `manage.py` normally set the settings module. Standalone Python snippets do not. Set:

```bash
export DJANGO_SETTINGS_MODULE=jarbas.settings
```

or configure it in the script before `django.setup()`.

## PostgreSQL, SQLite, and search-vector problems

### Search works in tests/deployment but not in a lightweight local DB

Jarbas API search relies on PostgreSQL full-text search and PostgreSQL-specific model fields:

- `SearchVectorField`
- `SearchQuery`
- `SearchRank`
- PostgreSQL `JSONField`
- PostgreSQL array support for reimbursement numbers

SQLite is not a faithful backend for these features. Symptoms include migration/import failures, database errors around JSON/search fields, empty search results, or result ordering that does not reflect rank.

Fix route: set up the PostgreSQL-backed Jarbas service and run the search-vector population command through `deployment-and-data-ops`. This sub-skill can explain the API behavior but does not own service setup or data loading.

### Search returns rows but order looks wrong

The queryset annotates a search rank but the intended rank ordering is not assigned back to the queryset in the verified source. If order matters:

1. Confirm that `search_vector` values were populated after loading data.
2. Compare behavior with and without `order_by=probability`.
3. If rank sorting is required, patch the queryset to assign the returned queryset from `order_by('-rank')` and verify under PostgreSQL.

## Empty or unexpected result sets

### Endpoint returns `count: 0`

A zero-count paginated response usually means the route is alive but one of these is true:

- no reimbursement/company/sample data has been loaded;
- filters are too strict;
- the value format does not match stored data;
- `search_vector` is empty or stale;
- pagination offset skips available rows.

Data loading, migrations, sample CSV/XZ files, and service orchestration are owned by `deployment-and-data-ops`.

### Formatted CNPJ/CPF does not match

The reimbursement list cleans formatted `cnpj_cpf` values before filtering. These forms should be equivalent:

```text
cnpj_cpf=07.575.651/0001-59
cnpj_cpf=07575651000159
cnpj_cpf=123.456.789-01
cnpj_cpf=12345678901
```

If a formatted value contains a slash in a URL, ensure it is query-encoded as `%2F` or use the digits-only form. Use:

```bash
python scripts/jarbas_api_probe.py clean-document '07.575.651/0001-59'
```

### Company endpoint returns 404 for a known CNPJ

The company endpoint path must be 14 digits:

```text
/api/company/07575651000159/
```

Jarbas formats the path internally to `07.575.651/0001-59` and looks up `Company.cnpj`. A 404 can mean:

- the company row was not loaded;
- the stored CNPJ is not formatted as expected;
- the path used punctuation or fewer/more than 14 digits;
- the reimbursement used a CPF supplier, not a CNPJ company.

## Boolean query parameter pitfalls

For reimbursement-list booleans, only `1` and `true` are true, case-insensitively. Any other present value is false.

| Query | Meaning |
| --- | --- |
| no parameter | no filter |
| `?suspicions=1` | rows with non-null `suspicions` |
| `?suspicions=true` | rows with non-null `suspicions` |
| `?suspicions=false` | rows with null `suspicions` |
| `?suspicions=0` | rows with null `suspicions` |
| `?suspicions=` | rows with null `suspicions` if the parameter is present |

The same parser is used for `receipt_url` and `in_latest_dataset` when those parameters are read by the view.

`force` on the receipt endpoint is different: any present `force` parameter triggers a forced receipt refetch, including `?force`, `?force=0`, and `?force=false`.

## `receipt_url` versus `has_receipt`

Some public prose names the receipt-presence filter `has_receipt`, but the verified view reads `receipt_url`.

Use:

```text
/api/chamber_of_deputies/reimbursement/?receipt_url=1
/api/chamber_of_deputies/reimbursement/?receipt_url=false
```

If you are debugging an older deployed API, test both names. If `has_receipt` appears to do nothing, it is probably being ignored by the view.

## `in_latest_dataset` failures

The public API prose lists `in_latest_dataset`, and the view attempts to call a queryset method when the parameter is present. The verified model/queryset surface does not provide that method or backing field.

Symptoms:

- server-side `AttributeError` when the parameter is present;
- a 500 response for only the requests that include `in_latest_dataset`;
- no local model field named for latest-dataset availability.

Workaround: omit `in_latest_dataset` unless your deployment has a patch or older schema that supports it. If latest-dataset filtering is required, inspect the deployed schema and implement/restore the queryset method before relying on the filter.

## Multi-value filters do not work as expected

Use one parameter with comma/space-separated values:

```text
/api/chamber_of_deputies/reimbursement/?document_id=42,84+126,+168
```

Do not rely on repeated parameters:

```text
/api/chamber_of_deputies/reimbursement/?document_id=42&document_id=84
```

The view reads a single value for each filter name; repeated parameters can discard earlier values depending on the request parser.

Filters OR values within a parameter and AND different parameters. This means:

```text
?document_id=42,84&year=2016,2017
```

matches rows whose document is 42 or 84 and whose year is 2016 or 2017.

## Pagination surprises

Default page size is 7. If results seem missing:

1. Check the `count` field.
2. Follow `next`/`previous` links or set explicit `limit` and `offset`.
3. Avoid assuming the first page contains all matches.
4. Remember that `order_by=probability` changes which rows appear on the first page.

Example:

```text
/api/chamber_of_deputies/reimbursement/?order_by=probability&limit=50&offset=0
```

## Receipt URL fetch issues

### Receipt detail is slow or raises a network error

The receipt endpoint may perform an HTTP `HEAD` request to the Chamber of Deputies receipt URL when no URL is stored and no prior miss was recorded. Network errors are not swallowed by the model logic.

For deterministic tests, mock the HTTP `HEAD` call. For API use, expect that not every reimbursement has a public receipt URL.

### Receipt detail keeps returning `null`

Check the row state:

- `receipt_url` already set -> endpoint returns it.
- `receipt_fetched=True` and `receipt_url=None` -> endpoint returns `null` without retrying.
- add `?force=1` to retry the network probe.

Remember that any `force` parameter triggers refetch; there is no false value for `force` once present.

## Same-day endpoint returns rows with `city: null`

Same-day logic finds other reimbursements with the same `issue_date` and `applicant_id` as the target document. It then tries to enrich each row with company city/state by formatting `cnpj_cpf` as a CNPJ and looking up a company row.

`city` can be `null` when:

- the supplier uses a CPF rather than a CNPJ;
- the company row was not loaded;
- the company CNPJ format does not match;
- the company lacks both city and state.

## Native/API verification candidates

When validating this sub-skill against a prepared Jarbas environment, useful checks are:

- serializer tests for CNPJ/CPF cleaning and output conversions;
- reimbursement list/detail/receipt tests, including masked CNPJ/CPF, multiple document IDs, date filters, and receipt fetch mocks;
- applicant/subquota distinct-list tests;
- same-day view tests with company city enrichment;
- company detail tests with nested activities;
- `manage.py check` as a settings/import preflight;
- PostgreSQL-backed search-vector cases when the service is available.
