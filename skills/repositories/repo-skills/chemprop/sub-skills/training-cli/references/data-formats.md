# Training Data Formats

Chemprop CLI training uses CSV input for `chemprop train`. This reference covers molecule-level CSV schemas, target inference, missing labels, split schemas, separate data files, and feature/descriptor alignment.

## Basic CSV Schema

A training CSV normally has a header row:

```csv
smiles,y
CCO,0.5
CCC,1.2
c1ccccc1,-0.3
```

Minimal command:

```bash
chemprop train --data-path data.csv --task-type regression --output-dir runs/demo
```

Default interpretation:

- The first column is the SMILES column.
- Every other column is treated as a target unless excluded by split, weight, descriptor, or ignore flags.
- Targets are parsed as numeric arrays.
- Blank target cells represent missing labels and are masked.

Use `--no-header-row` only for truly headerless CSVs. With headerless data, avoid named-column flags and reason carefully about column order.

## Explicit SMILES And Target Columns

Prefer explicit columns for production commands:

```bash
chemprop train \
  --data-path assays.csv \
  --smiles-columns canonical_smiles \
  --target-columns assay_a assay_b assay_c \
  --task-type classification \
  --output-dir runs/assays
```

For multi-molecule rows, pass multiple SMILES columns:

```bash
chemprop train \
  --data-path solute_solvent.csv \
  --smiles-columns solute_smiles solvent_smiles \
  --target-columns solubility \
  --task-type regression \
  --output-dir runs/solute_solvent
```

Detailed multicomponent architecture and feature routing belongs in `../specialized-molecular-tasks/SKILL.md`.

## Target Inference Rules

If `--target-columns` is omitted, Chemprop infers target columns as all CSV columns except:

- input columns from `--smiles-columns` and/or `--reaction-columns`, or the first column by default;
- columns listed in `--ignore-columns`;
- `--descriptors-columns`;
- `--splits-column`;
- `--weight-column`.

Avoid relying on inference when the CSV has metadata. Either list `--target-columns` or put metadata in `--ignore-columns`.

## Missing Labels

Multitask datasets may have blank target cells:

```csv
smiles,task_a,task_b,task_c
CCO,1,,0
CCC,0,1,
CCCC,,0,1
```

Guidelines:

- Leave genuinely unknown targets blank.
- Do not encode unknown labels as `0`; `0` is a valid regression value or binary negative label.
- For classification, targets should be `0`, `1`, or blank.
- For regression and spectral tasks, targets should be numeric or blank.
- For bounded regression losses, inequality strings such as `<1.5` or `>10` are parsed only with a bounded-loss workflow.

## Classification Data

Binary classification:

```csv
smiles,active,toxic
CCO,1,0
CCC,0,
CCCC,1,1
```

Command:

```bash
chemprop train \
  --data-path classification.csv \
  --smiles-columns smiles \
  --target-columns active toxic \
  --task-type classification \
  --metrics roc prc accuracy f1 \
  --output-dir runs/classification
```

Multiclass classification:

```csv
smiles,class_id
CCO,0
CCC,2
CCCC,1
```

Command:

```bash
chemprop train \
  --data-path multiclass.csv \
  --smiles-columns smiles \
  --target-columns class_id \
  --task-type multiclass \
  --multiclass-num-classes 3 \
  --output-dir runs/multiclass
```

## Spectral Data

Spectral training treats many numeric columns as spectral bins or channels:

```csv
smiles,bin_001,bin_002,bin_003
CCO,0.05,0.20,0.75
CCC,0.10,0.30,0.60
```

Command:

```bash
chemprop train \
  --data-path spectra.csv \
  --smiles-columns smiles \
  --target-columns bin_001 bin_002 bin_003 \
  --task-type spectral \
  --metrics sid wasserstein \
  --output-dir runs/spectral
```

Keep target bin ordering and preprocessing consistent across training and prediction.

## Split Column Schema

A split column can assign each row to `train`, `val`, or `test`:

```csv
smiles,y,split
CCO,1.0,train
CCC,2.0,train
CCCC,3.0,val
CCCCC,4.0,test
```

Command:

```bash
chemprop train \
  --data-path with_splits.csv \
  --smiles-columns smiles \
  --target-columns y \
  --splits-column split \
  --task-type regression \
  --output-dir runs/split_column
```

Do not also include the split column in `--target-columns`. If relying on inference, Chemprop excludes `--splits-column` automatically.

## Split JSON Schema

A split JSON file is a list of dictionaries:

```json
[
  {"train": [0, 1, 2], "val": "3-4", "test": "5,6"}
]
```

Rules:

- Indices refer to CSV row positions after the header and are zero-indexed.
- Ranges are inclusive: `"3-4"` means indices 3 and 4.
- Keys may omit `val` or `test` only if that split is intentionally absent.
- Multiple dictionaries represent multiple replicate split assignments.

Command:

```bash
chemprop train --data-path data.csv --splits-file splits.json --task-type regression --output-dir runs/json_split
```

## Separate CSV Files

`--data-path` can receive one, two, or three CSV files:

- One file: Chemprop splits it according to `--split-type`, `--split-sizes`, and related flags.
- Two files: the first is split into train/validation and the second is test; use `--split-sizes <train> <val> 0.0` unless using split column/file behavior.
- Three files: files are train, validation, and test respectively.

Examples:

```bash
chemprop train --data-path train.csv val.csv test.csv --task-type regression --output-dir runs/three_files
chemprop train --data-path trainval.csv test.csv --split-sizes 0.9 0.1 0.0 --task-type regression --output-dir runs/two_files
```

Separate train/validation/test files are not supported for extra features and descriptors `.npz` files.

## Weights And Ignored Columns

Use `--weight-column` for per-row weights:

```csv
smiles,y,row_weight,batch_id
CCO,1.2,0.8,A
CCC,1.4,1.0,A
```

```bash
chemprop train \
  --data-path weighted.csv \
  --smiles-columns smiles \
  --target-columns y \
  --weight-column row_weight \
  --ignore-columns batch_id \
  --task-type regression \
  --output-dir runs/weighted
```

Use `--ignore-columns` for metadata only when targets are inferred; explicit `--target-columns` is safer.

## Descriptors And Feature Files

CSV descriptor columns:

```bash
chemprop train \
  --data-path descriptors.csv \
  --smiles-columns smiles \
  --target-columns y \
  --descriptors-columns temperature pressure \
  --task-type regression \
  --output-dir runs/descriptors_columns
```

Molecule featurizers:

```bash
chemprop train \
  --data-path data.csv \
  --smiles-columns smiles \
  --target-columns y \
  --molecule-featurizers rdkit_2d \
  --task-type regression \
  --output-dir runs/rdkit2d
```

External `.npz` descriptors/features:

```bash
chemprop train \
  --data-path data.csv \
  --target-columns y \
  --descriptors-path descriptors.npz \
  --atom-features-path atom_features.npz \
  --bond-features-path bond_features.npz \
  --atom-descriptors-path atom_descriptors.npz \
  --task-type regression \
  --output-dir runs/npz_features
```

Alignment requirements:

- `.npz` rows must match CSV row order and row count.
- Atom and bond arrays must match the atoms/bonds produced by the same Chemprop featurization settings.
- Do not sort, filter, deduplicate, or shuffle the CSV without regenerating or transforming feature files the same way.
- When using `--save-data-splits`, Chemprop writes aligned split data/features under the output directory.

## Reaction And Specialized Schemas

Reaction input uses `--reaction-columns` with reaction SMILES such as `REACTANT>AGENT>PRODUCT`. Multicomponent and atom/bond target workflows introduce additional schema flags such as `--mol-target-columns`, `--atom-target-columns`, `--bond-target-columns`, `--constraints-path`, and `--constraints-to-targets`. Route detailed setup to `../specialized-molecular-tasks/SKILL.md`.

## Header And Target-Inference Diagnostics

If training fails during parsing or produces an unexpected target count:

1. Print the header and first rows of the CSV.
2. Identify disjoint roles: input, target, split, weight, descriptor, ignore/metadata.
3. Rebuild the command with explicit `--smiles-columns` and `--target-columns`.
4. Add `--ignore-columns` only for metadata when relying on target inference.
5. Use the bundled command builder with `--check-schema` to warn about missing/overlapping columns and inferred targets.

## Schema Guardrails

Before training, check:

- SMILES/reaction columns are not also target columns.
- Split, weight, descriptor, and metadata columns are not inferred as targets.
- `--target-columns` are present in the CSV header and numeric or blank.
- Classification targets use valid encodings for the selected task type.
- Split fractions are three numbers and intentionally sum to 1.
- Two-file input uses a zero test split fraction unless split column/file behavior intentionally overrides this rule.
- Feature/descriptor `.npz` files are aligned with the CSV and not used with separate train/val/test CSV workflows.
