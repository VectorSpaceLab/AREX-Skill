# Model Artifacts for Prediction and Fingerprints

Chemprop prediction and fingerprint workflows consume trained model artifacts created by Chemprop training or conversion workflows. This reference explains how to choose model paths and interpret inference artifacts.

## Accepted Model Path Inputs

`chemprop predict` and `chemprop fingerprint` accept the same model path forms:

- A `.pt` exported model file.
- A `.ckpt` Lightning checkpoint file.
- A directory containing `.pt` model files.
- A list combining files and directories.

The CLI flag names `--model-path` and `--model-paths` are aliases.

Directory discovery is recursive and collects `.pt` files only. A directory containing only `.ckpt` files is not enough; pass checkpoint files explicitly.

## Single Model vs Ensemble Semantics

Prediction:

- One discovered/supplied model writes the requested output only.
- Multiple discovered/supplied models are treated as an ensemble.
- Ensemble prediction writes averaged predictions to the requested output.
- Ensemble prediction also writes `<output_stem>_individual<suffix>` with one set of prediction columns per model.

Fingerprint:

- Fingerprint export writes one output file per model.
- Every output file appends the model index to the output stem.
- Fingerprint export does not average model representations and does not create `_individual` files.

## Output Column Names

Chemprop loads target/output column names from saved model artifacts when available. If output names are missing, prediction columns fall back to generic names such as `pred_0`, `pred_1`, and so on.

Multiclass prediction adds probability-string columns alongside predicted class labels. Per-model ensemble columns append `_model_<index>`.

Atom/bond property models can combine molecule, atom, and bond prediction targets in the same output table. Atom and bond predictions are stored as list-like values per input molecule because the number of atoms or bonds varies by row.

## CPU/GPU Loading Behavior

Chemprop inspects the first model artifact using CPU mapping before running inference. This helps CUDA-trained checkpoints load on CPU-only machines for metadata inspection and model-type detection.

For debugging or portable inference, force CPU execution:

```bash
chemprop predict \
  --test-path molecules.csv \
  --model-path cuda_trained_model.pt \
  --accelerator cpu \
  --devices 1 \
  --num-workers 0 \
  --output preds.csv
```

The same runtime flags can be used for fingerprints:

```bash
chemprop fingerprint \
  --test-path molecules.csv \
  --model-path cuda_trained_model.pt \
  --ffn-block-index 0 \
  --accelerator cpu \
  --devices 1 \
  --num-workers 0 \
  --output fps.npz
```

If a checkpoint still fails because it requires unavailable custom code or incompatible package versions, convert or regenerate the artifact before using it for production inference.

## `.pt` vs `.ckpt` Practical Guidance

Prefer `.pt` files for routine CLI inference because directory discovery finds them recursively and they are the normal model-file target for prediction workflows.

Use `.ckpt` files when:

- The training workflow preserved Lightning checkpoints and no exported `.pt` is available.
- You are validating a checkpoint directly after training.
- A conversion workflow has not yet produced a `.pt` artifact.

Pass `.ckpt` files explicitly; do not rely on directory discovery for checkpoints.

## Featurizer Compatibility Metadata

Prediction builds a dataloader from the current command flags and compares feature dimensions against the loaded model. A mismatch usually means the inference command did not match training.

Common causes:

- Missing or reordered `--smiles-columns` for multicomponent models.
- Missing `--reaction-columns` or wrong `--rxn-mode` for reaction models.
- Missing descriptor or atom/bond feature side files.
- Different `--multi-hot-atom-featurizer-mode` than training.
- Changed hydrogen, stereochemistry, or atom ordering flags.

Chemprop can detect a common legacy mismatch where v1 atom featurizer dimensions match the model. In that case it warns and uses the v1 default featurizer, and the cleaner command is to add:

```bash
--multi-hot-atom-featurizer-mode v1
```

## Artifact Handling Checklist

Before running inference:

- Confirm the model file suffix is `.pt` or `.ckpt`, or the path is a directory.
- If using a directory, confirm it contains `.pt` files recursively.
- Confirm all ensemble members were trained for the same task type and compatible target set.
- Confirm input CSV columns and side files match the training command.
- Confirm optional extras are installed before using optional features such as `--use-cuikmolmaker-featurization`.
- Decide whether output should be portable text (`.csv`) or Python-native (`.pkl` for predictions, `.npz` for fingerprints).
