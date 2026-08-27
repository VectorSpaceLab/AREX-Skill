# Data loading reference

Jarbas data loads are Django management commands. Run them only after configuration and migrations are ready. Sample datasets are useful for a development database; they are not the full Serenata de Amor dataset.

## Safe sample load order

For a fresh Jarbas database:

```console
$ python manage.py migrate
$ python manage.py reimbursements contrib/data/reimbursements_sample.csv
$ python manage.py companies contrib/data/companies_sample.xz
$ python manage.py suspicions contrib/data/suspicions_sample.xz
$ python manage.py searchvector
```

Docker Compose uses the container-mounted data path:

```console
$ docker compose run --rm django python manage.py migrate
$ docker compose run --rm django python manage.py reimbursements /mnt/data/reimbursements_sample.csv
$ docker compose run --rm django python manage.py companies /mnt/data/companies_sample.xz
$ docker compose run --rm django python manage.py suspicions /mnt/data/suspicions_sample.xz
$ docker compose run --rm django python manage.py searchvector
```

Why this order matters:

1. `migrate` creates the model tables and PostgreSQL search-vector column/index.
2. `reimbursements` creates the base `Reimbursement` rows.
3. `companies` creates suppliers and activities; it does not depend on reimbursements but is usually loaded before users inspect company pages.
4. `suspicions` updates existing reimbursement rows by `document_id`; it cannot attach anything if reimbursements were not loaded first.
5. `searchvector` should run after reimbursement text/search fields are present.
6. `tweets`, `receipts`, `receipts_text`, and `socialmedia` are optional enrichment steps with separate prerequisites.

## Bundled sample datasets

| File | Command | Compression | Important columns | Role |
| --- | --- | --- | --- | --- |
| `contrib/data/reimbursements_sample.csv` | `reimbursements` | plain CSV | `applicant_id`, `batch_number`, `cnpj_cpf`, `congressperson_document`, `congressperson_id`, `congressperson_name`, `document_id`, `document_number`, `document_type`, `document_value`, `issue_date`, `month`, `numbers`, `party`, `state`, `subquota_*`, `supplier`, `total_net_value`, `total_value`, `year` | Base expense rows for Jarbas. Rows without a parseable `issue_date` are skipped by the serializer. |
| `contrib/data/companies_sample.xz` | `companies` | LZMA/XZ CSV | `cnpj`, `opening`, `legal_entity`, `trade_name`, `name`, `type`, `status`, `situation`, `situation_date`, `address`, `city`, `state`, `email`, `phone`, `latitude`, `longitude`, `main_activity`, `main_activity_code`, repeated `secondary_activity_*` columns | Supplier/company records and related activity rows. |
| `contrib/data/suspicions_sample.xz` | `suspicions` | LZMA/XZ CSV | `applicant_id`, `year`, `document_id`, optional `probability`, one column per suspicion hypothesis | Updates existing reimbursements with `suspicions` JSON and `probability`. |

The sample data was produced by selecting about 1,000 reimbursement rows, filtering companies to suppliers present in that sample, and filtering suspicion rows to matching `document_id` values. Do not use it for statistical claims.

## Full data or Rosie output

Full operational datasets may come from Rosie or external data tooling:

- `reimbursements-YYYY.csv` files: loaded by the `update` command or manually with repeated `reimbursements` calls.
- `suspicions.xz`: Rosie suspicion output, loaded by `suspicions`.
- `companies.xz`: supplier/company dataset, loaded by `companies`.
- `2017-02-15-receipts-texts.xz` or equivalent receipt OCR/text dataset: loaded by `receipts_text`.

For manually replacing all reimbursements from full yearly files, first back up any data you need, then use `--drop-all` only on the first reimbursement file:

```console
$ python manage.py reimbursements path/to/reimbursements-2016.csv --drop-all
$ python manage.py reimbursements path/to/reimbursements-2017.csv
$ python manage.py suspicions path/to/suspicions.xz
$ python manage.py receipts_text path/to/receipts-texts.xz
$ python manage.py searchvector --all
```

The high-level `update` command automates part of this sequence and downloads a fixed receipt-text dataset. It is riskier than the explicit commands because it deletes/reloads reimbursement data and performs network I/O.

## Command-specific data contracts

### `reimbursements`

- Input: CSV, not LZMA, opened as text.
- Rows are converted through field-specific serializers:
  - Integer fields include IDs, year, month, term, subquota, document type, installment, and batch number.
  - Decimal/float-like fields include document value, remark value, total net value, and total value.
  - `issue_date` is parsed from the CSV date string; rows without a date are skipped.
  - `numbers` is parsed as an array/list-like field.
- Output: bulk-created `Reimbursement` rows.
- Flag: `--drop-all` deletes existing reimbursements before loading.
- Useful tuning: `--batch-size N` (default 4096).

### `companies`

- Input: LZMA/XZ CSV.
- Creates `Activity` rows from `main_activity`/`main_activity_code` and repeated secondary activity columns, then creates `Company` rows and attaches activities.
- Normalizes invalid email values to `None`.
- Parses dates like `DD/MM/YYYY` or `YYYY-MM-DD...`; invalid dates become `None`.
- Parses latitude/longitude as numbers.
- Flag: `--drop-all` deletes existing companies and activities first.

### `suspicions`

- Input: LZMA/XZ CSV.
- Must run after reimbursements are present.
- Uses `document_id` to find an existing reimbursement.
- Stores a JSON map of suspicion hypothesis columns whose values are truthy. Values like `false`, `0`, `0.0`, `none`, `nil`, `null`, or empty are false.
- Updates `probability` when the column exists.
- Tuning flags: `--batch-size N`, `--workers N`.

### `receipts_text`

- Input: LZMA/XZ CSV with at least `document_id` and `text` columns.
- Must run after reimbursements are present.
- Updates `Reimbursement.receipt_text`; missing document IDs are skipped.
- Tuning flag: `--batch-size N`.
- Re-run `searchvector` after loading receipt text if users need text search to include OCR/receipt content.

### `socialmedia`

- Input: plain CSV whose headers match the `SocialMedia` model fields:
  - `congressperson_name`
  - `congressperson_id`
  - `twitter_profile`
  - `secondary_twitter_profile`
  - `facebook_page`
- Creates `SocialMedia` rows in bulk.
- Flag: `--drop-all` deletes existing social-media rows first.

### `tweets`

- No dataset argument.
- Reads the latest Rosie account timeline via Twitter API credentials and links tweet status IDs to reimbursements whose tweeted URLs contain a `documentId/<id>` segment.
- If any Twitter credential is missing, the command logs a warning and exits without changing data.

### `tweet`

- No dataset argument.
- Selects an eligible suspicious reimbursement and publishes a tweet unless `--fake` is passed.
- Use `--fake` for dry runs. Without `--fake`, the command can post to the configured Twitter account.

### `receipts`

- No dataset argument.
- Fetches receipt URLs for reimbursements where `receipt_fetched=False`, using concurrent HTTP HEAD requests.
- Side effects: network calls to public receipt hosts and database updates.
- Tuning flags: `--batch-size N`, `--pause SECONDS`.

### `searchvector`

- No dataset argument.
- Uses PostgreSQL full-text search vectors over reimbursement fields including congressperson, supplier, party, state, receipt text, passenger, trip leg, and subquota descriptions.
- Flag: `--all` rebuilds all rows; default only fills rows where `search_vector` is null.
- Flag: `--silent` suppresses progress output.
- Tuning flag: `--batch-size N`.

## Validation snippets

After loading samples, verify counts without exposing data:

```console
$ python manage.py shell -c "from jarbas.chamber_of_deputies.models import Reimbursement; from jarbas.core.models import Company; print('reimbursements', Reimbursement.objects.count()); print('companies', Company.objects.count())"
```

Check how many loaded reimbursements have suspicions:

```console
$ python manage.py shell -c "from jarbas.chamber_of_deputies.models import Reimbursement; print(Reimbursement.objects.exclude(suspicions=None).count())"
```

For API queries after seeding, route to the `jarbas-data-api` sub-skill; this file only establishes that the database has the required rows and search vectors.

## Common load-order mistakes

- Running `suspicions` before `reimbursements`: results in zero or few updates because target rows do not exist.
- Running `searchvector` before `receipts_text`: text search will omit later receipt OCR/text until search vectors are rebuilt.
- Using SQLite for full loads: import checks may pass, but PostgreSQL-specific model/search behavior is not fully represented.
- Forgetting `lzma` support: `.xz` loaders fail before reading rows.
- Using `--drop-all` on the wrong database: destructive. Confirm `DATABASE_URL` first.
