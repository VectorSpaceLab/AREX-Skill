# Rosie Troubleshooting

## Native run unexpectedly downloads data

Symptom: `python rosie.py run ...` touches the network, takes a long time, or fails before classifier execution.

Cause: both native adapters update datasets when their `dataset` property is accessed. Chamber fetches the companies dataset and yearly reimbursements; Federal Senate fetches, translates, and cleans the senate dataset.

Fix:

- For production data, prepare network access and output storage through the data-ops workflow.
- For deterministic local checks, do not call the native `run` command. Use a direct classifier smoke or a custom adapter with local data.
- For Chamber, pre-populate expected company and reimbursement files only if you also prevent the update methods from refetching them.

## `suspicions.xz` is missing

Likely causes:

- Adapter dataset loading failed before `Core.__call__` reached `to_csv`.
- Required input files are absent or empty.
- A classifier raised a dependency, column, fit, or prediction error.
- The output directory is not writable.

Checks:

1. Confirm the selected module is one of `chamber_of_deputies` or `federal_senate`.
2. Confirm the output directory exists or can be created.
3. For Chamber, confirm reimbursement CSV files matching `reimbursements-<year>.csv` and the companies xz file exist after update.
4. For Federal Senate, confirm the toolbox helper returned a cleaned dataset path.
5. Run a no-download classifier smoke to separate import/dependency failures from download/data failures.

## Missing dataframe columns

Symptom: `KeyError` for columns such as `recipient_id`, `document_type`, `net_value`, `legal_entity`, `situation_date`, `latitude`, or `longitude`.

Cause: the classifier catalog does not match the adapter-normalized dataframe.

Fix:

- Use the classifier reference to list required columns for each selected classifier.
- For Chamber-style classifiers, run or reproduce Chamber normalization before fitting/predicting.
- For Federal Senate, use only classifiers whose required columns exist after Federal normalization, unless you explicitly enrich the dataframe.
- If building custom settings, remove classifiers that cannot be supported by your dataframe.

## Stale or incompatible `.pkl` cache

Symptom: predictions do not change after data/code changes, or joblib fails while loading a cached model.

Cause: `Core` reuses `<lowercase-class-name>.pkl` from the output directory whenever the file exists. The cache may be stale, trained on different data, or incompatible with the current dependency versions.

Fix:

- Delete the affected classifier `.pkl` in the selected output directory to force retraining.
- Keep caches separated by dataset version and dependency environment.
- Remember that `MonthlySubquotaLimitClassifier` is intentionally not cached.

## Legacy dependency errors

Rosie was written against older Python data-science APIs. In modern environments, common compatibility failures include:

- `ImportError` for `sklearn.externals.joblib`; use an environment with the expected scikit-learn version or patch/import `joblib` explicitly before importing the core.
- Missing `np.str`, `np.int`, or `np.long`; older code uses NumPy aliases removed in newer NumPy versions.
- Missing `DataFrame.append`; newer pandas removed it.
- Pandas category rename errors involving `inplace=True`; newer pandas APIs changed categorical rename behavior.
- Missing `geopy.distance.vincenty`; newer geopy versions replaced it with geodesic distance APIs.
- Missing packages such as `docopt`, `brutils`, `serenata_toolbox`, `pandas`, `scikit-learn`, `freezegun`, or `geopy`.

Fix by using the repository's intended environment when running native workflows. For narrow smoke checks, use the bundled script, which applies minimal compatibility shims only for the invalid-CNPJ/CPF smoke.

## Network and data-source failures

Chamber update catches per-year HTTP errors for reimbursements, logs them, and continues. This can leave partial data while still allowing later stages to run. Federal Senate update does not have the same per-year loop and may fail directly in fetch/translate/clean.

Operational checks:

- Treat a successful process with unexpectedly few rows as a possible partial-download run.
- Check which years were actually present before interpreting missing suspicions.
- Keep downloaded data versioned or isolated by run when comparing outputs.
- Route broader data acquisition, storage, and service setup to `deployment-and-data-ops`.

## Classifier-specific pitfalls

### Invalid CNPJ/CPF

- Only `bill_of_sale`, `simple_receipt`, and `unknown` document types are validated.
- Invalid IDs on `expense_made_abroad` or missing/other document types are not flagged.
- IDs are zero-filled to CPF/CNPJ length before validation, so preserve string-like IDs when reading CSVs.

### Election expenses

- Requires `legal_entity` from the company merge.
- Null or differently formatted legal-entity strings are not suspicious.

### Irregular companies

- Requires comparable date values in `issue_date` and `situation_date`.
- Flags only if the company was already in a suspicious situation before the expense date.

### Meal price outliers

- Needs enough applicable meal-company records to fit KMeans.
- Hotel-like supplier names are excluded from applicability.
- CPF-like recipient IDs are not applicable because the code expects 14-character company IDs.

### Monthly subquota limit

- `subquota_number` should be string-like so comparisons such as `"120"` match.
- Values are converted to cents by multiplying `net_value` by 100 and casting to int.
- The order by coerced issue date affects which reimbursement becomes the surplus row.

### Traveled speeds

- Must call `fit` before `predict`.
- `contamination` must be greater than 0 and less than 1.
- Rows outside the Brazil bounding box, party expenses, non-meal categories, or rows missing coordinates are treated as inliers.

## `VALUE` settings confusion

The core documentation says settings should define `VALUE`, but the current implementation does not read it, and native Chamber/Federal settings do not define it. If you are creating a new settings object, include `VALUE` for clarity and forward compatibility, but debug current execution through actual classifier-required columns such as `net_value`.
