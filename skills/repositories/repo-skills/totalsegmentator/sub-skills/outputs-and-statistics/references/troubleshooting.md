# Outputs and Statistics Troubleshooting

Use this matrix when a completed TotalSegmentator run produced files that are hard to consume. For failures before output creation, route to the runtime or segmentation workflow sub-skills.

## Report Problems

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `run_report.json` is missing. | The run did not include `--report`, failed before report writing, or wrote to a different path. | Do not scrape stdout. Re-run or adjust the workflow to pass `--report <path.json>`; then validate with `scripts/inspect_run_report.py`. |
| Required report keys are missing. | Report is not from the current TotalSegmentator report builder, is truncated, or was edited. | Fail the pipeline and regenerate the report. Required keys include versions, task, modality, device, run options, class map, runtime, and output file list. |
| `classes` lacks an expected class. | The run used `--roi_subset`, the wrong task, or the expected name is invalid for the selected task. | Check `report.task` and `report.roi_subset`; route task/class discovery to capability discovery before assuming a missing output. |
| `output_files` is empty. | `output` was not a directory, `--ml` wrote a single file, DICOM output was requested, `skip_saving` was used, or files were moved after the report was written. | Treat empty `output_files` as valid for single-file/non-directory outputs; otherwise verify the output directory and rerun report validation. |
| `runtime_seconds` exists but masks are incomplete. | A run can complete while producing only the requested ROI subset or while some statistics are zeroed for border-touching masks. | Validate against `classes`, `roi_subset`, and statistics fields instead of assuming the default full task output. |

## Statistics Problems

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `statistics.json` is missing. | The run did not include `--statistics`, used a custom statistics path, or failed before statistics calculation. | Inspect the command or report, then re-run with `--statistics` or search the configured custom statistics path. |
| Class statistics contain only `volume` and `intensity`. | `--statistics_extra` was not enabled. | Re-run with `--statistics --statistics_extra` if `n_voxels`, intensity distribution, centroid, or bounding box fields are required. |
| A class has `volume: 0.0` and `intensity: 0.0`. | The mask may be empty, excluded because it touches the image border, or outside the requested ROI subset. | Check whether the class is in `report.classes`; use `--stats_include_incomplete` only if border-touching masks should still be measured. |
| `centroid_vox` or `bbox_vox` is `null`. | The mask is empty or was excluded from statistics. | Treat `null` as a failed presence/location assertion for that class unless the run intentionally excluded the class. |
| Intensities do not match expected Hounsfield units. | The input image intensities were normalized, median aggregation was selected, or the wrong input image was used. | Check `--stats_aggregation`, `statistics_normalized_intensities` if using the API, and the report input path. |

## Radiomics Problems

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Import error for radiomics. | `pyradiomics` is not installed. | Install the optional dependency in the runtime environment or use basic statistics only. |
| Error: radiomics not supported for multilabel segmentation. | `--radiomics` was combined with `--ml`. | Use per-class NIfTI output instead of `--ml` for radiomics. |
| Error: radiomics not supported for DICOM input. | The input was a DICOM folder or zip. | Convert or provide NIfTI input for radiomics workflows. |
| Many radiomics features are zero. | The mask is empty/all-one or the radiomics extractor raised internally. | Check per-class masks and review warnings; use `statistics.json` volume as a simpler sanity check. |

## Multilabel Problems

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Label map cannot be loaded. | `xmltodict` is missing or the NIfTI file has no extension header. | Install `xmltodict`, run `scripts/inspect_multilabel_header.py`, or fall back to the run report and task class map. |
| Header extension index is absent. | The file was produced by a tool that did not preserve TotalSegmentator’s label-map extension. | Treat class names as unknown until recovered from report/task metadata; avoid combining by class name from this file. |
| Label IDs do not match expected names. | Wrong task, `--roi_subset`, `--v1_order`, or a non-TotalSegmentator file. | Validate `report.task`, `report.classes`, and label-map contents together. |
| `output_files` is empty for a successful `--ml` run. | The report only enumerates `*.nii.gz` files when `output` is a directory. | Validate the single output file path and inspect its header; do not require directory file listings for `--ml`. |

## Mask Combination Problems

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `totalseg_combine_masks` reports missing mask files. | The selected mode requires classes not present in the output directory, often due to `--roi_subset`, wrong task, or moved files. | Check mode-to-class requirements in `output-formats.md`; rerun segmentation with needed classes or choose a narrower mode. |
| Combining from a multilabel file fails. | The multilabel file has no readable label-map extension or lacks one of the requested class names. | Inspect with `scripts/inspect_multilabel_header.py`; if class names are unavailable, use per-class masks or regenerate a labeled multilabel file. |
| `heart` mode behaves unexpectedly. | The CLI accepts `heart`, but the current library combiner does not define an explicit heart class group in the inspected implementation. | Prefer an explicit Python `combine_masks(Path("seg/"), [<class names>])` list after discovering valid class names, or verify `heart` behavior in the installed version before relying on it. |
| A custom combination includes the wrong anatomy. | Class names were guessed or came from the wrong task. | Route class discovery to capability discovery and use exact class names from the selected task. |
| Combined output should carry a label map. | Default combined output is a binary NIfTI. | Add `--multilabel` to `totalseg_combine_masks` when a label-map extension is required. |

## Probability Output Problems

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Probability geometry does not match the input image. | `--save_probabilities` writes model-space softmax arrays plus companion geometry metadata. | Read the companion `.pkl` before aligning probabilities to input-space images. |
| Probability output is not useful for `total`. | The `total` task is assembled from multiple models. | Prefer task-specific probability workflows such as `lung_nodules`, or use final masks for normal automation. |
| Downstream tool expects NIfTI but receives `.npz`. | Probabilities are expert NumPy outputs, not mask files. | Use per-class masks or multilabel NIfTI for standard downstream consumers. |
