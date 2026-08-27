# DICOM and NIfTI Handling

This reference covers TotalSegmentator format decisions before and around inference. It intentionally avoids task selection, model execution tuning, statistics parsing, and installation instructions.

## Accepted Inputs

TotalSegmentator accepts these input forms for ordinary segmentation:

| Input form | How TotalSegmentator treats it | Use when |
| --- | --- | --- |
| `.nii` file | NIfTI input. | The scan is already converted and DICOM output is not required. |
| `.nii.gz` file | Compressed NIfTI input. | Most reproducible automation workflows. |
| DICOM directory | Non-NIfTI path is treated as DICOM and converted internally to NIfTI with `dicom2nifti`. | Original DICOM metadata must be preserved, especially for DICOM SEG/RTSTRUCT output. |
| DICOM zip | A zip is extracted to a temporary directory and converted with `dicom2nifti`; the converter requires a temporary extraction directory internally. | Transporting one DICOM series as one file. |
| `nibabel.nifti1.Nifti1Image` | Python API in-memory NIfTI input. | Python workflows that already loaded image data and do not need DICOM output. |

The CLI documents input as a CT NIfTI image, a folder of DICOM slices, or a zip of DICOM slices. In source, path inputs ending in `.nii` or `.nii.gz` are NIfTI; every other existing path is treated as DICOM.

## Quick Preflight

Use the bundled validator before long runs:

```bash
python scripts/validate_input_layout.py ct.nii.gz --output-type nifti
python scripts/validate_input_layout.py dicom_series/ --output-type dicom_seg --task total --strict
python scripts/validate_input_layout.py dicom_series.zip --output-type dicom_rtstruct --require-optional
```

What the helper checks:

- Missing or unsupported path forms.
- NIfTI extension spelling (`.nii` and `.nii.gz` only).
- DICOM directory vs DICOM zip classification.
- Optional header probes with `pydicom` when installed.
- Mixed DICOM modality/series warnings when tags are readable.
- DICOM output requested from NIfTI input.
- Missing optional libraries for `dicom_seg` (`highdicom`) and `dicom_rtstruct` (`rt_utils`).
- `save_lowres` incompatibility with DICOM output.

The helper does not run TotalSegmentator, load model weights, or modify files.

## Output Path Semantics

| Output choice | CLI flags | `-o` should be | Notes |
| --- | --- | --- | --- |
| Per-class NIfTI masks | default `--output_type nifti`, no `--ml` | Directory | Writes one `.nii.gz` per class. Use outputs/statistics sub-skill for report and mask consumption details. |
| Multilabel NIfTI | `--ml` or DICOM output enforced internally | File path | One NIfTI volume containing labels. |
| DICOM SEG | `-ot dicom_seg` or `--output_type dicom_seg` | File path, or base path when multiple outputs are requested | Requires original DICOM input and `highdicom`. |
| DICOM RTSTRUCT | `-ot dicom_rtstruct` or `--output_type dicom_rtstruct` | File path, or base path when multiple outputs are requested | Requires original DICOM input and `rt_utils`. |
| Multiple outputs | `-ot nifti dicom_seg` or `-ot nifti,dicom_seg` | Directory or file-like base path | CLI normalizes comma-separated and space-separated lists. If a directory is supplied, output names use `<task>_segmentation.*`; if a file path is supplied, its stem is used as the base. |

The CLI accepts `dicom` as a backward-compatible alias for `dicom_rtstruct` while normalizing output types. Valid normalized output types are `nifti`, `dicom_rtstruct`, and `dicom_seg`.

## DICOM Output Rules

DICOM output is different from ordinary NIfTI output because the writer needs the original DICOM series as reference metadata.

Required rules:

- Input must be a DICOM directory or DICOM zip. If the input is `.nii` or `.nii.gz`, TotalSegmentator raises `ValueError: To use output type dicom_rtstruct or dicom_seg you also have to use a Dicom image as input.`
- `dicom_seg` requires the optional Python package `highdicom`.
- `dicom_rtstruct` requires the optional Python package `rt_utils`.
- Any DICOM output type forces multilabel segmentation internally.
- `save_lowres` supports only NIfTI output and is rejected with DICOM SEG/RTSTRUCT.
- DICOM SEG/RTSTRUCT writers need orientation and grid metadata that match the produced segmentation. Mixed localizers, multiple acquisitions, missing tags, or anonymized metadata can make export fail even if DICOM-to-NIfTI conversion succeeded.

Example DICOM SEG command:

```bash
TotalSegmentator -i dicom_series/ -o seg.dcm -ta total -ot dicom_seg --report run_report.json --quiet
```

Example RTSTRUCT command:

```bash
TotalSegmentator -i dicom_series/ -o rtstruct.dcm -ta total -ot dicom_rtstruct --report run_report.json --quiet
```

Example DICOM input plus NIfTI output:

```bash
TotalSegmentator -i dicom_series.zip -o seg/ -ta total --report seg/run_report.json --quiet
```

## DICOM Conversion Behavior

Internally, DICOM input is converted to a temporary NIfTI before inference:

- `totalsegmentator.dicom_io.dcm_to_nifti(...)` uses `dicom2nifti.dicom_series_to_nifti(..., reorient_nifti=True)`.
- Zip inputs are extracted before conversion; extraction requires a temporary directory.
- The original DICOM input path is retained for DICOM SEG/RTSTRUCT export.
- DICOM SEG export reads all files in the reference DICOM directory, then filters to the image grid that matches the segmentation when possible. This protects some MR directories with localizers or duplicate spatial positions, but it is not a substitute for supplying a clean single series.

For robust automation, supply one patient series per directory or zip. Avoid mixing scout/localizer images, CT and MR images, or multiple acquisitions in one input folder.

## DICOM Modality Auto-correction

The CLI attempts a small DICOM modality correction before running segmentation:

- If input is DICOM and the readable DICOM `Modality` tag is `CT` while task is `total_mr`, the CLI warns and changes task to `total`.
- If input is DICOM and `Modality` is `MR` while task is `total`, the CLI warns and changes task to `total_mr`.
- The check uses a lightweight `pydicom.dcmread(..., stop_before_pixels=True)` probe and silently does nothing if modality cannot be read.

This auto-correction only covers the default CT/MR task mismatch. It does not choose among all specialized tasks. Use capability discovery for broader task selection.

## Crop-to-body Preprocessing

The package includes a separate `crop_to_body` console script. It takes a NIfTI input and writes a cropped NIfTI output:

```bash
crop_to_body -i ct.nii.gz -o ct_cropped.nii.gz --device cpu --quiet
```

Relevant flags:

| Flag | Meaning |
| --- | --- |
| `-i` | Input CT NIfTI path. |
| `-o` | Output cropped NIfTI path. |
| `-t`, `--only_trunc` | Crop to body trunk instead of the entire body. |
| `-nr`, `--nr_thr_resamp` | Threads for resampling. |
| `-ns`, `--nr_thr_saving` | Threads for saving segmentations. |
| `-d`, `--device` | `gpu` or `cpu` for the body-crop model. The script falls back to CPU if GPU is requested but unavailable. |
| `-q`, `--quiet` | Suppress intermediate output. |
| `-v`, `--verbose` | Print more details. |

Build, inspect, and copy a command with the bundled helper:

```bash
python scripts/crop_to_body_command.py -i ct.nii.gz -o ct_cropped.nii.gz --only-trunc --device cpu --quiet
```

Important cautions:

- `crop_to_body` is a model-running utility; the helper only prints the command.
- `crop_to_body` expects NIfTI, not a DICOM directory/zip. Convert or run ordinary segmentation on DICOM first if DICOM metadata must be preserved.
- Cropping changes image extent. Do not use a cropped NIfTI as the source for DICOM SEG/RTSTRUCT export unless the downstream workflow explicitly handles geometry restoration.
- If the goal is built-in inference-time body cropping, `TotalSegmentator --body_seg` belongs to segmentation workflow planning rather than this standalone preprocessing helper.

## Python API Format Notes

The public API accepts string/`Path` inputs and in-memory `Nifti1Image` inputs:

```python
from totalsegmentator.python_api import totalsegmentator

seg_img = totalsegmentator(
    "dicom_series/",
    "seg.dcm",
    task="total",
    output_type="dicom_seg",
    device="cpu",
    quiet=True,
)
```

For DICOM outputs in Python:

- Use a DICOM path input, not a `Nifti1Image` input.
- Pass `output_type="dicom_seg"` or `output_type="dicom_rtstruct"`.
- Preflight optional libraries before calling the API so missing dependencies fail quickly.
- For multiple output types, the implementation accepts a list such as `output_type=["nifti", "dicom_seg"]`; ensure the caller has tested that form in the installed version.

## Decision Checklist

Before running segmentation:

1. Is the input path present and either `.nii`, `.nii.gz`, a DICOM directory, or a DICOM zip?
2. If the input is DICOM, does it contain one coherent series rather than mixed studies/acquisitions?
3. If DICOM output is requested, is the input DICOM and is the required optional package importable?
4. If `--save_lowres` is requested, is output NIfTI-only and is `--fast` or `--fastest` also requested?
5. If modality tags indicate MR, is the task intentionally MR (`total_mr` or another MR task)?
6. If preprocessing with `crop_to_body`, is the input/output NIfTI and is the downstream workflow aware that geometry changed?
