# Management commands reference

Run these commands from a Serenata de Amor checkout with Django dependencies installed and environment variables configured. In Docker, prefix commands with `docker compose run --rm django` and use container paths such as `/mnt/data/...` for mounted sample data.

## Safety classes

- **Check-only**: no data mutation or external service call expected.
- **Local data mutation**: writes to the configured database; confirm `DATABASE_URL`.
- **Network read/write**: performs HTTP/API calls or publishes externally; require authorization.
- **Destructive/rebuild**: deletes or replaces existing rows; use backups and explicit target confirmation.
- **Reference-only**: historical or production/credential-bound workflow; do not run as generic setup.

## Command table

| Command | Safety | Prerequisites | Main effect | Key options | Expected signal |
| --- | --- | --- | --- | --- | --- |
| `check` | Check-only | Django imports, `SECRET_KEY`; DB URL can be safe check default | Django system checks | standard Django flags | `System check identified no issues` or actionable settings/import errors |
| `migrate` | Local data mutation | Intended DB reachable; migration permissions | Creates/updates DB schema | standard Django migration flags | Applied migrations or `No migrations to apply` |
| `reimbursements <dataset>` | Local data mutation; destructive with `--drop-all` | Migrated DB; CSV dataset | Bulk-creates `Reimbursement` rows | `--drop-all`, `--batch-size` | `Current count: ... Reimbursements` |
| `companies <dataset>` | Local data mutation; destructive with `--drop-all` | Migrated DB; `.xz` company CSV; Python `lzma` | Creates `Company` and `Activity` rows | `--drop-all` | count output and no uncaught CSV/LZMA errors |
| `suspicions <dataset>` | Local data mutation | Reimbursements already loaded; `.xz` suspicion CSV | Updates reimbursement `suspicions` JSON and `probability` | `--batch-size`, `--workers` | `... reimbursements updated` |
| `receipts_text <dataset>` | Local data mutation | Reimbursements loaded; `.xz` CSV with `document_id,text` | Updates `receipt_text` | `--batch-size` | `... reimbursements updated` |
| `searchvector` | Local data mutation; PostgreSQL-specific | PostgreSQL DB; reimbursement rows | Populates full-text search vectors | `--all`, `--silent`, `--batch-size` | progress bar or clean exit |
| `tweets` | Network read + local mutation | Twitter API credentials; DB rows; network | Reads recent Rosie tweets and links them to reimbursements | none | warning if credentials missing, otherwise DB links/log messages |
| `tweet` | Network write + local mutation | Twitter API credentials; suspicious reimbursements; network | Publishes next selected suspicion tweet and stores status | `--fake` | dry-run message with `--fake`; real tweet otherwise |
| `receipts` | Network read + local mutation | DB rows; external receipt hosts; network | Fetches and stores receipt URLs | `--batch-size`, `--pause` | fetched count, pause/save messages |
| `socialmedia <dataset>` | Local data mutation; destructive with `--drop-all` | CSV with social-media headers | Bulk-creates social-media account rows | `--drop-all` | `Saving social media accounts` then `Done!` |
| `update <directory>` | Destructive/rebuild + network read | Directory with full datasets; DB backup plan; network for receipt text | Backs up tweets, reloads all reimbursement files, loads suspicions/receipt text, rebuilds search vectors, restores tweets | none | step-by-step import/rebuild/restoration messages |
| `collectstatic` | Local filesystem mutation | Django settings; static root writable | Collects static files | `--no-input` | copied/static-file count |
| `runserver` | Service start | DB config and imports | Starts dev web server | host/port | server listens locally |

## Shared `LoadCommand` helpers

Several data loaders inherit a shared command helper:

- Adds a positional `dataset` argument.
- Adds `--drop-all` unless the command disables it.
- `drop_all(model)` deletes every row for the model and prints a count; treat it as destructive.
- `to_number(value, cast=None)` maps `nan`, `NaN`, and empty strings to `None`, otherwise parses `float` and optionally casts.
- `to_date(text)` accepts `DD/MM/YY`, `DD/MM/YYYY`, and `YYYY-MM-DD...` style dates; invalid dates become `None`.
- `print_count(model, permanent=False)` writes a carriage-return progress count unless permanent output is requested.

Native tests for these helpers cover date/number parsing, argument registration, count printing, and destructive drop-all behavior. When diagnosing loader parsing bugs, isolate helper conversion first before rerunning a full data load.

## Detailed command notes

### `python manage.py reimbursements <csv>`

Use for base CEAP reimbursement data. The serializer creates a model instance only when `issue_date` parses successfully. Empty numeric values in total fields become `0.0`; integer/date/list-like fields are normalized before bulk insert.

Operational tips:

```console
$ python manage.py reimbursements contrib/data/reimbursements_sample.csv --batch-size 512
$ python manage.py reimbursements path/to/reimbursements-2016.csv --drop-all
```

Use `--drop-all` only once at the beginning of a full rebuild, not before every yearly file.

### `python manage.py companies <xz>`

Loads company/supplier data. The command creates or updates `Activity` rows for main and secondary activity codes, then creates `Company` rows and attaches activities.

Pitfalls:

- Requires `lzma` module support.
- Invalid emails are stored as `None`, not fatal.
- The sample company file is filtered to suppliers present in the sample reimbursement file.

### `python manage.py suspicions <xz>`

Attaches Rosie suspicion output to existing reimbursements by `document_id`.

Pitfalls:

- Rows with missing/unmatched document IDs are skipped.
- If a `probability` column is absent, suspicion JSON can still be updated.
- Truthy suspicion columns become JSON keys set to `true`; false-like strings are ignored.

### `python manage.py receipts_text <xz>`

Loads receipt OCR/text content into `receipt_text`. Use before `searchvector` if text search should include the content.

Expected minimal dataset shape:

```csv
document_id,text
123456,"receipt text here"
```

### `python manage.py searchvector [--all]`

Builds PostgreSQL search vectors from reimbursement fields:

- High weight: congressperson name, supplier, CNPJ/CPF, party.
- Medium weight: state and receipt text.
- Lower weights: passenger, leg of trip, subquota descriptions.

Default mode only fills rows where `search_vector` is null. Use `--all` after changing text fields or when rebuilding from scratch.

### `python manage.py receipts`

Fetches receipt URLs from public Chamber of Deputies receipt endpoints. It uses a thread pool and periodically pauses to avoid being blocked.

Safe tuning for smaller batches:

```console
$ python manage.py receipts --batch-size 128 --pause 15
```

Do not run this as part of a basic sample smoke unless network calls and DB writes are explicitly desired.

### `python manage.py tweets`

Reads recent tweets from the Rosie account and links them to reimbursements. It requires all four Twitter credentials. Missing credentials cause a warning and no DB write.

### `python manage.py tweet [--fake]`

Selects a suspicious reimbursement and formats/publishes a tweet. Always use `--fake` for diagnostics:

```console
$ python manage.py tweet --fake
```

Without `--fake`, it can publish to the configured account and create a `Tweet` row.

### `python manage.py socialmedia <csv>`

Loads optional social media account mappings. Minimal headers:

```csv
congressperson_name,congressperson_id,twitter_profile,secondary_twitter_profile,facebook_page
```

Run this before mention-aware Twitter workflows if those workflows are implemented in the calling code.

### `python manage.py update <directory>`

High-risk rebuild command. It expects a directory containing full data files and performs the following sequence:

1. Backs up existing `Tweet` links to `tweets.csv` inside the given directory.
2. Deletes reimbursement data while loading sorted `reimbursements-*.csv` files.
3. Loads `suspicions.xz`.
4. Downloads a fixed receipt-text dataset from public object storage.
5. Loads receipt text.
6. Rebuilds search vectors.
7. Restores tweet links that still match loaded reimbursements.

Use this only with backups, network authorization, and a confirmed target DB. For local sample work, prefer explicit individual load commands.

## Recommended validation after command runs

```console
$ python manage.py check
$ python manage.py shell -c "from jarbas.chamber_of_deputies.models import Reimbursement; print(Reimbursement.objects.count())"
$ python manage.py shell -c "from jarbas.core.models import Company; print(Company.objects.count())"
```

When using Docker, run the same through the `django` service. If API behavior must be validated, route to `jarbas-data-api` after the database is seeded.
