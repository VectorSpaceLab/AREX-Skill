---
name: tiatoolbox
description: "Route TIAToolbox tasks for computational pathology image I/O,
  preprocessing, model inference, annotations, visualization, CLI usage, and
  troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# TIAToolbox

Use this repo skill when a user asks about TIAToolbox, `tiatoolbox`, TIA Toolbox, computational pathology workflows, WSI reading, stain normalization, tissue masking, patch extraction, pretrained pathology models, annotation stores, visualization overlays, or the `tiatoolbox` command-line interface.

TIAToolbox is a Python package for digital pathology image analysis. It covers whole-slide image I/O, image preprocessing, model inference, annotation storage/querying, and visualization.

## Quick Setup

Install the public package in a Python environment that matches TIAToolbox requirements:

```bash
python -m pip install tiatoolbox
python - <<'PY'
import tiatoolbox
print(tiatoolbox.__version__)
PY
tiatoolbox --help
```

If a task needs CPU-only Torch wheels or avoids GPU/CUDA packages, plan that before installing broad dependencies. Use `cli-and-configuration` troubleshooting when imports, native image codecs, OpenSlide, Torch, or the console entry point fail.

## Route by Task

- Use `sub-skills/wsi-io/SKILL.md` for WSI/image readers, metadata, resolution units, thumbnails, tiles, multichannel images, read bounds, and registration setup.
- Use `sub-skills/image-preprocessing/SKILL.md` for tissue masks, stain normalization/extraction/augmentation, patch extraction, tile pyramids, and preprocessing checks before inference.
- Use `sub-skills/model-inference/SKILL.md` for patch prediction, feature extraction, semantic segmentation, nucleus detection, multitask segmentation, pretrained model keys, IO configs, devices, weights, and outputs.
- Use `sub-skills/annotation-visualization/SKILL.md` for `AnnotationStore`, `SQLiteStore`, `DictionaryStore`, DSL filters, GeoJSON/dat overlays, graph overlays, tile servers, visualization layouts, and port/overlay issues.
- Use `sub-skills/cli-and-configuration/SKILL.md` for console command discovery, shell-safe command construction, JSON/YAML quoting, install validation, device/backend selection, and CLI startup troubleshooting.

## Common Workflows

- **Read a WSI or image region:** route to `wsi-io`; confirm input format, reader choice, resolution units, metadata availability, crop bounds, and memory-safe output size.
- **Prepare image data:** route to `image-preprocessing`; choose tissue mask method, stain normalizer, patch extractor mode, mask resolution, stride, and validation checks.
- **Run pretrained or custom inference:** route to `model-inference`; validate model key or custom model, avoid unwanted weight downloads, choose device, construct IO config, and decide output type.
- **Inspect model outputs:** route to `annotation-visualization`; validate annotation properties/geometry, filter expressions, overlay naming, color mapping, and server launch constraints.
- **Build a command:** route first to `cli-and-configuration`; then cross-link to the owning workflow sub-skill for data semantics and troubleshooting.

## Safe Helper Scripts

Each sub-skill bundles helper scripts that future agents can run after TIAToolbox is installed:

- `sub-skills/wsi-io/scripts/wsi_io_smoke.py` checks tiny in-memory `VirtualWSIReader` behavior without WSI downloads.
- `sub-skills/image-preprocessing/scripts/preprocessing_smoke.py` checks maskers, stain normalizers, and patch extraction on tiny arrays.
- `sub-skills/model-inference/scripts/model_registry_probe.py` summarizes the installed pretrained model registry without importing models or downloading weights.
- `sub-skills/annotation-visualization/scripts/annotation_store_smoke.py` checks in-memory annotation stores without launching visualization servers.
- `sub-skills/cli-and-configuration/scripts/cli_help_probe.py` runs timeout-bounded `tiatoolbox --help` and subcommand help probes.

## Troubleshooting First Moves

- For `ModuleNotFoundError`, `tiatoolbox: command not found`, native codec/OpenSlide failures, or CUDA/MPS/Torch mismatches, start with `sub-skills/cli-and-configuration/references/troubleshooting.md`.
- For incorrect crop sizes, missing objective power, unsupported WSI formats, or multichannel axis surprises, read `sub-skills/wsi-io/references/troubleshooting.md`.
- For zero patches, mask mismatch, invalid stain matrices, or stride/shape confusion, read `sub-skills/image-preprocessing/references/troubleshooting.md`.
- For model key typos, unexpected downloads, output-type mistakes, or deprecated nucleus instance segmentation APIs, read `sub-skills/model-inference/references/troubleshooting.md`.
- For overlay visibility, annotation filter errors, large annotation lag, or visualization port conflicts, read `sub-skills/annotation-visualization/references/troubleshooting.md`.

## Freshness and Routing Metadata

- Read `references/repo-provenance.md` when deciding whether this skill is stale against a newer TIAToolbox checkout.
- `references/repo-routing-metadata.json` is structured metadata for the managed `repo-skills-router` import process.

## Boundaries

This skill is for using TIAToolbox as a package and understanding its public workflows. For repository contribution tasks such as changing tests, packaging, release automation, Docker matrices, or benchmarks, prefer a Python repository-maintenance route instead of this user-facing TIAToolbox workflow skill.
