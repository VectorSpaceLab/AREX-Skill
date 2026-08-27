# Rosie Classifier Reference

## Missing-column preflight

Most classifier failures on tiny or custom dataframes start with missing columns. Check the required set first:

```python
required = {"recipient_id", "document_type"}
missing = sorted(required - set(df.columns))
if missing:
    raise ValueError(f"Missing Rosie columns: {missing}")
```

Use the classifier table below to choose the correct required columns for each smoke or adaptation task.

## Settings catalogs

### Chamber of Deputies

The Chamber pipeline uses these `CLASSIFIERS` entries, in settings order:

| Suspicion column | Classifier class | Output style |
| --- | --- | --- |
| `meal_price_outlier` | `MealPriceOutlierClassifier` | `1` / `-1`, converted by `Core` to `False` / `True` |
| `over_monthly_subquota_limit` | `MonthlySubquotaLimitClassifier` | Boolean |
| `suspicious_traveled_speed_day` | `TraveledSpeedsClassifier` | `1` / `-1`, converted by `Core` to `False` / `True` |
| `invalid_cnpj_cpf` | `InvalidCnpjCpfClassifier` | Boolean |
| `election_expenses` | `ElectionExpensesClassifier` | Boolean |
| `irregular_companies_classifier` | `IrregularCompaniesClassifier` | Boolean |

Chamber `UNIQUE_IDS` are `applicant_id`, `year`, and `document_id`, so the final suspicion file contains those identifiers plus classifier columns.

### Federal Senate

The Federal Senate pipeline uses only:

| Suspicion column | Classifier class | Output style |
| --- | --- | --- |
| `invalid_cnpj_cpf` | `InvalidCnpjCpfClassifier` | Boolean |

Federal Senate `UNIQUE_IDS` is `None`, so the final suspicion file preserves the full normalized dataframe and appends the classifier column.

## Required columns and behavior

### `InvalidCnpjCpfClassifier`

Use for both Chamber and Federal Senate data.

Required columns:

- `recipient_id`: CNPJ or CPF as a string-like value. Missing values are stringified before validation.
- `document_type`: only `bill_of_sale`, `simple_receipt`, and `unknown` are checked. `unknown` is used by Federal Senate normalization.

Behavior:

- Validates both CPF and CNPJ check digits.
- Returns `True` when the document type is applicable and neither CPF nor CNPJ validation passes.
- Returns `False` for non-applicable document types such as expenses made abroad.
- `fit` and `transform` are no-op methods returning the classifier instance.

### `ElectionExpensesClassifier`

Use for Chamber data after company information has been merged.

Required columns:

- `legal_entity`: Brazilian Federal Revenue legal-entity category string.

Behavior:

- Returns `True` only when `legal_entity` is exactly `409-0 - CANDIDATO A CARGO POLITICO ELETIVO`.
- `fit` and `transform` are no-ops that return `None` in the native implementation.

### `IrregularCompaniesClassifier`

Use for Chamber data after company information has been merged.

Required columns:

- `issue_date`: expense date.
- `situation`: company situation string.
- `situation_date`: date when the company situation changed.

Behavior:

- Treats `BAIXADA`, `NULA`, `SUSPENSA`, and `INAPTA` as suspicious situations.
- Returns `True` only when the suspicious situation date is earlier than the expense issue date.
- `fit` and `transform` are no-ops returning the classifier instance.

### `MealPriceOutlierClassifier`

Use for Chamber meal expenses.

Required columns:

- `applicant_id`: reimbursing person identifier.
- `category`: expected to contain `Meal` for applicable rows.
- `net_value`: reimbursement value.
- `recipient`: supplier name; used to exclude hotel-like names.
- `recipient_id`: CNPJ/CPF string; only 14-character company IDs are applicable.

Behavior:

- Fits a KMeans model over company-level meal statistics using `mean` and `std` of `net_value`.
- Considers only rows with `category == "Meal"`, 14-character `recipient_id`, and supplier names that do not look like hotels.
- Uses common-company thresholds when a company has more than 3 congresspeople and more than 20 records; otherwise falls back to cluster thresholds.
- Returns `-1` for outliers and `1` for inliers; `Core` converts that to `True` and `False` respectively.
- Needs enough applicable training rows to fit KMeans. Tiny synthetic dataframes often fail unless the model is already fitted with representative records.

### `MonthlySubquotaLimitClassifier`

Use for Chamber monthly spending-limit checks.

Required columns:

- `applicant_id`: grouping key.
- `issue_date`: expense date; used to sort reimbursement order.
- `month`: quota month.
- `net_value`: reimbursement value, converted to cents internally.
- `subquota_number`: category code as a string-like value.
- `year`: quota year.

Behavior:

- Creates a reimbursement-month date from `year`, `month`, and day `1`.
- Checks cumulative monthly spending against hard-coded limits for subquota numbers `3`, `8`, `120`, `122`, and `137` over specific date ranges.
- Returns boolean `True` for surplus reimbursements after the cumulative limit is exceeded.
- Is always fitted during a core run and is not cached to `.pkl`.

### `TraveledSpeedsClassifier`

Use for Chamber meal-location plausibility checks.

Required columns:

- `applicant_id`: grouping key.
- `category`: only `Meal` rows are applicable.
- `is_party_expense`: must be `False` for applicable rows.
- `issue_date`: date grouping key.
- `latitude`: supplier latitude.
- `longitude`: supplier longitude.

Behavior:

- Accepts `contamination` in the open interval `(0, 1)`; default is `0.001`.
- Fits a polynomial over daily combinations of meal coordinates grouped by applicant and issue date.
- Restricts applicable rows to coordinates inside a broad Brazil bounding box and non-null latitude/longitude.
- Flags rows when a day has more than 8 applicable meal expenses or when traveled-distance deviation exceeds a threshold chosen for the contamination target.
- Returns `-1` for outliers and `1` for inliers; `Core` converts that to `True` and `False` respectively.

## Interpreting output columns

In `suspicions.xz`, `True` means the row was considered suspicious by that classifier. `False` means the classifier did not flag it. For classifiers that internally use `1` and `-1`, this conversion is already performed by `Core` when integer predictions are returned.

If calling classifiers directly, preserve the native return convention of that classifier. Do not assume all direct classifier calls return booleans.
