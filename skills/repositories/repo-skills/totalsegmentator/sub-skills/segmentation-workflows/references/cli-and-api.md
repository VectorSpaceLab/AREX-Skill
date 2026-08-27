# CLI And Python API Reference

This reference covers building segmentation runs. It intentionally summarizes report/statistics schemas only enough to choose flags; detailed parsing belongs to `../../outputs-and-statistics/SKILL.md`.

## CLI Shape

```bash
TotalSegmentator -i <input> -o <output> -ta <task> [workflow options]
```

Inputs may be a NIfTI file (`.nii` or `.nii.gz`), a folder of DICOM slices, or a zip of DICOM slices. The output is normally a directory of one mask file per class. With `--ml` it is a single multilabel NIfTI file; with DICOM output types it is a single DICOM output path.

For actual segmentation, both `-i` and `-o` are required. `--list-tasks` and `--list-classes [task]` short-circuit before segmentation and do not require input/output, but prefer the lightweight `totalseg_info` command via `../../capability-discovery/SKILL.md` for automation.

## Core Flags

| Flag | API argument | Purpose | Notes |
| --- | --- | --- | --- |
| `-i <path>` | `input` | Input image or DICOM container | Required for segmentation. |
| `-o <path>` | `output` | Output directory or output file | Required for segmentation. Required for radiomics in Python. |
| `-ta`, `--task <task>` | `task` | Selects CT/MR model/task | Default is `total`; MR default task is commonly `total_mr`. |
| `-d`, `--device cpu|gpu|gpu:N|mps` | `device` | Runtime device selection | `gpu` maps to CUDA when available and falls back to CPU when unavailable. |
| `-f`, `--fast` | `fast` | 3 mm lower-resolution model | Reduces runtime and memory. |
| `-ff`, `--fastest` | `fastest` | 6 mm lower-resolution model | Fastest/lowest-resolution mode where supported. |
| `-sl`, `--save_lowres` | `save_lowres` | Save model-resolution output | Requires `--fast` or `--fastest`; supports NIfTI only. |
| `-rs`, `--roi_subset <class...>` | `roi_subset` | Save/predict selected classes | Use class names from `totalseg_info`; can reduce runtime/memory. |
| `-rc`, `--robust_crop` | `robust_crop` | Use slower, more robust ROI crop model | Helps when fast cropping cuts off anatomy. |
| `-ml`, `--ml` | `ml` | Save one multilabel image | Output path is a file rather than a per-class directory. |
| `-s`, `--statistics [path]` | `statistics` | Compute volume and mean intensity | Optional custom path; otherwise writes `statistics.json`. |
| `-sx`, `--statistics_extra` | `statistics_extra` | Add extra statistics metrics | Requires statistics workflow; see outputs-and-statistics for schema. |
| `-rp`, `--report <path>` | `report` | Write machine-readable run report | Recommended for reproducible automation. |
| `-ot`, `--output_type <type...>` | `output_type` | Output type(s) | Valid types: `nifti`, `dicom_seg`, `dicom_rtstruct`; `dicom` aliases to `dicom_rtstruct` in the CLI. |
| `-ms`, `--model_size big|small` | `model_size` | Model-size selector | `small` is only supported for task `total_v3`; default is `big`. |
| `-ro`, `--resampling_order 0..5` | `resampling_order` | Spline order for input resampling | Default `3`; `1` can speed resampling with similar accuracy. |
| `-q`, `--quiet` | `quiet` | Suppress intermediate output | Useful in non-interactive automation. |
| `--debug` | `debug` | Extra error context | Prints useful context such as input path/task on errors. |

Other flags exist for advanced inference (`--force_split`, `--body_seg`, `--higher_order_resampling`, `--save_probabilities`, etc.). Use them only when the workflow explicitly needs those behaviors, and route probability-output details to `../../outputs-and-statistics/SKILL.md`.

## Device Semantics

Valid device strings are exactly:

- `cpu`
- `gpu`
- `gpu:N`, where `N` is a non-negative integer CUDA device index such as `gpu:0`
- `mps`

Invalid examples include `cuda`, `gpu:-1`, `gpu:1.5`, and empty `gpu:`. When `gpu` or `gpu:N` is requested but CUDA is unavailable or the device id is out of range, TotalSegmentator warns and runs on CPU. CPU runs can be very slow; prefer `--fast`, `--fastest`, and/or `--roi_subset` for constrained machines.

## Python API

```python
from totalsegmentator.python_api import totalsegmentator

seg_img = totalsegmentator(
    "ct.nii.gz",
    "seg/",
    task="total",
    device="gpu",
    fast=False,
    roi_subset=None,
    statistics=False,
    report="seg/run_report.json",
    quiet=True,
)
```

Main callable signature:

```python
totalsegmentator(input, output=None, ml=False, nr_thr_resamp=1, nr_thr_saving=6,
                 fast=False, nora_tag="None", preview=False, task="total", roi_subset=None,
                 statistics=False, radiomics=False, crop_path=None, body_seg=False,
                 force_split=False, output_type="nifti", quiet=False, verbose=False, test=0,
                 skip_saving=False, device="gpu", license_number=None,
                 statistics_exclude_masks_at_border=True, no_derived_masks=False,
                 v1_order=False, fastest=False, roi_subset_robust=None, stats_aggregation="mean",
                 remove_small_blobs=False, statistics_normalized_intensities=False,
                 robust_crop=False, higher_order_resampling=False, save_probabilities=None,
                 debug=False, report=None, statistics_extra=False, save_lowres=False,
                 resampling_order=3, plans="nnUNetPlans", model_size="big")
```

Accepted `input` values include `str`, `pathlib.Path`, and `nibabel.nifti1.Nifti1Image`. If a `Nifti1Image` is passed, run reports identify the input as `"Nifti1Image"`.

The API returns a multilabel `Nifti1Image`. When `output` is provided, it also saves requested masks/statistics/reports according to the arguments. If `output` is `None` and `radiomics=True`, the API raises `ValueError` because radiomics requires an output directory.

## Validation Rules To Apply Before Running

- Require input and output for segmentation workflows.
- Validate device strings against `cpu`, `gpu`, `gpu:N`, and `mps`.
- Validate `resampling_order` as an integer from `0` through `5`.
- Validate output types as `nifti`, `dicom_seg`, or `dicom_rtstruct`.
- Use `--save_lowres` only with `--fast` or `--fastest`.
- Use `--save_lowres` only with NIfTI output.
- Use `--model_size small` only when `--task total_v3`.
- Discover task and ROI names with `totalseg_info`; do not invent or hard-code class names.

## Exit-Code Expectations

- `0`: success.
- `1`: runtime error such as missing license, model/runtime exception, or dependency problem.
- `2`: argument error such as invalid task/device/output settings or missing `-i`/`-o`.

Use `--report` and statistics files for machine parsing. Stdout is human-oriented and should not be scraped by pipelines.
