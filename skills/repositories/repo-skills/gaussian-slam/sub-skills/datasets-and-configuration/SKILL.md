---
name: datasets-and-configuration
description: "Prepare, select, and validate Gaussian-SLAM RGB-D datasets and
  YAML configurations for a safe GPU run."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Datasets and configuration

Use this sub-skill when a Gaussian-SLAM run needs an RGB-D scene, a dataset
alias, a scene-specific YAML file, or a preflight check. It covers the data
contract implemented by `src/entities/datasets.py` and the recursive YAML
merge behavior in `src/utils/io_utils.py`. It does **not** own SLAM
optimization, tracking/mapping choices, or evaluation metrics.

## Applicability and operating contract

- A run must use one of the exact dataset aliases `replica`, `tum_rgbd`,
  `scan_net`, or `scannetpp`. These are case-sensitive; `scannet`, `ScanNet`,
  `tum-rgbd`, and `scannet_pp` are not aliases accepted by `get_dataset`.
- Start from a dataset default config and use a per-scene config with
  `inherit_from`. The effective configuration must contain the top-level
  `project_name`, `dataset_name`, `checkpoint_path`, `use_wandb`, `frame_limit`,
  `seed`, `mapping`, `tracking`, `cam`, and `data` keys. A per-scene
  `data.frame_limit` is also accepted and is the value passed to the dataset
  loader when present (the supplied ScanNet++ scenes use this form).
- Run the bundled validator before importing CUDA-heavy runtime modules:

  ```bash
  python skills/disco/gaussian-slam/sub-skills/datasets-and-configuration/scripts/validate_config.py \
      configs/Replica/office0.yaml
  ```

  Add `--require-data --path-base <repository-root>` when the data must be
  present now rather than merely checking the YAML contract. Multiple explicit
  config paths may be supplied. The validator uses PyYAML and standard Python
  modules only; it does not import PyTorch, OpenCV, Open3D, or custom CUDA
  extensions.
- `run_slam.py` accepts a config path followed by optional `--input_path` and
  `--output_path` overrides. Those overrides replace the values under `data`;
  validate the final values, not only the YAML defaults.

## Safe workflow

1. Identify the dataset and exact scene. Confirm that the external dataset's
   license, download permissions, credentials, and storage budget permit local
   use. Do not guess a scene's camera model or silently substitute a dataset.
2. Inspect the corresponding default and scene YAML. Confirm inheritance,
   dataset alias, `data.input_path`, `data.output_path`, camera values, depth
   scale, and split/frame-limit behavior. Check both the run-level
   `frame_limit` and any loader-level `data.frame_limit` override.
3. Acquire or mount data using the reference-only guidance in
   [data-and-downloads.md](references/data-and-downloads.md). Never execute a
   download merely as part of validation.
4. Validate the effective config and available data. Resolve relative input and
   output paths against the intended working directory (the source CLI does
   not rewrite them). Require paired RGB/depth/pose records and the metadata
   needed by the selected loader.
5. Treat warnings as a stop-and-review gate before a GPU run. In particular,
   investigate relative paths, dropped timestamp associations, changed
   intrinsics, missing split names, and a frame limit larger than the selected
   sequence.
6. Only after the preflight passes, launch the repository command with the
   final explicit paths. Preserve the effective YAML with the run output for
   reproducibility.

For field-level rules and effective merge examples, see
[configuration.md](references/configuration.md). For on-disk records and image,
depth, and pose conventions, see [data-formats.md](references/data-formats.md).
For download prerequisites and licensing boundaries, see
[data-and-downloads.md](references/data-and-downloads.md). For failure symptoms
and recovery, see [troubleshooting.md](references/troubleshooting.md).

## Expected observations and checks

A successful preflight reports the resolved inheritance chain, effective
`dataset_name`, camera dimensions/intrinsics/depth scale, selected split (when
applicable), and either verified data counts or an explicit “data path not
present; YAML-only validation” warning. With `--require-data`, absent paths,
missing files, malformed records, unsupported aliases, count mismatches, and
unresolved inheritance are failures (exit status 1).

The validator is intentionally conservative: it does not modify YAML, create
output directories, download data, initialize wandb, allocate a GPU, or import
the Gaussian-SLAM package. A passing validator proves configuration and
layout preconditions only; it is not evidence that CUDA extensions, tracking,
mapping, or evaluation will succeed.

## Difficult synthetic usability cases

Use these cases during integrated skill verification; keep fixtures and reports
outside this runtime skill tree:

1. **Inheritance and path trap:** create `nested/scene.yaml` inheriting
   `base.yaml`, run validation from a different current directory, and give the
   scene a relative `data.input_path`. The validator must load the sibling base
   by path relative to `scene.yaml`, flag the data path as relative, and reject
   a second fixture whose base path forms an inheritance cycle.
2. **Silent frame drop trap:** create a TUM fixture with valid-looking RGB and
   depth lists but one pose timestamp more than `0.08` seconds from every RGB
   timestamp; create a ScanNet++ fixture whose selected train split names a
   frame absent from `transforms_undistorted.json`. Validation must fail with a
   dataset-specific association/metadata message without importing CUDA.

## Linked resources

- [references/data-formats.md](references/data-formats.md)
- [references/configuration.md](references/configuration.md)
- [references/data-and-downloads.md](references/data-and-downloads.md)
- [references/troubleshooting.md](references/troubleshooting.md)
- [scripts/validate_config.py](scripts/validate_config.py)
