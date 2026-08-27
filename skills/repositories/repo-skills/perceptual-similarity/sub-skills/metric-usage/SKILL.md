---
name: metric-usage
description: "Routes LPIPS pairwise comparison, directory comparison, spatial
  maps, and LPIPS-loss optimization workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 2-Clause
---

# Metric Usage

Use this sub-skill when the request is about comparing images or using LPIPS as a perceptual loss.

## Trigger phrases

- "compare these two images"
- "which image is closer"
- "run LPIPS on two folders"
- "show the spatial map"
- "optimize an image with LPIPS"
- "use perceptual loss"

## What this route covers

- Single image-pair distance checks.
- Directory-pair comparison on matching filenames.
- All-pairs comparison within one directory.
- LPIPS spatial maps.
- A bounded LPIPS optimization demo.

## What this route excludes

- BAPPS 2AFC/JND scoring.
- Dataset download and split management.
- Training and checkpointing.

If the user wants benchmark scoring or training, route to the BAPPS sub-skills instead.

## Read these next

- `references/workflows.md` for the command matrix and safe defaults.
- `references/troubleshooting.md` for normalization, backend, and plotting issues.
- `../../references/api-reference.md` for the verified LPIPS API surface.

## Run these helpers

- `scripts/compare_images.py` for pair, directory-pair, and all-pairs LPIPS comparisons.
- `scripts/optimize_lpips.py` for a bounded perceptual-loss optimization demo.

The helpers default to the bundled example assets under `../../assets/examples/`, so they remain usable even when the original repository checkout is gone.

## Working assumptions

- Inputs should be RGB images.
- LPIPS expects tensors scaled to `[-1, 1]`; the helper scripts handle the conversion for file inputs.
- `spatial=True` returns a map rather than a single scalar, so use the spatial-map output when you want localization.
- The first LPIPS use may download torchvision backbone weights if they are not cached yet.
