# Prediction Workflows

This reference covers `chemprop predict` for inference with trained Chemprop v2 model files and checkpoints.

## Required Inputs

A prediction command needs:

- `--test-path`: CSV file containing molecule SMILES, reaction SMILES, or component columns.
- `--model-path`/`--model-paths`: one or more `.pt` files, `.ckpt` files, or directories.
- `--output`/`--preds-path`: optional output path. Use `.csv` or `.pkl` only.

Minimal single-model prediction:

```bash
chemprop predict \
  --test-path test.csv \
  --model-path model.pt \
  --output preds.csv
```

If `--output` is omitted, Chemprop writes `<test_stem>_preds.csv` beside `--test-path`.

## Model Path Patterns

Single exported model:

```bash
chemprop predict \
  --test-path molecules.csv \
  --model-path checkpoints/best.pt \
  --output molecules_preds.csv
```

Explicit checkpoint:

```bash
chemprop predict \
  --test-path molecules.csv \
  --model-path checkpoints/last.ckpt \
  --output checkpoint_preds.csv
```

Directory of exported models:

```bash
chemprop predict \
  --test-path molecules.csv \
  --model-path ensemble_models/ \
  --output ensemble_preds.csv
```

Directory behavior is recursive and collects `.pt` files only. If an ensemble includes `.ckpt` checkpoints, list each checkpoint explicitly:

```bash
chemprop predict \
  --test-path molecules.csv \
  --model-path fold0.ckpt fold1.ckpt fold2.ckpt \
  --output ensemble_preds.csv
```

## Output Files and Columns

Prediction output format is selected by suffix:

- `.csv`: CSV output with original input columns plus prediction columns.
- `.pkl`: pandas pickle output with original input columns plus prediction columns.

For one model, Chemprop writes only the requested output. For multiple supplied or discovered model artifacts, Chemprop writes:

- `<output>`: averaged predictions across models.
- `<output_stem>_individual<suffix>`: per-model predictions.

Per-model columns are named by appending the model index, such as `solubility_model_0`, `solubility_model_1`, or generic `pred_0_model_0` when target names are unavailable. For multiclass models, Chemprop also writes probability-string columns such as `<target>_prob` or `<target>_prob_model_0`.

Use `--drop-extra-columns` when the final CSV should contain only structure columns and newly generated prediction columns instead of preserving every original input column.

## Molecule, Multicomponent, and Reaction Inputs

Default single-molecule CSV parsing reads the first column:

```bash
chemprop predict \
  --test-path molecules.csv \
  --model-path model.pt \
  --output preds.csv
```

Named molecule column:

```bash
chemprop predict \
  --test-path molecules.csv \
  --smiles-columns smiles \
  --model-path model.pt \
  --output preds.csv
```

Multicomponent molecule model:

```bash
chemprop predict \
  --test-path pairs.csv \
  --smiles-columns solute solvent \
  --model-path pair_model.pt \
  --output pair_preds.csv
```

Reaction model:

```bash
chemprop predict \
  --test-path reactions.csv \
  --reaction-columns rxn_smiles \
  --rxn-mode REAC_DIFF \
  --model-path reaction_model.pt \
  --output reaction_preds.csv
```

Mixed molecule and reaction components are possible when that is how the model was trained:

```bash
chemprop predict \
  --test-path mixed.csv \
  --smiles-columns catalyst \
  --reaction-columns rxn_smiles \
  --rxn-mode REAC_PROD \
  --model-path mixed_model.pt \
  --output mixed_preds.csv
```

The prediction command must match training-time component order. A model trained with `--smiles-columns solute solvent` should not be predicted with `--smiles-columns solvent solute` unless the model was intentionally trained in that order.

## Extra Descriptors and Features

Reuse the same descriptor and side-feature family used during training:

```bash
chemprop predict \
  --test-path molecules.csv \
  --smiles-columns smiles \
  --descriptors-path descriptors.npz \
  --atom-features-path atom_features.npz \
  --bond-features-path bond_features.npz \
  --model-path model_with_features.pt \
  --output preds.csv
```

For multicomponent side features, use component-index/path pairs:

```bash
chemprop predict \
  --test-path pairs.csv \
  --smiles-columns solute solvent \
  --atom-features-path 0 solute_atom_features.npz \
  --atom-features-path 1 solvent_atom_features.npz \
  --model-path pair_model.pt \
  --output pair_preds.csv
```

The row order and component order of every side file must match `--test-path`. Calibration-specific feature alignment belongs with uncertainty workflows, but prediction still needs matching normal test descriptors and side features.

## Featurizer Compatibility Flags

Common graph construction flags that must match training include:

- `--multi-hot-atom-featurizer-mode V1`, `V2`, `ORGANIC`, or `RIGR`.
- `--keep-h` for preserving explicit hydrogens.
- `--add-h` for adding hydrogens.
- `--ignore-stereo` for ignoring stereochemistry.
- `--reorder-atoms` for atom-map based ordering.
- `--molecule-featurizers morgan_binary`, `morgan_count`, `rdkit_2d`, `v1_rdkit_2d`, `v1_rdkit_2d_normalized`, or `charge` when used as extra descriptors.

Chemprop can detect one common v1/v2 atom featurizer mismatch. If it logs a warning that v1 default featurizer dimensions match the model, rerun explicitly with:

```bash
chemprop predict \
  --test-path molecules.csv \
  --model-path legacy_model.pt \
  --multi-hot-atom-featurizer-mode v1 \
  --output legacy_preds.csv
```

## Optional Acceleration and Runtime Flags

For ordinary debugging, prefer deterministic CPU settings:

```bash
chemprop predict \
  --test-path molecules.csv \
  --model-path model.pt \
  --accelerator cpu \
  --devices 1 \
  --num-workers 0 \
  --output preds.csv
```

For large single-component molecule datasets, Chemprop can use optional `cuik-molmaker` featurization when the extra package is installed:

```bash
chemprop predict \
  --test-path molecules.csv \
  --smiles-columns smiles \
  --model-path model.pt \
  --use-cuikmolmaker-featurization \
  --output fast_preds.csv
```

This accelerated path does not support `--keep-h`, `--ignore-stereo`, `--reorder-atoms`, reaction columns, or multicomponent molecule columns.

## Prediction-Time Uncertainty Routing

This sub-skill can assemble flags, but uncertainty method choice and calibration interpretation belong to `uncertainty-advanced`.

Command shape:

```bash
chemprop predict \
  --test-path test.csv \
  --cal-path calibration.csv \
  --model-path model0.pt model1.pt \
  --uncertainty-method ensemble \
  --calibration-method zscaling \
  --evaluation-methods nll-regression spearman \
  --output preds_with_uncertainty.csv
```

Prediction outputs add `<target>_unc` columns for most uncertainty methods. Evaluation metric values are logged to the console when targets are present in `--test-path`.
