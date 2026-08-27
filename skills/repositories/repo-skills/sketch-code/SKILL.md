---
name: sketch-code
description: "Operate SketchCode legacy wireframe-to-HTML workflows: conversion,
  training data preparation, BLEU evaluation, assets, and TensorFlow/Keras
  troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# SketchCode

Use this repo skill when the user is working with SketchCode, the legacy proof-of-concept that converts hand-drawn web wireframe PNGs into GUI DSL and compiled HTML using a CNN encoder plus recurrent decoder. It is most useful for task prompts about SketchCode conversion commands, pretrained model assets, paired `.png`/`.gui` training data, model training/fine-tuning, and BLEU evaluation.

## First checks

1. Confirm the task is about SketchCode's historical TensorFlow/Keras code path, not a modern general-purpose vision-language model.
2. Check whether the user has a SketchCode runtime checkout/source root or an environment where the `classes` package is importable. The bundled wrappers accept `--sketchcode-root` so they do not depend on this skill's source-generation checkout.
3. Read [references/environment-and-assets.md](references/environment-and-assets.md) before downloading data/model files or diagnosing install errors.
4. Run [scripts/check_sketch_code_environment.py](scripts/check_sketch_code_environment.py) when importability, model files, or image preprocessing are in doubt.
5. Run [scripts/sketch_code_assets.py](scripts/sketch_code_assets.py) to print/check expected dataset and pretrained model asset locations without downloading anything.

## Route by task

- Use [conversion-inference](sub-skills/conversion-inference/SKILL.md) for converting one PNG or a folder of PNGs to `.gui`/`.html`, checking model JSON/weights prerequisites, selecting `default`/`facebook`/`airbnb` style, or debugging GUI DSL compilation.
- Use [training-data](sub-skills/training-data/SKILL.md) for validating paired `.png`/`.gui` training folders, understanding `vocabulary.vocab`, image preprocessing, destructive train/validation split behavior, model architecture, or guarded training/fine-tuning commands.
- Use [evaluation](sub-skills/evaluation/SKILL.md) for single or batch BLEU scoring of `.gui` files, button-color normalization, prediction trimming, folder pairing behavior, and NLTK/BLEU caveats.
- Use [references/troubleshooting.md](references/troubleshooting.md) for cross-cutting install/import, external asset, legacy Python, OpenCV/TensorFlow/Keras, network, and source-layout issues.
- Use [references/repo-provenance.md](references/repo-provenance.md) before deciding whether this skill is current for another checkout or should be refreshed.

## Legacy constraints to preserve

- The repository is script-style and targets old dependencies: Keras `2.1.2`, TensorFlow `1.4.0`, OpenCV `3.3.0.10`, NumPy `1.13.1`, and related packages.
- There is no packaged console-entry-point metadata; operating workflows historically ran from source scripts. This skill therefore bundles guarded wrappers and validators instead of linking to original source scripts.
- External assets are optional and network-backed: the full synthetic dataset archive is large, and pretrained `model_json.json` plus `weights.h5` are required for actual conversion.
- Full training can be long-running and deletes/recreates sibling `training_set` and `validation_set` folders under the parent of the raw data directory. Always dry-run or validate before training.

## Minimal safe commands

```sh
python scripts/sketch_code_assets.py --root "$SKETCHCODE_ROOT"
python scripts/check_sketch_code_environment.py --sketchcode-root "$SKETCHCODE_ROOT"
python sub-skills/training-data/scripts/validate_training_dataset.py "$DATASET_DIR"
python sub-skills/conversion-inference/scripts/compile_tiny_dsl.py --style default
python sub-skills/evaluation/scripts/evaluate_tiny_gui_bleu.py
```

These helpers are safe by default. They do not download assets, start training, or run model inference unless the user supplies the required runtime paths and explicit command options documented in the sub-skills.
