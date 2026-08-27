# Configuration and Data Troubleshooting

Use this guide for static config/data failures before running retrosynthesis. If the failure occurs during tree search execution, route to planning-workflows; if it occurs while reading outputs, route to route-analysis.

## Missing Environment Variables

Symptom:

- Config loading raises a message like `'<NAME>' not in environment variables`.
- The bundled validator reports unresolved placeholders.

Cause:

- AiZynthFinder replaces `${VAR}` placeholders before YAML parsing and fails if any variable is missing.

Fix:

1. List placeholders in the config.
2. Ask the user for values or remove placeholders.
3. Export variables in the shell that will run AiZynthFinder.
4. Re-run static validation.

Avoid quoting numeric placeholders if the value should parse as an int, float, or bool.

## Malformed YAML or Wrong Top-Level Shape

Symptoms:

- YAML parser errors.
- Validator reports the top-level document is not a mapping.
- AiZynthFinder raises unexpected attribute or unpacking errors.

Cause:

- Tabs, bad indentation, lists where mappings are required, or scalar top-level content.

Fix:

- Keep top-level keys as mappings: `search`, `post_processing`, `expansion`, `filter`, `stock`, `scorer`.
- Use two spaces for indentation.
- Put short-form expansion as exactly a two-item list: `[model, template]` or block list with two items.
- Put short-form filter and stock as scalar paths.

## Invalid Search Settings

Symptoms:

- Error mentioning `Could not find attribute to set`.
- Error mentioning `algorithm_config settings need to be dictionary`.
- Error mentioning bond settings or bond-pair length.

Causes and fixes:

- Unknown `search` key: remove or correct the key.
- `algorithm_config` is not a mapping: change it to key-value YAML.
- `break_bonds` or `freeze_bonds` is not a list: use a list.
- A bond entry is not exactly two values: use `[[1, 2], [3, 4]]`.
- Atom mapping/index interpretation is wrong for the molecule: verify the mapped product used by the planning workflow.

## Missing Model, Template, Mask, or Stock Files

Symptoms:

- Validator warns that a referenced file is missing.
- Runtime raises file-not-found, HDF5 read, ONNX/Keras load, or pandas read errors.

Cause:

- Config paths are resolved relative to the process working directory at runtime, not automatically relative to the config file in every context.

Fix:

1. Prefer project-relative or absolute user-approved asset paths in the config used for execution.
2. Check paths relative to both the config file directory and planned runtime working directory.
3. For templates, confirm HDF5 key `table` or tab-separated `.csv`/`.csv.gz` shape.
4. For stocks, confirm HDF5/CSV/text file type and required columns.
5. Re-run the static validator after path edits.

## Template Table Column or Size Mismatch

Symptoms:

- Runtime raises missing column errors such as missing `retro_template`.
- Runtime raises a policy error that model output dimensions do not match number of templates.
- Mask loading reports mask length does not match templates.

Cause:

- Template table column does not match `template_column`.
- Model checkpoint and template table were trained/generated as different sets.
- Mask file length differs from template rows.

Fix:

- Set `template_column` to the actual column containing retrosynthesis SMARTS.
- Pair model and template files from the same release/training run.
- Regenerate or remove the mask file if it does not match the template table.

## No Expansion Policy Selected

Symptoms:

- Runtime raises `No expansion policy selected`.
- Search starts but cannot generate actions.

Cause:

- Policies may be loaded from config but not selected in the execution interface.

Fix:

- For CLI execution, use planning-workflows and ensure the interface selects expansion policies as intended.
- In programmatic workflows, call selection on the expansion policy collection before search.
- Static config validation can verify policies are defined, but it cannot prove runtime selection.

## Filter Policy Problems

Symptoms:

- Runtime raises `No filter policy selected` when applying a filter manually.
- Quick-filter model load fails.
- Reactions are unexpectedly rejected.

Causes and fixes:

- Filter configured but not selected: select it in the planning workflow or let CLI select all loaded filters where appropriate.
- Missing quick-filter model path: fix `filter.<name>.model`.
- Too high `filter_cutoff`: lower cautiously or compare against known working settings.
- Wrong `exclude_from_policy`: ensure names match expansion policy keys, not filenames unless those are the policy keys.

## Stock File Column Problems

Symptoms:

- CSV/HDF5 stock loading fails with missing `inchi_key` or configured column.
- Price-based stop criteria are ineffective or raise stock exceptions.
- Duplicate, null, or negative price errors appear.

Cause:

- File does not match expected stock schema.

Fix:

- HDF5 stock: table key must be `table` and contain `inchi_key` by default.
- CSV stock: include `inchi_key` or set `inchi_key_col`.
- Text stock: one InChI key per line, not SMILES.
- If `price_col` is set, each InChI key must be unique, price values must be non-null, and prices must be non-negative.
- Use `smiles2stock --target hdf5` to create a compatible stock from plain SMILES.

## MongoDB Stock Failures

Symptoms:

- Import error says `pymongo` is not installed.
- Connection or authentication errors.
- Stock appears empty even though MongoDB is reachable.

Causes and fixes:

- Install optional Mongo support before use.
- Confirm `host`, credentials, database, and collection.
- If `host` is omitted, confirm whether `MONGODB_HOST` or `localhost` is intended.
- Ensure documents contain `inchi_key` and `source` fields.
- If using `smiles2stock --target mongo`, confirm the source tag in `--output` is the intended tag; existing docs for that tag are deleted before insertion.

## Molbloom Failures

Symptoms:

- Import error says `molbloom` is not installed.
- `.bloom` path exists but lookup fails unexpectedly.
- False positives are too frequent.

Causes and fixes:

- Install optional molbloom support before use.
- Match config `smiles_based` to how the bloom filter was created.
- For `smiles2stock --target molbloom`, lookup is SMILES-based.
- For `smiles2stock --target molbloom-inchi`, lookup is InChI-key based.
- Recreate the filter with better `--bloom_params` if false positives are unacceptable.

## TensorFlow Serving and Remote Model Failures

Symptoms:

- Remote model connection errors.
- TensorFlow/gRPC import errors.
- Policy or filter cannot obtain predictions.

Cause:

- `use_remote_models: true` requires TensorFlow-serving-related optional dependencies and a reachable server with expected model names/signatures.

Fix:

- Set `use_remote_models: false` for local ONNX/Keras checkpoints.
- Confirm optional `tf` dependencies for remote serving.
- Confirm server URL/model naming in the model source expected by the runtime.
- Fall back to local model files when reproducibility matters.

## Public Data Download Failures

Symptoms:

- HTTP error during `download_public_data`.
- Partial files in the target directory.
- Generated `config.yml` points to missing files.

Cause:

- Network failure, storage limit, changed upstream availability, or interrupted download.

Fix:

1. Do not retry blindly if storage or network policy is unclear.
2. Remove partial files or choose a clean target directory.
3. Confirm enough disk space and network access.
4. Re-run `download_public_data PATH` only after user approval.
5. Validate generated `config.yml` before execution.

## Route-Distance or Plotting Optional Features

Symptoms:

- `post_processing.route_distance_model` fails to load.
- Clustering or plotting imports fail.

Cause:

- Optional route-distance, SciPy, or plotting dependencies are missing or the model file is incompatible.

Fix:

- Install the optional dependencies needed for route-distance/plotting workflows.
- Confirm `route_distance_model` path exists.
- Route output interpretation and clustering decisions to route-analysis.
