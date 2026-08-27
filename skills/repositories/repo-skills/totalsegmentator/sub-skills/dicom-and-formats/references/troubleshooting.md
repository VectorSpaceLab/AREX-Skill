# DICOM and Format Troubleshooting

Use this matrix when a TotalSegmentator workflow fails before, during, or immediately after format conversion/export. Route model/task/device issues to the sibling segmentation or runtime-configuration sub-skills.

## Input Classification Failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ERROR: The input file or directory does not exist.` | The path passed to `-i` does not exist from the process working directory. | Resolve the input path before launching. Use `python scripts/validate_input_layout.py <path>` to fail quickly. |
| `.nii.gz` file classified incorrectly by another script | The extension was split as `.gz` only or renamed to something like `.nii.gzip`. | TotalSegmentator recognizes paths ending in `.nii` or `.nii.gz`; keep the full suffix. |
| Unsupported input warning from helper | The path is not a NIfTI file, DICOM directory, or zip file. | Convert to `.nii/.nii.gz`, provide a DICOM series directory, or zip only the DICOM slices. |
| NIfTI loads but segmentation rejects the image as 2D | The image has only two dimensions. | Provide a 3D volume. TotalSegmentator raises `TotalSegmentator does not work for 2D images. Use a 3D image.` |
| Input image has more than three dimensions | A 4D image or extra channel/time dimension was supplied. | The implementation warns and uses the first three dimensions; intentionally select or convert the desired 3D volume before running. |

## DICOM Directory and Zip Problems

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| DICOM-to-NIfTI conversion fails | Directory is not a clean DICOM image series, contains mixed series, or has missing/inconsistent metadata. | Re-export one image series into its own directory. Avoid localizers, scout images, derived objects, or mixed CT/MR files. |
| Zip input fails conversion | Zip does not contain a coherent DICOM series or was not recognized as a zip by Python. | Create a zip containing the DICOM slice files for one series, not a nested archive or unrelated study tree. Validate with `python scripts/validate_input_layout.py series.zip --strict`. |
| Helper cannot read DICOM tags | `pydicom` is not installed or files are not readable DICOM images. | Install/repair optional DICOM inspection dependencies through runtime configuration, or proceed only if another tool has verified the series. |
| Mixed modality or multiple series warning | Directory contains CT and MR files, multiple `SeriesInstanceUID` values, localizers, or derived DICOM objects. | Split into one input folder/zip per series before running. If DICOM SEG/RTSTRUCT is required, preserve the exact original image series as the input. |
| DICOM input works for NIfTI output but DICOM SEG export fails | Conversion chose one compatible grid, but DICOM export could not match segmentation geometry back to source images. | Use a cleaner single-series DICOM directory. Remove localizers and duplicate acquisitions. Check rows/columns/slice count and orientation tags. |

## DICOM Output Problems

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `To use output type dicom_rtstruct or dicom_seg you also have to use a Dicom image as input.` | DICOM output was requested from `.nii` or `.nii.gz` input. | Re-run from the original DICOM directory/zip, or choose NIfTI output. |
| `highdicom is required for output_type='dicom_seg'` | `dicom_seg` was requested without `highdicom`. | Route to runtime configuration to install/verify the optional package, then preflight with `--require-optional`. |
| `rt_utils is required for output_type='dicom_rtstruct'` | `dicom_rtstruct` was requested without `rt_utils`. | Route to runtime configuration to install/verify the optional package, then preflight with `--require-optional`. |
| `save_lowres only supports nifti output.` | `--save_lowres` was combined with DICOM SEG/RTSTRUCT. | Remove `--save_lowres` for DICOM output, or choose NIfTI-only output. |
| No DICOM files found in reference directory | The DICOM output writer could not find files in the reference input path. | Use a directory/zip containing actual DICOM slice files. Avoid pointing `-i` to an already-converted NIfTI or empty extraction. |
| `No non-empty segments found to save` | Selected task/ROI produced no non-empty masks for the output writer. | Verify the task and ROI subset. Route task/class selection to capability discovery or segmentation workflow guidance. |
| Shape mismatch while creating DICOM SEG/RTSTRUCT | Segmentation dimensions do not match DICOM rows, columns, slices, or expected orientation. | Supply a single clean series; avoid cropped or resampled files as DICOM reference; inspect orientation and slice ordering. |
| DICOM output file naming is unexpected with multiple output types | Multiple `-ot` values derive names from output directory or output stem. | If `-o` is a directory, expect names like `<task>_segmentation_seg.dcm`; if `-o` is a file path, expect that stem with suffixes. |

## Modality and Task Mismatch

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| CLI warns it will run CT model instead of MR model | DICOM `Modality` tag was `CT` while task was `total_mr`. | Confirm the series is truly CT, then accept `total` or explicitly choose a CT task. |
| CLI warns it will run MR model instead of CT model | DICOM `Modality` tag was `MR` while task was `total`. | Confirm the series is truly MR, then accept `total_mr` or explicitly choose an MR task. |
| No warning despite wrong task | Modality tag could not be read or input was NIfTI. | Use explicit task selection. For NIfTI modality prediction, route to auxiliary-analysis for `totalseg_get_modality`. |
| Mixed CT/MR DICOM folder produces confusing behavior | The first readable tag may not represent the intended series. | Split CT and MR into separate folders and validate each before choosing a task. |

## Crop-to-body Problems

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `crop_to_body` rejects a DICOM folder/zip | The utility expects a CT NIfTI input path. | Run it on `.nii` or `.nii.gz`, or use ordinary TotalSegmentator DICOM input if DICOM metadata must be retained. |
| Cropped image cannot be used for DICOM SEG export | Cropping changed image extent and broke correspondence with original DICOM reference geometry. | For DICOM SEG/RTSTRUCT, run segmentation directly from DICOM input. Use crop-to-body only for NIfTI workflows unless geometry restoration is explicitly handled. |
| GPU requested but run falls back to CPU | The crop script maps `--device gpu` to CUDA and checks availability. | Use `--device cpu` in CPU-only environments or route backend setup to runtime configuration. |
| Output overwritten or placed incorrectly | `crop_to_body` writes exactly the output file passed to `-o`. | Build the command with `scripts/crop_to_body_command.py` and review `-i`/`-o` before running. |
| Memory remains high after cropping plan | Crop-to-body itself runs a body model first and may still need model weights and inference memory. | Use it when reducing a later NIfTI workflow is worth the preprocessing cost; route general runtime/device memory planning to segmentation-workflows and runtime-configuration. |

## Fast Preflight Commands

Classify input only:

```bash
python scripts/validate_input_layout.py input_path
```

Preflight DICOM SEG with strict DICOM tag checks and optional dependency checks:

```bash
python scripts/validate_input_layout.py dicom_series/ --output-type dicom_seg --strict --require-optional
```

Check a planned DICOM RTSTRUCT run without enforcing optional dependency presence:

```bash
python scripts/validate_input_layout.py series.zip --output-type dicom_rtstruct --task total
```

Build crop command without executing it:

```bash
python scripts/crop_to_body_command.py -i ct.nii.gz -o ct_cropped.nii.gz --device cpu --quiet
```
