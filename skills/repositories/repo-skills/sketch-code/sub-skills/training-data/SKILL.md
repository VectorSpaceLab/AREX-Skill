---
name: training-data
description: "Prepare, validate, and train SketchCode paired PNG/GUI datasets,
  including vocabulary, preprocessing, model architecture, and legacy training
  troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# SketchCode training-data

Use this sub-skill when the task involves preparing paired SketchCode training data, validating `.png`/`.gui` layouts, understanding `vocabulary.vocab`, running or adapting legacy training, fine-tuning from model JSON/weights, inspecting image preprocessing, or explaining the CNN-plus-GRU model structure.

## Route here for

- Training SketchCode from scratch or from existing `model_json.json` and weights.
- Checking a flat dataset of paired `sample_id.png` and `sample_id.gui` files before training.
- Debugging `training_set`, `validation_set`, `.npz` feature outputs, augmentation, or validation split surprises.
- Explaining vocabulary tokens, GUI DSL tokenization, sequence generation, and model save files.

## Route elsewhere

- Converting wireframe PNGs to `.gui` or HTML belongs to `conversion-inference`.
- BLEU scoring or comparing predicted/original `.gui` files belongs to `evaluation`.
- Downloading public data or pretrained model assets belongs to the root SketchCode asset workflow, not this training sub-skill.

## Operating sequence

1. Read [references/data-formats.md](references/data-formats.md) to confirm the dataset shape, vocabulary, tokenization, and preprocessing outputs.
2. Run the bundled validator before expensive or destructive training:

   ```sh
   python sub-skills/training-data/scripts/validate_training_dataset.py DATASET_DIR
   ```

3. Use the guarded bundled training wrapper when a real run is requested; it dry-runs by default and requires explicit destructive-split acknowledgement:

   ```sh
   python sub-skills/training-data/scripts/run_training.py --help
   ```

4. Read [references/training-workflow.md](references/training-workflow.md) before launching training; it explains command templates, flags/defaults, fine-tuning inputs, and the destructive split directory behavior.
5. Read [references/model-overview.md](references/model-overview.md) when the task asks about architecture, optimizer, callbacks, saved files, sequence lengths, or memory expectations.
6. Use [references/api-reference.md](references/api-reference.md) for a concise source-level API and CLI map.
7. If anything fails, start with [references/troubleshooting.md](references/troubleshooting.md), especially for missing pairs, duplicate GUI layouts, legacy TensorFlow/Keras/OpenCV imports, and the `VOCAB_FILE` relative-path issue.

## Safety defaults

- Validate first; full training is long-running and mutates filesystem state.
- Stage data in a scratch parent directory. The legacy split code deletes and recreates sibling `training_set` and `validation_set` directories under the parent of `--data_input_path`.
- Do not fine-tune in-place inside a directory that contains important `training_set` or `validation_set` folders.
- Use the bundled wrapper's dry-run output to inspect the split directories and model output location before passing `--run --allow-destructive-split`.
