# Training-data troubleshooting

## Quick triage

Run the safe validator first:

```sh
python sub-skills/training-data/scripts/validate_training_dataset.py DATASET_DIR
```

Use `--strict` when duplicate GUI contents, existing split folders, or other warnings should fail preflight.

## Common failures

| Symptom | Likely cause | Action |
| --- | --- | --- |
| Fewer samples than expected | Missing `.png` or `.gui` pairs. | Validate the raw dataset. The legacy loader only includes stems that have both files and can skip missing pairs silently. |
| Duplicate layouts appear in validation | Duplicate `.gui` content and historical duplicate check behavior. | The legacy code hashes whitespace-stripped GUI text but compares hash strings by identity instead of equality. Use the validator to list duplicate GUI bodies before splitting. |
| Existing `training_set` or `validation_set` disappeared | Legacy split setup deletes and recreates sibling split folders. | Never point `--data_input_path` at a parent where valuable sibling split folders already exist. Stage raw pairs in a scratch parent. |
| `FileNotFoundError` for `../vocabulary.vocab` | `VOCAB_FILE` is resolved relative to the process current working directory. | Prefer the bundled `run_training.py` wrapper, which changes into the runtime `src` directory for real runs; otherwise patch the code to resolve the vocabulary path from the module file. |
| Unknown token or tokenizer mismatch | `.gui` file contains tokens not in the vocabulary, casing differs, or commas/braces are not separated. | Check [data-formats.md](data-formats.md). Normalize whitespace, separate braces/commas, and update the vocabulary only when intentionally retraining with a changed DSL. |
| Fine-tuning starts from scratch unexpectedly | Only one of `--model_json_file` or `--model_weights_file` was provided. | Provide both files. The legacy constructor loads a pretrained model only when both optional paths are non-empty. |
| Keras/TensorFlow import errors | The code targets old APIs and pinned dependencies. | Use a legacy-compatible Python environment. Expect issues with modern TensorFlow/Keras, `fit_generator`, `RMSprop(lr=...)`, and `ModelCheckpoint(period=...)`. |
| OpenCV import or image read failure | Legacy `opencv-python` pin is old, or the PNG is unreadable/corrupt. | Validate with Pillow if available, then test OpenCV separately in the training environment. Re-encode corrupt images as standard PNGs. |
| Training is very slow or runs out of memory | Full training uses 256x256x3 arrays, a CNN/GRU model, augmentation, and many prefix examples per GUI. | Reduce epochs for smoke runs, disable augmentation with `--augment_training_data 0`, use a smaller staged subset, or use suitable accelerator hardware when available. |
| `steps_per_epoch` or `validation_steps` is zero | The dataset has too few GUI tokens relative to `BATCH_SIZE=64`. | Use more samples/tokens or patch the batch/step calculation for tiny smoke experiments. |
| Stale `.npz` alignment looks wrong | Old feature files remain in a split directory or files were manually edited after preprocessing. | Delete generated split folders intentionally, regenerate from raw pairs, and avoid mixing hand-written `.npz` files with fresh split data. |

## Missing pairs

The legacy pair discovery starts from `.gui` files and includes a sample only if a matching `.png` exists. The copy step also requires both files. This means missing pairs reduce the effective dataset without a hard error. The bundled validator reports:

- `.gui` files without matching `.png`.
- `.png` files without matching `.gui`.
- Uppercase or unusual suffixes that the legacy code may not recognize.

## Validation split duplicate behavior

The historical split logic appears intended to keep identical GUI text out of validation by hashing each `.gui` after removing spaces and newlines. However, it compares hash strings with identity semantics rather than value equality. As a result, duplicate GUI text can still be selected as validation, and duplicate leakage can affect metrics or fine-tuning diagnostics.

Use the validator's duplicate report before training. If duplicates are expected, decide whether to keep them, remove them, or group them deliberately in a custom split.

## Destructive split directories

For an input directory named `raw_dataset`, the code creates split folders as siblings of that input directory:

```text
parent/
  raw_dataset/
  training_set/      # deleted first if present
  validation_set/    # deleted first if present
```

The deletion happens before new split files and `.npz` features are written. To avoid surprises:

- Stage raw pairs under a scratch parent.
- Keep model outputs outside the split parent when experimenting.
- Back up any important folder named `training_set` or `validation_set` before running legacy training.
- Do not use an existing fine-tuning dataset directory as both raw input and split output storage.

## Legacy runtime imports

Pinned requirements include old Keras, TensorFlow, OpenCV, NumPy, Pillow, h5py, NLTK, matplotlib, tqdm, and SciPy versions. Modern Python environments may not install or import the exact pins cleanly. Common compatibility fixes include using an older Python, replacing deprecated Keras arguments, or isolating training in a purpose-built environment. Keep these fixes local to the user's working copy; do not encode machine-specific environment paths into reusable instructions.

## VOCAB_FILE relative path issue

`Dataset.load_vocab()` opens `../vocabulary.vocab` directly. Because this is not resolved relative to the module file, the process working directory matters. The bundled `run_training.py` wrapper changes into the SketchCode runtime `src` directory before real training so this relative path resolves to the runtime root. Launching the legacy code from a different working directory can make it look for a vocabulary file outside the runtime tree.

Safe options:

1. Use `scripts/run_training.py` for dry-run planning and guarded real training.
2. Patch `VOCAB_FILE` or `load_vocab()` to resolve from the module or repository root.
3. Pass a custom absolute vocabulary path in a local patch if the workflow must run from another directory.

## Fine-tuning asset checks

For fine-tuning, check that:

- The JSON file is readable and matches the intended model architecture.
- The weights file is readable and compatible with that architecture.
- Both optional flags are supplied together.
- `--model_output_path` points to a new or intentionally reusable output directory.

If the request is actually to download pretrained assets, route to the root asset workflow rather than starting training from this sub-skill.
