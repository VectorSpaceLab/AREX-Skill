# Segmentation Troubleshooting

This guide covers segmentation command/API construction and common runtime choices. Route setup, license, DICOM, and output-parsing details to sibling sub-skills when noted.

## Quick Matrix

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| CLI exits with missing `-i` or `-o` | Segmentation runs require both input and output | Add `-i <input>` and `-o <output>`. Discovery flags are the only common no-input/no-output mode. |
| `Invalid device type` | Device string is not `cpu`, `gpu`, `gpu:N`, or `mps` | Replace `cuda`, `gpu:-1`, `gpu:abc`, etc. with a valid TotalSegmentator device string. |
| Requested GPU but run says CPU | CUDA unavailable or selected GPU index is invalid | Accept CPU fallback or fix backend/device setup via `../../runtime-configuration/SKILL.md`; add `--fast` or `--roi_subset` to reduce CPU cost. |
| CPU run is too slow or memory-heavy | Full-resolution, many-class segmentation on CPU | Add `--fast`, `--fastest`, `--roi_subset <class...>`, `--ml`, or `--resampling_order 1` where acceptable. |
| `save_lowres only works together with fast or fastest mode` | `--save_lowres` used without `--fast`/`--fastest` | Add `--fast` or `--fastest`, or remove `--save_lowres`. |
| `save_lowres only supports nifti output` | Low-resolution saving requested with DICOM output | Use NIfTI output or remove `--save_lowres`; route DICOM decisions to `../../dicom-and-formats/SKILL.md`. |
| `model_size='small' is currently only supported for task 'total_v3'` | `--model_size small` used with another task | Use `--model_size big` or change task to `total_v3` if that is the intended workflow. |
| Invalid output type | Output type is not supported | Use `nifti`, `dicom_seg`, or `dicom_rtstruct`; CLI also maps `dicom` to `dicom_rtstruct`. |
| ROI class is missing or not produced | Class name does not belong to selected task | Discover classes with `totalseg_info --classes -ta <task>` via `../../capability-discovery/SKILL.md`; use exact names. |
| Licensed task fails | License missing or invalid | Route to `../../runtime-configuration/SKILL.md` for license setup and task license status. |
| DICOM output import error | Missing DICOM output dependency | Route to `../../dicom-and-formats/SKILL.md`; `dicom_seg` needs `highdicom`, `dicom_rtstruct` needs `rt_utils`. |
| Python API raises `Output path is required for radiomics` | `radiomics=True` with `output=None` | Provide an output directory or disable radiomics. |
| Automation cannot identify files/classes reliably | Pipeline is scraping stdout | Add `--report <path.json>` and parse the report; route detailed schema handling to `../../outputs-and-statistics/SKILL.md`. |

## Argument Errors

For a real segmentation, always provide:

```bash
TotalSegmentator -i <input> -o <output> -ta <task>
```

The CLI permits `--list-tasks` and `--list-classes [task]` without `-i`/`-o`, but those load the full runtime. Use `totalseg_info` through `../../capability-discovery/SKILL.md` for fast, no-model discovery.

## Device Problems

Validate device strings before running:

- Good: `cpu`, `gpu`, `gpu:0`, `gpu:1`, `mps`
- Bad: `cuda`, `cuda:0`, `gpu:-1`, `gpu:1.0`, `gpu:`, `auto`

When `gpu` is requested and no CUDA device is available, TotalSegmentator prints a warning and runs on CPU. That is not necessarily a fatal error, but it can make workflows much slower. For unattended jobs, explicitly choose `--device cpu` when CPU is expected, and combine it with speed/memory options.

## Speed And Memory Recovery

Use these in increasing order of workflow change:

1. Add `--roi_subset <class...>` when only a few structures are needed.
2. Add `--fast` for 3 mm lower-resolution inference.
3. Add `--fastest` for 6 mm lower-resolution inference when acceptable.
4. Use `--ml` to reduce per-class file-saving overhead.
5. Use `--resampling_order 1` to speed input resampling.
6. Consider `--save_lowres` only when lower-resolution output is acceptable and the output type is NIfTI.

Do not hide the accuracy/runtime tradeoff from users: lower resolution and ROI-only workflows can be less accurate for small structures.

## ROI And Cropping Artifacts

If a ROI run appears cut off or misses anatomy after using crop-assisted inference, try:

```bash
TotalSegmentator -i ct.nii.gz -o seg_roi/ -ta total --roi_subset <class...> --robust_crop --report seg_roi/run_report.json
```

`--robust_crop` uses a slower but more robust crop model. If ROI names are uncertain, route to `../../capability-discovery/SKILL.md` first.

## Output Mode Mismatches

Per-class masks:

```bash
TotalSegmentator -i ct.nii.gz -o seg_dir/ -ta total
```

Multilabel NIfTI:

```bash
TotalSegmentator -i ct.nii.gz -o seg.nii.gz -ta total --ml
```

DICOM output:

```bash
TotalSegmentator -i dicom_slices/ -o seg.dcm -ta total --output_type dicom_seg
```

DICOM output dependencies, DICOM folder layout, and DICOM-specific troubleshooting belong to `../../dicom-and-formats/SKILL.md`.

## Report And Statistics Confusion

`--report` is the reproducibility manifest: versions, resolved device, task, modality, class map, runtime, and written output files. `--statistics` and `--statistics_extra` compute per-class measurements. If the task is to parse these JSON files, combine masks, or handle probability outputs, route to `../../outputs-and-statistics/SKILL.md`.

## Licensed Tasks

Some selectable tasks require a license. Segmentation workflows should not embed license keys or setup instructions. If a run fails with a missing/invalid license message, route to `../../runtime-configuration/SKILL.md` for license status, configuration, and offline/runtime setup.

## Safe Verification Candidates

Lightweight checks that do not require model weights:

```bash
TotalSegmentator --help
totalseg_info --json
python scripts/build_segmentation_command.py --help
python scripts/build_segmentation_command.py --input ct.nii.gz --output seg/ --task total --device cpu --fast --roi liver --report seg/run_report.json --quiet
```

Native end-to-end prediction tests exercise real inference and should be treated as expensive/network/weights-dependent unless weights already exist and the user explicitly wants that verification.
