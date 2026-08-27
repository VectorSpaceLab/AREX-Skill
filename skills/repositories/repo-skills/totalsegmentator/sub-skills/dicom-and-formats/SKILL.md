---
name: dicom-and-formats
description: "Handle TotalSegmentator NIfTI and DICOM inputs, DICOM outputs,
  modality checks, and crop-to-body preprocessing."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# DICOM and Formats

Use this sub-skill when an agent needs to decide whether a TotalSegmentator input is NIfTI, a DICOM directory, or a DICOM zip; when it needs DICOM SEG or RTSTRUCT output; or when it needs crop-to-body preprocessing to reduce volume size.

## Start Here

1. Classify the input with `scripts/validate_input_layout.py` before building a long-running segmentation command.
2. Use `.nii` or `.nii.gz` inputs for ordinary NIfTI workflows; use a DICOM folder or zip when DICOM SEG/RTSTRUCT output is required.
3. For DICOM SEG/RTSTRUCT, pass DICOM input and set `--output_type dicom_seg` or `--output_type dicom_rtstruct`; do not request DICOM output from NIfTI input.
4. For memory reduction before a NIfTI segmentation, build a `crop_to_body` command with `scripts/crop_to_body_command.py` and review it before running.
5. If the task/classes/device/model execution choices are the main question, route to `../segmentation-workflows/SKILL.md` after the format decision is settled.

## Local References

- `references/dicom-and-nifti.md` covers accepted input layouts, DICOM conversion behavior, DICOM output rules, modality auto-correction, and crop-to-body usage.
- `references/troubleshooting.md` maps common format, DICOM dependency, orientation, zip, and crop-to-body failures to fixes.
- `scripts/validate_input_layout.py` inspects a candidate input path and optional output settings without loading model weights or running segmentation.
- `scripts/crop_to_body_command.py` prints a shell-quoted `crop_to_body` command; it does not execute the command.

## Route Elsewhere

- Use `../capability-discovery/SKILL.md` to discover valid tasks and class names with `totalseg_info` or the registry API.
- Use `../segmentation-workflows/SKILL.md` to run `TotalSegmentator` or `python_api.totalsegmentator(...)` after format choices are known.
- Use `../outputs-and-statistics/SKILL.md` for run reports, statistics, multilabel NIfTI consumption, probability outputs, and mask combination.
- Use `../runtime-configuration/SKILL.md` for installing optional DICOM libraries, model weights, licenses, offline config, devices, or backend setup.
- Use `../auxiliary-analysis/SKILL.md` for explicit NIfTI modality/phase/body-stats helper CLIs.

## Safe Defaults

- Validate NIfTI input: `python scripts/validate_input_layout.py ct.nii.gz --output-type nifti`.
- Validate DICOM SEG preflight: `python scripts/validate_input_layout.py series.zip --output-type dicom_seg --task total --strict`.
- Build DICOM SEG run only after preflight: `TotalSegmentator -i series.zip -o seg.dcm -ta total -ot dicom_seg --report run_report.json --quiet`.
- Build crop command only: `python scripts/crop_to_body_command.py -i ct.nii.gz -o ct_cropped.nii.gz --device cpu --quiet`.
