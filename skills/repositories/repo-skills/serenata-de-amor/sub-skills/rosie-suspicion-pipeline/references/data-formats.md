# Rosie Data Formats

## Output: `suspicions.xz`

Rosie writes a compressed CSV named `suspicions.xz` in the selected output directory. The file is written with xz compression, UTF-8 encoding, and no dataframe index.

The core output shape depends on `settings.UNIQUE_IDS`:

- When `UNIQUE_IDS` is a column list, the output starts with those identifiers and appends one suspicion column per classifier.
- When `UNIQUE_IDS` is `None`, the output starts as a copy of the entire normalized input dataframe and appends one suspicion column per classifier.

Chamber output uses `applicant_id`, `year`, and `document_id` as identifiers. Federal Senate output keeps the whole normalized dataframe because its settings use `UNIQUE_IDS = None`.

Each suspicion column contains `True` for suspicious and `False` for not suspicious after `Core` finishes conversion.

## Chamber of Deputies adapter

The Chamber adapter receives an output/data directory and exposes `dataset` plus `path`.

### Data acquisition

When `dataset` is accessed, the adapter calls its update methods before loading local files:

- Ensures the output directory exists.
- Fetches the companies dataset named `2016-09-03-companies.xz` through the toolbox dataset fetcher.
- Requests yearly reimbursement CSV files from 2009 through the current year using the toolbox Chamber reimbursement fetcher.
- Logs per-year HTTP errors during reimbursement updates, then continues with the next year.

This means the native `run chamber_of_deputies` command is a network-touching workflow unless the fetchers are mocked, pre-cached, or otherwise isolated.

### Local files read

The adapter reads:

- `2016-09-03-companies.xz` with `cnpj` as string-like data.
- Every CSV in the output directory whose filename matches `reimbursements-<year>.csv`.

The reimbursement reader treats `applicant_id`, `cnpj_cpf`, `congressperson_id`, and `subquota_number` as string-like values to preserve identifiers and category codes.

### Merge and normalization

The Chamber adapter merges reimbursements to companies with:

- left key: reimbursement `cnpj_cpf`
- right key: company `cnpj`
- join style: left join

It then normalizes the merged dataframe:

| Source column | Normalized column |
| --- | --- |
| `subquota_description` | `category` |
| `total_net_value` | `net_value` |
| `cnpj_cpf` | `recipient_id` |
| `supplier` | `recipient` |

Additional normalization:

- Company `cnpj` has non-digits removed before merge.
- `document_type` numeric categories are converted to `bill_of_sale`, `simple_receipt`, and `expense_made_abroad`; undocumented numeric values 3, 4, and 5 are replaced with missing values before category conversion.
- `subquota_description == "Congressperson meal"` is renamed to `Meal` so meal classifiers can match it.
- `is_party_expense` is `True` when `congressperson_id` is missing.
- `issue_date` is parsed with `%Y-%m-%d`.
- `situation_date` is parsed with `%d/%m/%Y`.

### Classifier-relevant Chamber columns

After normalization and company merge, Chamber classifiers may require:

- identifiers: `applicant_id`, `year`, `document_id`
- values/categories: `category`, `net_value`, `subquota_number`, `month`
- document fields: `recipient_id`, `document_type`, `recipient`
- company fields: `legal_entity`, `situation`, `situation_date`, `latitude`, `longitude`
- travel fields: `is_party_expense`, `issue_date`

Missing company merge rows can leave `legal_entity`, `situation`, coordinates, or situation dates null, which affects classifier applicability.

## Federal Senate adapter

The Federal Senate adapter receives an output/data directory and exposes `dataset` plus `path`.

### Data acquisition

When `dataset` is accessed, the adapter:

1. Ensures the output directory exists.
2. Creates the toolbox Federal Senate dataset helper.
3. Calls `fetch()`.
4. Calls `translate()`.
5. Calls `clean()` and reads the returned cleaned dataset path.

This is also a network-touching native workflow unless isolated or mocked.

### Normalization

The Federal adapter reads the cleaned CSV with `cnpj_cpf` as string-like data and renames:

| Normalized column | Source column |
| --- | --- |
| `net_value` | `reimbursement_value` |
| `recipient_id` | `cnpj_cpf` |
| `recipient` | `supplier` |

It also creates `document_type = "unknown"` because the Federal dataset does not provide the Chamber document-type categories required by the core CNPJ/CPF classifier.

The native adapter has a method intended to drop null CNPJ/CPF values, but the current implementation does not assign the filtered dataframe back to the adapter. If null recipient IDs matter for your task, filter them explicitly in an offline adapter or validate the produced dataframe before running classifiers.

## Data-loading and Jarbas boundaries

Rosie produces suspicion data. Jarbas serving, API querying, database migrations, loading CSV data into tables, search-vector setup, Docker/service orchestration, and deployment are outside this sub-skill.

- Use `jarbas-data-api` for API endpoint behavior, serializers, querysets, and URL construction.
- Use `deployment-and-data-ops` for setup, data loading, management commands, databases, Docker, and service troubleshooting.
