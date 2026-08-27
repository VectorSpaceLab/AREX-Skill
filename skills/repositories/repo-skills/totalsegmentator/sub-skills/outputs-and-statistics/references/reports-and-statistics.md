# Run Reports and Statistics

TotalSegmentator can emit machine-readable JSON artifacts that are safer for automation than stdout. Use `--report <path.json>` for a run manifest and `--statistics` / `--statistics_extra` / `--radiomics` for quantitative outputs.

## Run Report Contract

Create a report during segmentation:

```bash
TotalSegmentator -i ct.nii.gz -o seg/ --task total --report seg/run_report.json
```

The report builder writes a JSON object with these keys:

| Key | Meaning |
| --- | --- |
| `totalsegmentator_version` | Installed TotalSegmentator package version. |
| `nnunetv2_version` | Installed nnU-Net v2 version, or `null` if package metadata is absent. |
| `torch_version` | PyTorch version imported by the runtime. |
| `task` | Task that was run, for example `total` or `total_mr`. |
| `modality` | Registry modality for the task, `CT` or `MR`. |
| `license_required` | Boolean registry flag for the selected task. |
| `device` | Resolved device string such as `gpu`, `cpu`, or `mps`. |
| `fast`, `fastest`, `save_lowres` | Runtime resolution/output options. |
| `multilabel` | Whether `--ml` was used. |
| `output_type` | Requested output type, usually `nifti`; may also indicate DICOM output modes. |
| `roi_subset` | Requested ROI subset list, or `null`. |
| `input` | Input path, or `Nifti1Image` for in-memory API input. |
| `output` | Output path as a string, or `null`. |
| `num_classes` | Number of classes in `classes` after ROI filtering. |
| `classes` | Stringified index-to-class map, filtered by `roi_subset` when set. |
| `runtime_seconds` | Wall-clock runtime rounded to two decimals. |
| `output_files` | Sorted `*.nii.gz` filenames found directly under `output` when `output` is a directory. |

Validation checklist:

1. Confirm required keys are present before reading values.
2. Compare `task`, `device`, `fast`, `fastest`, `multilabel`, and `output_type` against the expected workflow.
3. Use `classes` rather than a hard-coded class map, because `roi_subset` filters the report down to requested names.
4. Treat `output_files` as directory-only evidence. It is expected to be empty when `output` is `null`, a single multilabel file, or a non-directory output.
5. If `license_required` is true and the run failed before writing a report, route license handling to runtime configuration.

Helper:

```bash
python scripts/inspect_run_report.py \
  --report seg/run_report.json \
  --require-task total \
  --require-class liver \
  --require-output-file liver.nii.gz
```

## Statistics JSON

Enable basic statistics with:

```bash
TotalSegmentator -i ct.nii.gz -o seg/ --statistics --report seg/run_report.json
```

By default, `statistics.json` is written in the output directory for per-class NIfTI output. For `--ml`, the statistics file is written next to the single output file. The CLI also accepts an optional custom statistics path:

```bash
TotalSegmentator -i ct.nii.gz -o seg/ --statistics results/case001-statistics.json
```

Each class entry contains:

| Field | Meaning |
| --- | --- |
| `volume` | Mask volume in cubic millimeters. |
| `intensity` | Aggregated input intensity for the mask; default aggregation is mean. |

`--stats_aggregation median` switches the intensity aggregation from mean to median. Statistics normally exclude masks that touch the image border by returning zeros; `--stats_include_incomplete` disables that exclusion.

## Extra Statistics

Add `--statistics_extra` together with `--statistics` to include extra metrics:

```bash
TotalSegmentator -i ct.nii.gz -o seg/ --statistics --statistics_extra
```

Extra fields per class:

| Field | Meaning |
| --- | --- |
| `n_voxels` | Count of voxels in the class mask. |
| `intensity_std` | Standard deviation of input intensities inside the mask. |
| `intensity_min` | Minimum input intensity inside the mask. |
| `intensity_max` | Maximum input intensity inside the mask. |
| `centroid_vox` | Voxel/index-space centroid as `[i, j, k]`, or `null` for empty/excluded masks. |
| `bbox_vox` | Inclusive voxel/index bounding box as `[[i_min, i_max], [j_min, j_max], [k_min, k_max]]`, or `null`. |

Use `--statistics_extra` when downstream QA needs to prove a non-empty segmentation, locate a structure, or verify a bounding box without loading every mask.

## Radiomics

Enable radiomics with:

```bash
TotalSegmentator -i ct.nii.gz -o seg/ --radiomics
```

Behavior and constraints:

- Writes `statistics_radiomics.json` in the segmentation output directory.
- Requires `pyradiomics` to be installed.
- Is not supported for `--ml` multilabel segmentation.
- Is not supported for DICOM input; use NIfTI input.
- If a mask is empty or radiomics raises internally, the implementation warns and fills standard features with zeros.

## Python API Notes

The Python API accepts the same output/statistics controls:

```python
from totalsegmentator.python_api import totalsegmentator

seg_img, stats = totalsegmentator(
    "ct.nii.gz",
    "seg/",
    task="total",
    statistics=True,
    statistics_extra=True,
    report="seg/run_report.json",
    device="cpu",
)
```

When `statistics` is truthy, the API returns `(seg_img, stats)`; otherwise it returns `seg_img`. `statistics` may be `True` or a custom file path. `radiomics=True` requires an output path.

## Automation Pattern

For a completed segmentation directory:

1. Validate `run_report.json` with `inspect_run_report.py`.
2. Confirm expected classes are in `report.classes` and, for per-class output, expected files are in `report.output_files`.
3. Load `statistics.json` and require `volume`, `intensity`, and any `--statistics_extra` fields needed by downstream logic.
4. For ROI runs, expect only requested ROI classes in `report.classes` and statistics output.
5. For single-file outputs, validate the report and then inspect the file header or adjacent statistics instead of requiring `output_files`.
