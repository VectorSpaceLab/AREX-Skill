---
name: prediction-fingerprints
description: "Run Chemprop prediction and fingerprint workflows from trained
  model artifacts, including model-path handling, output formats, ensembles, and
  fingerprint layer choices."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Chemprop Prediction and Fingerprints

Use this sub-skill when an agent needs to run trained Chemprop model artifacts with `chemprop predict` or extract learned encodings with `chemprop fingerprint`. Keep prediction-time command construction, model path discovery, output naming, ensemble individual outputs, fingerprint layer choice, and inference artifact interpretation here.

## When to Use

Use this sub-skill for:

- Building `chemprop predict` commands for CSV inputs and `.pt` or `.ckpt` model artifacts.
- Building `chemprop fingerprint` commands for learned model representations.
- Choosing legal prediction outputs (`.csv`, `.pkl`) or fingerprint outputs (`.csv`, `.npz`).
- Supplying one model, multiple model files, or directories of model files.
- Understanding averaged ensemble outputs and per-model individual output files.
- Reusing training-time parsing and featurization flags during prediction or fingerprint export.
- Diagnosing model path, output suffix, featurizer, reaction, multicomponent, and checkpoint loading failures.

Route elsewhere when the task is:

- Training, split selection, checkpoint creation, or training output layout: use [`training-cli`](../training-cli/SKILL.md).
- Input schema design, descriptors, atom/bond features, or NPZ side-file alignment: use the data-featurization sub-skill if present.
- Uncertainty method selection, calibration design, conformal interpretation, or calibration feature alignment: use [`uncertainty-advanced`](../uncertainty-advanced/SKILL.md).
- Model conversion before inference: use [`uncertainty-advanced`](../uncertainty-advanced/SKILL.md) for conversion and compatibility decisions.
- Custom Python dataloaders or model internals: use the Python API sub-skill if present.

## Quick Prediction Pattern

Minimum prediction command:

```bash
chemprop predict \
  --test-path new_inputs.csv \
  --model-path models/best.pt \
  --output predictions.csv
```

Core rules:

- `--test-path` must be a `.csv` file.
- `--model-path` and `--model-paths` are aliases and accept one or more paths.
- Each model path may be a `.pt` model file, `.ckpt` checkpoint, or directory.
- Directory model paths are searched recursively for `.pt` files only; pass `.ckpt` files explicitly.
- Prediction output may be `.csv` or `.pkl`; if omitted, Chemprop writes `<test_stem>_preds.csv` beside the input.
- With multiple discovered or supplied models, Chemprop writes averaged predictions to the requested output and a second file named `<output_stem>_individual<suffix>` with per-model columns.

See [`references/prediction-workflows.md`](references/prediction-workflows.md) for command patterns and output interpretation.

## Quick Fingerprint Pattern

Minimum fingerprint command:

```bash
chemprop fingerprint \
  --test-path new_inputs.csv \
  --model-path models/best.pt \
  --ffn-block-index 0 \
  --output fingerprints.npz
```

Core rules:

- `--ffn-block-index` is required.
- `--ffn-block-index 0` returns the post-aggregation representation before FFN layers.
- `--ffn-block-index 1` returns the first FFN linear block output; higher valid indexes select later FFN blocks.
- Fingerprint output may be `.csv` or `.npz`; if omitted, Chemprop uses `<test_stem>_fps.csv` as the base output.
- Chemprop appends the model index to every fingerprint output, such as `fingerprints_0.npz`, `fingerprints_1.npz`, or `new_inputs_fps_0.csv`.
- Atom/bond prediction models can emit kind-specific files with `_mol_fingerprints`, `_atom_fingerprints`, and `_bond_fingerprints` in the stem.

See [`references/fingerprint-workflows.md`](references/fingerprint-workflows.md) for layer choice and output handling.

## Match Training-Time Data Flags

Prediction and fingerprint commands must reuse the structure parsing and featurization choices used to train the model. Important flags include:

- `--smiles-columns` for named molecule columns and multicomponent molecule models.
- `--reaction-columns` plus `--rxn-mode`/`--reaction-mode` for atom-mapped reaction SMILES.
- `--descriptors-path` or `--descriptors-columns` for molecule-level descriptors.
- `--atom-features-path`, `--atom-descriptors-path`, `--bond-features-path`, and `--bond-descriptors-path` for side features.
- `--multi-hot-atom-featurizer-mode`, `--keep-h`, `--add-h`, `--ignore-stereo`, and `--reorder-atoms` for graph construction compatibility.

Single-molecule default when neither `--smiles-columns` nor `--reaction-columns` is supplied: Chemprop reads the first CSV column as SMILES.

## Model Artifact Routing

Use [`references/model-artifacts.md`](references/model-artifacts.md) when choosing model paths or interpreting artifacts.

Key facts:

- Chemprop prediction and fingerprint loading first inspect the first model artifact on CPU to detect model type, including atom/bond prediction models.
- `.pt` files are normal exported model artifacts; `.ckpt` files are Lightning checkpoints that can be loaded when passed explicitly.
- Directories are accepted but discover `.pt` files only.
- Prediction target names are loaded from the artifact when available; otherwise outputs use generic names such as `pred_0`, `pred_1`.
- CUDA-trained artifacts can be loaded for CPU prediction because Chemprop loads checkpoint metadata with CPU mapping before inference.

## Bundled Command Builder

Use [`scripts/chemprop_predict_command_builder.py`](scripts/chemprop_predict_command_builder.py) to plan commands without importing Chemprop or loading model files.

Examples:

```bash
python scripts/chemprop_predict_command_builder.py predict \
  --test-path new_inputs.csv \
  --model-path models/ \
  --output predictions.csv \
  --smiles-columns smiles
```

```bash
python scripts/chemprop_predict_command_builder.py fingerprint \
  --test-path new_inputs.csv \
  --model-path models/best.pt \
  --output fingerprints.npz \
  --ffn-block-index 0
```

The helper validates common suffix mistakes, notes model directory discovery behavior, warns about likely parsing mismatches, and can emit JSON with `--json`.

## Troubleshooting First Pass

Use [`references/troubleshooting.md`](references/troubleshooting.md) for failures.

Fast triage:

- Run `chemprop --help`, `chemprop predict --help`, or `chemprop fingerprint --help` to confirm CLI availability.
- Confirm input is `.csv` and output suffix is legal for the selected subcommand.
- Confirm every model path is a `.pt`, `.ckpt`, or directory, and that directory paths contain `.pt` files if relying on recursive discovery.
- Reuse the training-time component columns, reaction mode, descriptors, side features, and featurizer mode.
- If a v1 featurizer mismatch warning appears, rerun with `--multi-hot-atom-featurizer-mode v1` or convert/verify the artifact before production inference.
- Prefer `--accelerator cpu --devices 1 --num-workers 0` while debugging checkpoint loading or multiprocessing issues.
