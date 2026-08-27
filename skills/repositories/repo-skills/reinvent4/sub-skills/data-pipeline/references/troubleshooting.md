# Troubleshooting Data Pipeline Runs

## CLI and Environment

- Use `reinvent_datapre data_pipeline.toml --log-filename data_pipeline.log`; do not put `run_type` in a data-pipeline config.
- `reinvent_datapre` only accepts a config `FILE` and optional `--log-filename`.
- If a console script is missing, verify that the installed distribution exposes `reinvent_datapre` and that the active environment has REINVENT4 installed.
- If the main `reinvent --help` fails before showing help because `scipy` is missing, install the missing dependency and retry. That failure is caused by an imported plotting utility and does not mean `data_pipeline.toml` keys are wrong.

## Config Parsing Failures

- Unknown top-level or `[filter]` keys fail runtime validation because the pydantic models forbid extras.
- `input_csv_file`, `output_smiles_file`, and practical `[filter]` settings are required for a usable job.
- `separator` must be exactly one character. In TOML, tab is `"\t"`; comma is `","`.
- Numeric thresholds such as `num_procs`, `chunk_size`, `min_heavy_atoms`, `max_heavy_atoms`, `max_num_rings`, and `max_ring_size` must be positive.
- `max_*` values lower than corresponding `min_*` values cause over-filtering even if schema parsing succeeds.

## Wrong Delimiter, Header, or Column

Symptoms:

- The selected `smiles_column` is reported missing.
- A CSV appears to have one giant column containing delimiters.
- A header row appears in the output or logs as if it were a molecule.

Fixes:

- For headered CSV/TSV input, use the exact header text in `smiles_column` and the actual delimiter in `separator`.
- For `.smi`/`.smi.gz`, remember input is treated as headerless and `smiles_column` is only an internal synthetic name.
- Run `validate_data_pipeline_config.py CONFIG --sample-rows 10` to inspect the selected column before running preprocessing.
- Convert Excel-exported semicolon or comma files deliberately instead of guessing tab delimiters.

## Invalid SMILES and Filtering Surprises

- Empty SMILES are skipped.
- Invalid RDKit SMILES are removed during chemistry filtering; set `report_errors = true` to log chemistry problems.
- Bracketed charged or high-valent halogens such as `[Cl+]`, `[Br+3]`, `[I-]`, or `[IH]` are rejected by token filtering.
- Unexpected elements are rejected unless they are in the runtime allowed set. REINVENT adds `{C, O, N, S, F, Cl, Br, I}` automatically; add valid symbols such as `B`, `P`, or `Si` in `filter.elements` when intentional.
- `min_carbons`, `min_heavy_atoms`, `max_heavy_atoms`, and `max_mol_weight` are enforced before RDKit cleanup, so strict values can remove otherwise valid molecules.
- `max_num_rings` and `max_ring_size` are enforced after RDKit processing and can remove macrocycles or highly fused scaffolds.

## Transform File Problems

- Built-in `filter.transforms` names include `"standard"` and `"four_valent_nitrogen"`.
- For a custom transform file, set `transform_file = "path/to/transforms.txt"` and include `"from_file"` in `filter.transforms`, unless the file starts with `// TRANSFORM_NAME: custom_name`; then use `"custom_name"`.
- A transform listed in `filter.transforms` that is neither built-in nor the transform-file name raises `Unknown transform`.
- Keep transform files small and review them on a tiny fixture before processing a library.

## Deduplication and Output

- `output_smiles_file` is overwritten by preprocessing. Validate the path before running.
- `regex.smi` is written to the current working directory, not next to the config unless the process starts there.
- Output has no header and no guaranteed order.
- Default deduplication is by final SMILES string; `inchi_key_deduplicate = true` deduplicates by InChIKey and keeps the last associated SMILES.
- If the output is unexpectedly empty, compare input count, regex-stage count, chemistry-stage count, discarded tokens, and RDKit problem messages in the log.

## Multiprocessing and Large Datasets

- Start with `num_procs = 1` to get clearer logs, token counts, and discarded-token summaries.
- Runtime clips `num_procs` to the available core count and logs an adjustment.
- For very large datasets, multiprocessing is used for regex filtering only above an internal large-input threshold; below that, the regex stage uses an in-memory set.
- Increase `chunk_size` only after a representative subset confirms memory and runtime behavior.
- `canonical_tautomer = true` can be much slower; benchmark it on a sample first.

## Hard Synthetic Case to Practice

Create a headered comma CSV with rows like:

- `CCO` as a valid small molecule.
- `CC(=O)Oc1ccccc1C(=O)O` duplicated twice.
- `not_a_smiles` as invalid syntax.
- `c1ccc([SiH3])cc1` with an unexpected element unless `Si` is configured.
- `CC(=O)O[Cl+][O-]` with an unwanted charged halogen token.

A future agent should build a matching config, run the validator, explain which entries fail at static/sample inspection versus runtime regex/RDKit stages, then run `reinvent_datapre` only after the delimiter, column, output path, and element policy are correct.
