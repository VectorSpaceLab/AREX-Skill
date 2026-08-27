# Workflow Recipes

Use these recipes as starting points. Replace task and ROI names with values discovered through `totalseg_info`; capability discovery is owned by `../../capability-discovery/SKILL.md`.

## Basic CT Segmentation

```bash
TotalSegmentator \
  -i ct.nii.gz \
  -o seg_total/ \
  -ta total \
  --report seg_total/run_report.json \
  --quiet
```

This writes per-class NIfTI masks under `seg_total/` and a machine-readable manifest at `seg_total/run_report.json`. Downstream automation should read the report instead of parsing stdout.

## Basic MR Segmentation

```bash
TotalSegmentator \
  -i mr.nii.gz \
  -o seg_total_mr/ \
  -ta total_mr \
  --report seg_total_mr/run_report.json \
  --quiet
```

Task names ending in `_mr` are MR-oriented. If an input DICOM folder has modality metadata and the requested default task mismatches `total` versus `total_mr`, the CLI may warn and switch between those defaults.

## CPU-Constrained ROI Run

```bash
TotalSegmentator \
  -i ct.nii.gz \
  -o seg_liver_spleen/ \
  -ta total \
  --device cpu \
  --fast \
  --roi_subset liver spleen \
  --statistics \
  --report seg_liver_spleen/run_report.json \
  --quiet
```

Use this shape when no GPU is available. `--fast` uses a lower-resolution model, and `--roi_subset` reduces the target classes. Confirm ROI names through discovery before running.

## Fast Multilabel File

```bash
TotalSegmentator \
  -i ct.nii.gz \
  -o seg_total_fast.nii.gz \
  -ta total \
  --ml \
  --fast \
  --save_lowres \
  --resampling_order 1 \
  --report seg_total_fast.report.json \
  --quiet
```

This saves one multilabel NIfTI instead of per-class masks. `--save_lowres` is valid here because the run is fast and output is NIfTI. Do not combine `--save_lowres` with DICOM output types.

## Robust ROI Crop

```bash
TotalSegmentator \
  -i ct.nii.gz \
  -o seg_roi_robust/ \
  -ta total \
  --roi_subset prostate urinary_bladder \
  --robust_crop \
  --report seg_roi_robust/run_report.json \
  --quiet
```

Use `--robust_crop` when a fast ROI crop cuts off anatomy or produces obvious crop artifacts. It uses a slower but more robust crop model.

## Statistics-Aware Pipeline

```bash
TotalSegmentator \
  -i ct.nii.gz \
  -o seg_stats/ \
  -ta total \
  --statistics \
  --statistics_extra \
  --report seg_stats/run_report.json \
  --quiet
```

This chooses statistics generation during segmentation. Parsing field-level statistics schemas, combining masks, and probability outputs belong to `../../outputs-and-statistics/SKILL.md`.

## Shell-Safe Command Builder

Use the bundled helper to construct a command without running inference:

```bash
python scripts/build_segmentation_command.py \
  --input ct.nii.gz \
  --output seg_liver/ \
  --task total \
  --device cpu \
  --fast \
  --roi liver \
  --statistics \
  --report seg_liver/run_report.json \
  --quiet
```

The helper prints warnings plus a shell-quoted `TotalSegmentator ...` command. It validates device strings, output types, `--save-lowres` rules, model-size restrictions, and resampling order; it does not import TotalSegmentator or download weights.

## Python API With Saved Outputs

```python
from totalsegmentator.python_api import totalsegmentator

seg_img = totalsegmentator(
    "ct.nii.gz",
    "seg_api/",
    task="total",
    device="cpu",
    fast=True,
    roi_subset=["liver", "spleen"],
    statistics=True,
    statistics_extra=True,
    report="seg_api/run_report.json",
    quiet=True,
)
```

`seg_img` is a multilabel `Nifti1Image`. The output directory contains the requested saved masks and JSON side outputs.

## Python API With In-Memory Input

```python
import nibabel as nib
from totalsegmentator.python_api import totalsegmentator

image = nib.load("ct.nii.gz")
seg_img = totalsegmentator(
    image,
    "seg_from_image/",
    task="total",
    device="gpu",
    report="seg_from_image/run_report.json",
    quiet=True,
)
```

Passing a `Nifti1Image` is supported. In run reports, the input field records `"Nifti1Image"` rather than a filesystem path.

## Python API Return-Only Pattern

```python
import nibabel as nib
from totalsegmentator.python_api import totalsegmentator

image = nib.load("ct.nii.gz")
seg_img = totalsegmentator(
    image,
    output=None,
    task="total",
    device="cpu",
    fast=True,
    quiet=True,
)
```

Use this only when the caller wants the returned `Nifti1Image` and does not need saved masks, reports, statistics files, or radiomics. Do not set `radiomics=True` without an output path.

## Licensed Task Pattern

```bash
TotalSegmentator \
  -i ct.nii.gz \
  -o seg_tissue/ \
  -ta tissue_types \
  --report seg_tissue/run_report.json \
  --quiet
```

If the task requires a license and the environment is not configured, the run fails with a runtime error. License discovery and setup belong to `../../runtime-configuration/SKILL.md`.

## Pre-Run Checklist

- Task exists and modality matches the input (`total` for CT, `total_mr` for MR defaults).
- ROI class names are exact class names for the selected task.
- Output path shape matches the output mode: directory for per-class masks, file path for `--ml` or DICOM outputs.
- Device string is valid; CPU workflows include speed/memory reductions when possible.
- `--report` path is set for automation.
- `--save_lowres` is paired with `--fast` or `--fastest` and NIfTI output.
- Licensed tasks are either avoided or the runtime has already been configured.
