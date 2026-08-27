---
name: conversion-inference
description: "Convert SketchCode PNG wireframes to GUI DSL and HTML,
  compile/debug GUI DSL, choose output style, and check inference
  prerequisites."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# conversion-inference

Use this sub-skill when the user wants to convert hand-drawn/wireframe PNGs with SketchCode, batch-convert mockups, use pretrained model artifacts, compile or debug generated `.gui` DSL, or choose between the `default`, `facebook`, and `airbnb` HTML styles.

## Route first

- For model training, dataset preparation, vocabulary construction, or image augmentation, route to the `training-data` sub-skill.
- For BLEU scoring details or standalone evaluation of `.gui` files, route to the `evaluation` sub-skill. This sub-skill only explains how the conversion CLIs expose optional BLEU flags.
- For downloading or checking external pretrained/data assets, route to the parent `sketch-code` asset helper when available. Conversion itself requires a Keras model JSON file and an HDF5 weights file.
- Do not treat arbitrary non-PNG images as valid inputs; SketchCode's conversion sampler rejects filenames without `.png`.

## Minimum operating checklist

1. Confirm the user has PNG input: one `*.png` file for single conversion or a directory containing `*.png` files for batch conversion.
2. Confirm both pretrained/model artifacts exist: `model_json.json`-style model architecture JSON and `weights.h5`-style Keras weights.
3. Choose a style: exactly `default`, `facebook`, or `airbnb`.
4. Choose an output folder. The conversion CLIs create it when missing; existing files with the same sample basename may be overwritten.
5. If the user asks for BLEU during conversion, require matching original `.gui` files and route metric interpretation to `evaluation`.

## References

- [Conversion workflows](references/workflows.md) - safe single-image, batch, and DSL compilation flow.
- [CLI reference](references/cli-reference.md) - public conversion flags, required artifacts, output behavior, and preprocessing facts.
- [DSL and styles](references/dsl-and-styles.md) - supported style names, GUI DSL grammar, known tokens, and compiler behavior.
- [API reference](references/api-reference.md) - distilled `Sampler`, `Compiler`, `Node`, `SamplerUtils`, and BLEU-routing facts.
- [Troubleshooting](references/troubleshooting.md) - missing assets, invalid PNGs, unsupported styles, parsing errors, imports, and output folder issues.

## Bundled helpers

- [scripts/run_conversion.py](scripts/run_conversion.py) is the bundled, validated replacement for the historical conversion entry points. Use it when the user has a SketchCode runtime checkout or importable `classes` package plus model JSON/weights.
- [scripts/compile_tiny_dsl.py](scripts/compile_tiny_dsl.py) validates and compiles a tiny `.gui` token string without requiring TensorFlow/Keras or pretrained weights. It can optionally use a user-provided SketchCode project root for the original compiler, but its `--help` and fallback compiler are self-contained.
