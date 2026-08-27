# Prediction and Fingerprint Troubleshooting

Use this guide when `chemprop predict` or `chemprop fingerprint` fails or produces unexpected files.

## CLI Availability

Check the installed CLI and subcommands:

```bash
chemprop --help
chemprop predict --help
chemprop fingerprint --help
```

The expected Chemprop command includes subcommands such as `train`, `predict`, `convert`, `fingerprint`, and `hpopt`.

## Input and Output Suffix Errors

Prediction and fingerprint inputs must be CSV files:

```text
--test-path must end in .csv
```

Prediction outputs must be `.csv` or `.pkl`:

```bash
chemprop predict \
  --test-path molecules.csv \
  --model-path model.pt \
  --output preds.csv
```

Fingerprint outputs must be `.csv` or `.npz`:

```bash
chemprop fingerprint \
  --test-path molecules.csv \
  --model-path model.pt \
  --ffn-block-index 0 \
  --output fps.npz
```

If an expected fingerprint output path is missing, remember that Chemprop appends the model index. An output base of `fps.npz` becomes `fps_0.npz` for the first model.

## Missing or Invalid Model Paths

Valid model path entries are:

- `.pt` files.
- `.ckpt` files.
- Directories.

Directories are searched recursively for `.pt` files only. If a directory contains only `.ckpt` checkpoints, either export `.pt` models or pass each checkpoint explicitly:

```bash
chemprop predict \
  --test-path molecules.csv \
  --model-path fold0.ckpt fold1.ckpt fold2.ckpt \
  --output preds.csv
```

If a directory has no `.pt` files, prediction can fail later because no models were collected.

## v1 Featurizer Mismatch Warning

Chemprop v1 and v2 use different default atom feature dimensions. When a v1-style model is predicted with v2 defaults, Chemprop may warn that v1 default featurizer dimensions match the model and suggest:

```bash
--multi-hot-atom-featurizer-mode v1
```

Rerun with that flag when using legacy artifacts:

```bash
chemprop predict \
  --test-path molecules.csv \
  --model-path legacy_model.pt \
  --multi-hot-atom-featurizer-mode v1 \
  --output legacy_preds.csv
```

For production use, prefer converting and validating legacy artifacts before relying on them.

## Featurizer Dimension Mismatch

A hard error comparing featurizer output dimensions to model input dimensions usually means prediction-time flags do not match training-time flags.

Check:

- `--smiles-columns` names and order for multicomponent models.
- `--reaction-columns` and `--rxn-mode` for reaction models.
- `--descriptors-path` or `--descriptors-columns` when descriptors were used.
- `--atom-features-path`, `--atom-descriptors-path`, `--bond-features-path`, and `--bond-descriptors-path` for side features.
- `--keep-h`, `--add-h`, `--ignore-stereo`, and `--reorder-atoms` graph flags.
- `--multi-hot-atom-featurizer-mode` for v1/v2/organic/RIGR atom feature modes.

## Multicomponent and Reaction Flag Mismatch

Chemprop infers component count from `--smiles-columns` and `--reaction-columns`:

- Neither flag: one molecule component from the first CSV column.
- `--smiles-columns a b`: two molecule components.
- `--reaction-columns rxn`: one reaction component.
- Both flags: mixed molecule and reaction components.

A model trained with multiple components needs the same number and order of components at prediction time. A reaction model needs reaction columns, not molecule SMILES columns. If `--reaction-mode` was used during training, reuse the same mode with `--rxn-mode` or `--reaction-mode`.

## Descriptor and Calibration Alignment

For ordinary prediction, descriptor and side-feature files must match the test CSV row order and component order. For uncertainty calibration, calibration files need their own aligned descriptor and side-feature flags such as `--cal-descriptors-path` and `--cal-atom-features-path`.

If calibration and feature alignment are part of the task, route design and interpretation to `uncertainty-advanced`; this sub-skill only keeps the prediction command shape consistent.

## CPU/GPU Checkpoint Loading

When a CUDA-trained checkpoint fails on a CPU-only or different-GPU machine, first force a simple CPU run:

```bash
chemprop predict \
  --test-path molecules.csv \
  --model-path cuda_trained_model.pt \
  --accelerator cpu \
  --devices 1 \
  --num-workers 0 \
  --output preds.csv
```

Use the same flags with `chemprop fingerprint`. Chemprop maps the first model artifact to CPU for metadata inspection, but runtime inference still goes through Lightning trainer settings.

If loading still fails, suspect incompatible package versions, unavailable custom modules, corrupted checkpoint files, or unsupported artifact format.

## Fingerprint Layer or File Confusion

`chemprop fingerprint` requires `--ffn-block-index`. If the target layer is unknown, use `0` first. If the command succeeds but the file name is unexpected, apply Chemprop's naming rules:

- Base `fps.csv` with one model writes `fps_0.csv`.
- Base `fps.npz` with three models writes `fps_0.npz`, `fps_1.npz`, `fps_2.npz`.
- Atom/bond models add kind-specific stems such as `_atom_fingerprints`.

## Debugging Defaults

For reproducible debugging, start with:

```bash
--accelerator cpu --devices 1 --num-workers 0
```

Then add GPU acceleration, worker processes, or optional `--use-cuikmolmaker-featurization` only after the model, data columns, side files, and outputs are known to be correct.
