---
name: cli-and-configuration
description: "Use the TIAToolbox console safely: discover commands, choose the
  right workflow owner, quote JSON/YAML configuration, validate
  installs/backends, and troubleshoot CLI startup issues."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# TIAToolbox CLI and Configuration

Use this sub-skill when a user starts from the `tiatoolbox` console, needs command discovery, asks how to build a shell-safe command, or reports CLI/configuration failures. TIAToolbox exposes the console entry point `tiatoolbox=tiatoolbox.cli:main`; start with `tiatoolbox --help` and `tiatoolbox --version` for safe probes.

## Route the Request

- Use `references/cli-reference.md` to map top-level commands and representative flags before constructing commands.
- Use `references/configuration.md` for JSON-list/dict quoting, YAML IO config behavior, device strings, and output naming patterns.
- Use `references/troubleshooting.md` when `tiatoolbox` is missing, imports fail, native libraries/codecs are unavailable, models cannot download, output paths conflict, or visualization ports collide.
- Use `scripts/cli_help_probe.py` for safe timeout-bounded help/version checks that do not need a source checkout.

## Command Ownership

- Route `slide-info`, `slide-thumbnail`, `save-tiles`, and `read-bounds` to `wsi-io` for WSI metadata, reading, tiling, and resolution semantics.
- Route `tissue-mask` and `stain-norm` to `image-preprocessing` for tissue masking, stain normalization, target images, and preprocessing quality decisions.
- Route `patch-predictor`, `semantic-segmentor`, `nucleus-instance-segment`, `nucleus-detector`, `multitask-segmentor`, and `deep-feature-extractor` to `model-inference` for model selection, pretrained weights, IO config semantics, inference output interpretation, and performance tuning.
- Route `visualize` and `show-wsi` to `annotation-visualization` for TileServer/Bokeh usage, annotation overlays, color maps, and browser/server behavior.

## Safe CLI Workflow

1. Probe availability with `python scripts/cli_help_probe.py --commands semantic-segmentor --version` or direct `tiatoolbox --help`.
2. Build commands as argument lists first; shell-quote only at the final boundary with `shlex.quote` or equivalent.
3. Quote JSON arguments as one shell token, especially `--input-resolutions`, `--output-resolutions`, and `--class-dict`.
4. Prefer explicit `--device cpu` for portable examples; use `cuda` or `mps` only after checking the installed torch backend.
5. Choose a new `--output-path` for model commands unless intentionally passing `--overwrite True`, because model preparation rejects an existing output directory.

## What Not To Duplicate Here

This sub-skill should stay CLI-centric. Deep WSI coordinate rules, image preprocessing theory, model output schemas, annotation store usage, and visualization API details belong in their routed workflow sub-skills.
