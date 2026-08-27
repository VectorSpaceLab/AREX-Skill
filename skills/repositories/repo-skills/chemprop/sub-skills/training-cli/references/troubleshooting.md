# Training CLI Troubleshooting

Use this guide for `chemprop train` failures and confusing outputs. Start with the smallest command that reproduces the issue, usually with `--epochs 3 --num-workers 0 --accelerator cpu`.

## Install Or Import Failures

Symptoms:

- `chemprop: command not found`
- `ModuleNotFoundError: No module named 'chemprop'`
- Import errors for `torch`, `lightning`, `rdkit`, or optional packages

Actions:

1. Confirm the active Python environment is intended.
2. Run `python -c "import chemprop; print(chemprop.__version__)"`.
3. Run `chemprop --help` and `chemprop train --help`.
4. Run `pip check` if dependencies look inconsistent.
5. Install optional extras only when needed; ordinary training does not need hpopt/docs/notebook/cuik extras.

Chemprop 2.2.x expects Python 3.11 through less than 3.15.

## CPU Vs CUDA And Lightning Flags

Symptoms:

- CUDA device errors.
- Training unexpectedly uses CPU.
- Lightning accelerator/device parsing errors.
- Multi-GPU device strings are not parsed as expected.

Actions:

- For reliable smoke tests, add `--accelerator cpu`.
- If requesting GPUs, verify PyTorch can see them with `python -c "import torch; print(torch.cuda.is_available())"`.
- Keep `--devices` as a single string accepted by Lightning, for example `--devices '0'` or `--devices '0,1'`.
- Do not assume optional GPU-oriented packages are installed; `cuik_molmaker` is optional.

## Invalid SMILES Or Reaction Strings

Symptoms:

- RDKit parsing warnings.
- Failures during featurization or graph construction.
- Unexpectedly missing datapoints.

Actions:

1. Inspect the input column selected by `--smiles-columns` or `--reaction-columns`.
2. Confirm the column contains molecule SMILES or reaction SMILES as intended.
3. For reactions, strings should be `REACTANT>AGENT>PRODUCT`; route detailed setup to `../specialized-molecular-tasks/SKILL.md`.
4. Test `--ignore-stereo` only if stereochemistry can be discarded scientifically.
5. Choose deliberately between `--keep-h` and `--add-h` if hydrogens matter.

## CSV, Header, And Target Inference Mistakes

Symptoms:

- Key errors for missing columns.
- Non-numeric conversion failures.
- Model trains on metadata columns by accident.
- Target count differs from expectation.
- Header row appears to be treated as data, or data row appears to be treated as header.

Actions:

- Use `--no-header-row` only for headerless data.
- Prefer explicit `--smiles-columns` and `--target-columns` for data with metadata.
- Put metadata in `--ignore-columns` if targets are inferred.
- Ensure `--splits-column`, `--weight-column`, and `--descriptors-columns` are not also targets.
- Confirm target cells are numeric or blank.
- For classification, use `0`, `1`, or blank; for multiclass, use integer class ids.

Example fixed command:

```bash
chemprop train \
  --data-path assays.csv \
  --smiles-columns smiles \
  --target-columns tox_a tox_b \
  --ignore-columns batch_id source_id \
  --splits-column split \
  --task-type classification \
  --output-dir runs/fixed_schema
```

## Overlapping Columns

Symptoms:

- The same column is passed as SMILES and target.
- A split or weight column becomes a target.
- A descriptor column is also predicted.

Actions:

- Treat input, target, ignore, split, weight, and descriptor columns as disjoint roles unless a specialized workflow requires otherwise.
- Run the bundled command builder with `--check-schema` before running Chemprop.
- If a descriptor column should also be predicted, duplicate it in the CSV under a separate target column name.

## Split Fraction Errors

Symptoms:

- Error that test split size should be `0` when a separate test file is supplied.
- Empty validation/test set surprises.
- Split proportions do not match expectations.

Actions:

- Pass exactly three values to `--split-sizes`.
- Use fractions that intentionally sum to 1 for random/scaffold-style splitting.
- With two input CSV paths, set the third split size to `0.0`, for example `--split-sizes 0.9 0.1 0.0`.
- With a split column, ensure values are exactly `train`, `val`, or `test`.
- With split JSON, use zero-indexed indices and inclusive ranges.

## Two-Path And Three-Path Data Semantics

Symptoms:

- A user expects two files to mean train and validation, but Chemprop uses the second as test.
- `--num-replicates` appears ignored with three separate files.
- Extra `.npz` features fail with separate CSVs.

Actions:

- One file means Chemprop creates train/validation/test splits.
- Two files mean first file is split into train/validation and second file is test.
- Three files mean train, validation, and test respectively.
- With three files, replicate splitting is fixed to one direct split.
- Do not use separate train/validation/test CSVs with external feature/descriptor `.npz` workflows.

## Config File Override Surprises

Symptoms:

- A rerun uses unexpected paths, epochs, task type, columns, or metrics.
- `--config-path` run writes output somewhere unexpected.

Actions:

1. Remember that command-line flags override config values.
2. Inspect the generated `config.toml` from the previous output directory.
3. Explicitly pass a new `--output-dir` when reusing a config.
4. Convert the config-based run back into a fully explicit CLI command for debugging.
5. Check whether list-valued arguments from the config are being replaced by command-line list flags.

## Metrics, Losses, And Tracking Metric

Symptoms:

- `Tracking metric must be one of ...`.
- Loss/metric registry lookup errors.
- Early stopping tracks the wrong metric.

Actions:

- Ensure losses and metrics are valid for the selected `--task-type`.
- If using `--tracking-metric` other than `val_loss`, include the metric in `--metrics` unless it is the selected task's default.
- For molecule/atom/bond mixed targets, append `-mol`, `-atom`, or `-bond` to non-default target-specific tracking metrics.
- Use `chemprop train --help` in the target environment to confirm accepted registry names.

## Removed Or Mutually Exclusive Flags

Known validation rules:

- `-k` / `--num-folds` was removed; use `--num-replicates`.
- `--class-balance` only works with `--task-type classification`.
- `--checkpoint` and `--from-foundation` are mutually exclusive.
- `--checkpoint` and deprecated `--model-frzn` are mutually exclusive.
- `--freeze-encoder` requires `--checkpoint`.
- `--frzn-ffn-layers > 0` requires checkpoint/frozen-model setup; with `--checkpoint`, also use `--freeze-encoder`.
- Single-component data accepts only one `--message-hidden-dim` and one `--depth` value.
- `--mpn-shared` cannot be combined with component-specific `--message-hidden-dim` or `--depth` values.

## Foundation And Download Caveats

Symptoms:

- `--from-foundation` model name is not recognized.
- Download/cache failure on first foundation model use.
- Message-passing architecture flags seem ignored.
- CheMeleon rejects feature settings.

Actions:

- Confirm accepted names with `chemprop train --help`.
- Use a local model path with `--from-foundation` if network download is not available.
- Do not combine `--from-foundation` with `--checkpoint`.
- Expect foundation initialization to fix message-passing settings; do not rely on `--depth`, `--message-hidden-dim`, or aggregation flags to change that layer.
- For CheMeleon, keep the V2 atom featurizer mode and avoid external atom/bond feature paths.

## Missing Checkpoint Or Model Artifacts

Symptoms:

- `best.pt` is missing.
- Prediction cannot find a trained model.
- Only intermediate checkpoints exist.

Actions:

1. Confirm training reached the model-save stage and did not fail earlier.
2. Inspect the output structure. Single runs usually write `model_0/best.pt`; replicate/ensemble runs nest under `replicate_<i>/model_<j>/best.pt`.
3. Check whether `--remove-checkpoints` removed intermediate checkpoints, not `best.pt`.
4. If there is no validation/test split, understand that checkpointing and metrics may differ from validation-based runs.
5. Route prediction command construction to `../prediction-fingerprints/SKILL.md`.

## Extra Descriptor Or NPZ Row Mismatch

Symptoms:

- Shape mismatch errors.
- Failures when saving data splits.
- Atom/bond feature array mismatch.

Actions:

- Ensure every `.npz` row corresponds to the same CSV row order.
- Regenerate feature files after filtering, sorting, or deduplicating the CSV.
- Do not use separate train/validation/test CSVs with external `.npz` features/descriptors.
- For atom/bond arrays, ensure feature generation used the same SMILES parsing, hydrogen, stereo, and atom ordering assumptions.

## Optional Extras

Symptoms:

- `cuik-molmaker is not installed`.
- Hpopt dependencies are missing.
- Docs/notebook-only dependencies are missing.

Actions:

- Ordinary `chemprop train` does not require hpopt, docs, notebook, or cuik extras.
- Remove `--use-cuikmolmaker-featurization` unless the optional package is installed and compatible.
- `cuik_molmaker` does not support every featurization path, including common reaction/multicomponent and some atom-ordering flags.
- Route deep hyperparameter optimization setup away from basic training troubleshooting.

## Slow Or Hanging Training

Actions:

- Use `--num-workers 0` for local debugging, Windows, or macOS.
- Start with `--epochs 3` and a small sample to validate schema.
- Use `--batch-size` appropriate for available memory.
- Use `--accelerator cpu` to isolate GPU/driver problems from data/schema problems.
- If scaffold or non-random splitting is expensive, test with random splitting first, then restore the scientific split.
- Add `--no-cache` if graph cache memory is the bottleneck, at the cost of repeated featurization.

## Triage Template

When diagnosing a failed training run, collect:

- Exact `chemprop train ...` command.
- Chemprop version and whether `chemprop train --help` works.
- First 5 CSV header/rows with sensitive values redacted.
- Any config file used and command-line overrides.
- Full error traceback.
- Expected split design and task type.
- Whether optional feature/descriptor `.npz` files are used.
- Expected output artifact, such as `model_0/best.pt` or split files.
