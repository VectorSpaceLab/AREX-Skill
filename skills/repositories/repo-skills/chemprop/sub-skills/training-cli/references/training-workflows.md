# Chemprop CLI Training Workflows

These command patterns assume Chemprop 2.2.x is installed and available as `chemprop`. Use `--epochs 3 --num-workers 0 --accelerator cpu` for local smoke tests, then remove or adjust those flags for full training.

## Minimal Regression

Input CSV:

```csv
smiles,solubility
CCO,-0.1
c1ccccc1,-1.3
```

Command:

```bash
chemprop train \
  --data-path data/regression.csv \
  --task-type regression \
  --output-dir runs/regression
```

If `--task-type` is omitted, Chemprop defaults to `regression`; keeping it explicit avoids accidental defaults when commands are reused.

## Explicit Columns And Multitask Targets

By default, Chemprop uses the first CSV column as SMILES and infers targets from remaining non-special columns. For production training, name the schema explicitly:

```bash
chemprop train \
  --data-path data/toxicity.csv \
  --smiles-columns smiles \
  --target-columns NR_AR NR_AhR SR_p53 \
  --task-type classification \
  --metrics roc prc accuracy f1 \
  --tracking-metric prc \
  --output-dir runs/toxicity_multitask
```

Blank target cells are valid missing labels. Do not replace unknown binary labels with `0` unless `0` is truly a negative label.

## Binary Classification

Binary classification targets should contain `0`, `1`, or blanks:

```bash
chemprop train \
  --data-path data/classification.csv \
  --smiles-columns smiles \
  --target-columns active inactive_assay2 \
  --task-type classification \
  --metrics roc prc accuracy f1 \
  --tracking-metric roc \
  --class-balance \
  --output-dir runs/classification
```

Use `--class-balance` only with `classification`; validation rejects it for regression, multiclass, and spectral tasks.

## Multiclass Classification

Multiclass labels are integer class ids, not one-hot columns. Set class count when needed:

```bash
chemprop train \
  --data-path data/multiclass.csv \
  --smiles-columns smiles \
  --target-columns assay_class \
  --task-type multiclass \
  --multiclass-num-classes 5 \
  --metrics ce multiclass-mcc \
  --tracking-metric ce \
  --output-dir runs/multiclass
```

For `multiclass-dirichlet`, keep training command construction here and route uncertainty interpretation/calibration to `../uncertainty-advanced/SKILL.md`.

## Spectral Training

Spectral training treats all target columns together as a spectrum:

```bash
chemprop train \
  --data-path data/spectra.csv \
  --smiles-columns smiles \
  --target-columns bin_001 bin_002 bin_003 bin_004 \
  --task-type spectral \
  --loss-function sid \
  --metrics sid wasserstein \
  --tracking-metric sid \
  --output-dir runs/spectral
```

Keep spectral preprocessing, bin ordering, and normalization consistent with the scientific task. Spectral behavior is more specialized than ordinary scalar multitask regression.

## Regression Variants

Chemprop exposes regression variants through task types and losses:

```bash
chemprop train \
  --data-path data/regression.csv \
  --smiles-columns smiles \
  --target-columns y \
  --task-type regression-evidential \
  --evidential-regularization 0.2 \
  --metrics rmse mae \
  --tracking-metric rmse \
  --output-dir runs/evidential_regression
```

Other variants include `regression-mve` and `regression-quantile`. Training flags belong here; uncertainty calibration and interval interpretation belong in `../uncertainty-advanced/SKILL.md`.

## Random And Scaffold Splits

Random splitting is the default:

```bash
chemprop train \
  --data-path data/regression.csv \
  --task-type regression \
  --split-type random \
  --split-sizes 0.8 0.1 0.1 \
  --data-seed 13 \
  --output-dir runs/random_split
```

For scaffold-separated molecules:

```bash
chemprop train \
  --data-path data/regression.csv \
  --task-type regression \
  --split-type scaffold_balanced \
  --split-sizes 0.8 0.1 0.1 \
  --data-seed 13 \
  --output-dir runs/scaffold_split
```

Other split choices may include `random_with_repeated_smiles`, `kennard_stone`, and `kmeans`; confirm exact choices with `chemprop train --help` in the target environment.

## User Split Column

Use a CSV split column for externally controlled assignments:

```csv
smiles,y,split
CCO,1.2,train
CCC,1.7,val
CCCC,2.1,test
```

```bash
chemprop train \
  --data-path data/with_splits.csv \
  --smiles-columns smiles \
  --target-columns y \
  --splits-column split \
  --task-type regression \
  --output-dir runs/user_split
```

Split values should be `train`, `val`, or `test`. The split column is excluded from inferred targets when `--splits-column` is provided.

## Split JSON File

A split JSON file is a list of dictionaries with zero-indexed assignments:

```json
[
  {"train": [0, 1], "val": "2-3", "test": "4,5"},
  {"val": [0, 1], "test": "2-3", "train": "4,5"}
]
```

Command:

```bash
chemprop train \
  --data-path data/regression.csv \
  --task-type regression \
  --splits-file splits.json \
  --output-dir runs/json_splits
```

Ranges are inclusive, so `[0, 1]`, `"0-1"`, and `"0,1"` are equivalent. A dictionary may omit `val` or `test` only when intentionally training without that split.

## Separate Train/Validation/Test Files

Three paths map directly to train, validation, and test:

```bash
chemprop train \
  --data-path train.csv val.csv test.csv \
  --task-type regression \
  --output-dir runs/separate_three_files
```

Two paths mean the first file is split into train/validation and the second is used as the test set. Set the test split fraction to zero unless using a split column/file:

```bash
chemprop train \
  --data-path trainval.csv test.csv \
  --task-type regression \
  --split-sizes 0.9 0.1 0.0 \
  --output-dir runs/separate_test_file
```

Separate train/validation/test CSVs are not supported for extra features and descriptors `.npz` files.

## Replicates And Ensembles

`--num-replicates` repeats split/training trials. `--ensemble-size` trains multiple models per split:

```bash
chemprop train \
  --data-path data/classification.csv \
  --task-type classification \
  --split-type random \
  --num-replicates 3 \
  --ensemble-size 2 \
  --metrics roc prc \
  --output-dir runs/replicate_ensemble
```

Expect nested outputs such as `replicate_2/model_1/best.pt`. Prediction workflows should point to the desired `best.pt`, checkpoint directory, or collection of model paths according to `../prediction-fingerprints/SKILL.md`.

## Config File Workflow

Every successful training run writes `config.toml` into the output directory. Reuse it with deliberate command-line overrides:

```bash
chemprop train \
  --config-path runs/regression/config.toml \
  --epochs 10 \
  --output-dir runs/regression_rerun
```

Command-line flags override config-file values. When diagnosing config surprises, convert the config run back into an explicit CLI command and compare paths, task type, columns, metrics, split flags, and output directory.

## Transfer Learning And Foundation Initialization

Use an existing Chemprop model/checkpoint to initialize weights:

```bash
chemprop train \
  --data-path data/regression.csv \
  --task-type regression \
  --checkpoint previous_runs/model_0/best.pt \
  --freeze-encoder \
  --frzn-ffn-layers 1 \
  --output-dir runs/transfer
```

Rules:

- `--freeze-encoder` requires `--checkpoint`.
- `--frzn-ffn-layers` requires checkpoint/frozen-model setup; with `--checkpoint`, also use `--freeze-encoder`.
- `--checkpoint` and `--from-foundation` are mutually exclusive.
- Checkpoint-based initialization expects compatible architecture.

Foundation initialization:

```bash
chemprop train \
  --data-path data/small_regression.csv \
  --smiles-columns smiles \
  --target-columns y \
  --task-type regression \
  --from-foundation chemeleon \
  --output-dir runs/foundation_finetune
```

Foundation caveats:

- Named foundation models may download on first use and require network/cache availability.
- Foundation initialization fixes message-passing configuration; message-passing flags such as `--depth`, `--message-hidden-dim`, and `--aggregation` may be ignored.
- CheMeleon requires the V2 atom featurizer mode and does not support external atom/bond feature paths.
- A local `.pt` model path can be passed to `--from-foundation` for FFN reinitialization while reusing message passing.

## Extra Descriptors And Features

For tabular descriptors embedded in the CSV:

```bash
chemprop train \
  --data-path data/descriptors_in_csv.csv \
  --smiles-columns smiles \
  --target-columns y \
  --descriptors-columns temperature pressure \
  --task-type regression \
  --output-dir runs/descriptors_columns
```

For molecule featurizers:

```bash
chemprop train \
  --data-path data/regression.csv \
  --smiles-columns smiles \
  --target-columns y \
  --molecule-featurizers rdkit_2d \
  --task-type regression \
  --output-dir runs/rdkit2d
```

Available molecule featurizers include `morgan_binary`, `morgan_count`, `rdkit_2d`, `v1_rdkit_2d`, `v1_rdkit_2d_normalized`, and `charge` in verified installs. External `.npz` descriptors/features must align row-for-row with the CSV.

## Output Auditing

Add split-saving flags when reproducibility matters:

```bash
chemprop train \
  --data-path data/regression.csv \
  --task-type regression \
  --save-smiles-splits \
  --save-data-splits \
  --output-dir runs/audited_split
```

Audit `config.toml`, `splits.json`, split CSVs, `model_*/best.pt`, `model_*/checkpoints/last.ckpt`, `model_*/trainer_logs/`, and `model_*/test_predictions.csv` when a test split exists.

## Hpopt Handoff

`chemprop hpopt` reuses training arguments and adds Ray Tune search controls. Build and validate the training part first, then adapt:

```bash
chemprop hpopt \
  --data-path data/regression.csv \
  --smiles-columns smiles \
  --target-columns y \
  --task-type regression \
  --epochs 20 \
  --metrics rmse mae \
  --tracking-metric rmse \
  --search-parameter-keywords basic learning_rate \
  --raytune-num-samples 20 \
  --hpopt-save-dir runs/hpopt_regression
```

Handoff notes:

- Hpopt requires optional Ray Tune/search dependencies; ordinary `chemprop train` does not.
- Search keywords include `basic`, `learning_rate`, and `all`, plus individual supported hyperparameters.
- `--tracking-metric` also controls hpopt objective selection.
- Deep Ray Tune scheduler/resource/search-space design belongs in `../uncertainty-advanced/SKILL.md` or a dedicated hpopt skill if present.
