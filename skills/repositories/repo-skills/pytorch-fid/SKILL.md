---
name: pytorch-fid
description: "Use pytorch-fid to compute Frechet Inception Distance for image
  directories or saved activation statistics, precompute .npz stats, validate
  inputs, and troubleshoot PyTorch Inception FID workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# pytorch-fid

Use this repo skill when a task involves `pytorch-fid`, the `pytorch_fid`
Python package, Frechet Inception Distance (FID), image dataset quality
comparison, GAN or diffusion sample evaluation, Inception feature dimensions, or
`.npz` activation-statistics files produced by this package.

## First checks

1. Confirm the public package and import name:
   - package/distribution: `pytorch-fid`
   - import package: `pytorch_fid`
   - console script: `pytorch-fid`
   - module CLI: `python -m pytorch_fid`
2. Run the safe environment probe before giving install or runtime advice:
   ```bash
   python scripts/check_pytorch_fid_env.py
   ```
   Add `--json` when a machine-readable report is needed.
3. If the task depends on the source snapshot, read
   [`references/repo-provenance.md`](references/repo-provenance.md).
4. If the task is about router selection or when this skill should load, read
   [`references/repo-routing-metadata.json`](references/repo-routing-metadata.json).
5. For first-run or failure diagnosis, start with
   [`references/troubleshooting.md`](references/troubleshooting.md).

Minimal import smoke:

```python
from pytorch_fid.fid_score import calculate_fid_given_paths
from pytorch_fid.inception import InceptionV3
```

The import smoke must not construct `InceptionV3` unless a model download/cache
check is explicitly allowed. The bundled scripts avoid model construction.

## When to read this skill

Read this skill when the user asks to:

- compute FID between two image directories;
- precompute one dataset's Inception statistics for later comparisons;
- compare an image directory against a saved `.npz` statistics file;
- call the `pytorch_fid.fid_score` APIs from Python;
- select `--dims` values `64`, `192`, `768`, or `2048`;
- choose CPU, CUDA device strings, batch size, or DataLoader worker count;
- validate whether directories and `.npz` files are compatible before running;
- troubleshoot unsupported image files, empty directories, CUDA/OOM, missing
  weights, shape mismatches, singular covariances, or non-comparable scores.

Avoid this skill when the task is only generic image preprocessing, generic
PyTorch model training, TensorFlow FID code, CLIP-based image metrics, or repo
maintenance unrelated to using the packaged FID workflows.

## Route map

Use the bundled references instead of returning long inline explanations:

- CLI commands, flags, positional path combinations, output, and gotchas:
  [`references/cli-reference.md`](references/cli-reference.md)
- Python API signatures, return shapes, and Inception layer selection:
  [`references/api-reference.md`](references/api-reference.md)
- Input directory and `.npz` data contract:
  [`references/data-formats.md`](references/data-formats.md)
- End-to-end operating recipes and validation-first flows:
  [`references/workflows.md`](references/workflows.md)
- Cross-cutting failure symptoms, causes, and recoveries:
  [`references/troubleshooting.md`](references/troubleshooting.md)
- Provenance and evidence snapshot:
  [`references/repo-provenance.md`](references/repo-provenance.md)

Use bundled scripts for safe checks:

- [`scripts/check_pytorch_fid_env.py`](scripts/check_pytorch_fid_env.py): import,
  package metadata, CLI help, torch/torchvision, and optional CUDA availability.
- [`scripts/validate_fid_inputs.py`](scripts/validate_fid_inputs.py): validate two
  FID input paths as image directories or `.npz` statistics files.
- [`scripts/inspect_stats_npz.py`](scripts/inspect_stats_npz.py): summarize saved
  statistics files and check their `mu`/`sigma` arrays.

## Core operating workflow

1. Identify the two comparison inputs. Each input can be an image directory or a
   `.npz` file containing saved activation statistics. If both are directories,
   the package computes statistics for both in the same run.
2. Validate inputs before constructing a model:
   ```bash
   python scripts/validate_fid_inputs.py INPUT_A INPUT_B --expected-dims 2048
   ```
   Omit `--expected-dims` when the intended feature dimension is not known yet.
3. Choose the feature dimension. Default is `2048`; lower dimensions (`64`,
   `192`, `768`) are faster but not directly comparable to `2048` scores.
4. Choose device and batch parameters. Start with CPU or `--device cuda:0` only
   after verifying CUDA availability; reduce `--batch-size` for memory errors.
5. Run via CLI for ordinary comparisons:
   ```bash
   python -m pytorch_fid PATH_A PATH_B --dims 2048 --batch-size 50
   ```
6. Precompute reusable reference statistics when one dataset is reused often:
   ```bash
   python -m pytorch_fid --save-stats DATASET_DIR reference_stats.npz
   ```
7. Compare generated images against saved stats:
   ```bash
   python -m pytorch_fid GENERATED_DIR reference_stats.npz --dims 2048
   ```
8. For Python integration, prefer the public functions in
   [`references/api-reference.md`](references/api-reference.md) and keep path,
   dimension, and device checks explicit in the calling code.

## Important constraints

- Supported image extensions are `bmp`, `jpg`, `jpeg`, `pgm`, `png`, `ppm`,
  `tif`, `tiff`, and `webp`; use lowercase suffixes for reliable source
  matching across platforms.
- Saved stats must contain finite `mu` and `sigma` arrays; `sigma` must be a
  square covariance matrix whose side length matches `mu` length.
- The first real FID run may download Inception weights unless they are already
  available in the PyTorch cache. Do not treat a network failure as an input
  validation failure.
- Scores are comparable only when the same package/version, preprocessing,
  Inception weights, feature dimension, and dataset conventions are used.
- The README warns that scores are not exactly comparable with the official
  TensorFlow FID implementation.
- CPU is a valid backend for correctness checks; CUDA is optional acceleration.
- With torch builds that are not compatible with NumPy 2, use a NumPy 1.x
  runtime such as `numpy<2` to avoid ABI warnings or import failures.

## Troubleshooting entry points

- Install/import, CLI discovery, torch/torchvision, NumPy ABI, or CUDA probe:
  run [`scripts/check_pytorch_fid_env.py`](scripts/check_pytorch_fid_env.py),
  then read [`references/troubleshooting.md`](references/troubleshooting.md).
- Empty or mixed input directories, missing `.npz` keys, non-finite stats, or
  dimension mismatches: run
  [`scripts/validate_fid_inputs.py`](scripts/validate_fid_inputs.py).
- Saved-statistics uncertainty: run
  [`scripts/inspect_stats_npz.py`](scripts/inspect_stats_npz.py).
- Unexpected FID values: verify dimension, stats provenance, input preprocessing,
  package/version, and whether the comparison is being made against TensorFlow
  or another implementation.
