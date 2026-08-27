# Cross-Cutting Troubleshooting

Use this root reference for issues that span multiple TotalSegmentator workflows. For workflow-specific details, route to the nearest sub-skill troubleshooting reference.

## Install and Import

| Symptom | Likely cause | Action |
| --- | --- | --- |
| `TotalSegmentator` command not found | Package is not installed in the active environment | Install `TotalSegmentator`, then run `totalseg_info --json` and `python scripts/check_install.py --json`. |
| `ModuleNotFoundError: totalsegmentator` | Python environment mismatch | Run `python -m pip show TotalSegmentator`; make sure the same `python` runs the helper and user code. |
| PyTorch/CUDA import failure | Backend wheel or driver mismatch | Use runtime configuration to inspect `torch.cuda.is_available()` and choose CPU fallback or a compatible PyTorch install. |
| Optional dependency error | Feature-specific extra missing | Install only the dependency for the requested feature, such as `pyradiomics`, `highdicom`, `rt_utils`, `xgboost`, `timm`, or `monai`. |

## Task and Class Selection

| Symptom | Likely cause | Action |
| --- | --- | --- |
| Unknown task | Task name is not in the installed registry | Run `totalseg_info --list-tasks --json` and use an exact task name. |
| ROI subset fails or produces unexpected classes | Class name does not belong to selected task | Run `totalseg_info --classes -ta <task>` and validate exact class names before segmentation. |
| User asks for a modality-specific task | Task modality may differ from input modality | Use registry modality for planning; validate DICOM modality separately when input is DICOM. |
| Licensed task fails before inference | Missing or invalid saved license | Use runtime configuration; do not print or store real license numbers. |

## Runtime, Weights, and Devices

| Symptom | Likely cause | Action |
| --- | --- | --- |
| Run falls back from GPU to CPU | CUDA unavailable or GPU index invalid | Accept CPU fallback with `--fast`/`--roi_subset`, or repair the PyTorch/CUDA stack. |
| CPU run is too slow or memory-heavy | Full-resolution or broad-class segmentation | Use `--fast`, `--fastest`, `--roi_subset`, `--body_seg`, or `--force_split` when appropriate. |
| Offline system tries to download weights | Weights are not staged where TotalSegmentator looks | Set `TOTALSEG_HOME_DIR`/`TOTALSEG_WEIGHTS_PATH`, predownload/import required weights, and run read-only diagnostics. |
| Preview rendering fails | Optional GUI/rendering dependency missing | Install preview dependencies only when `--preview` is required. |

## Input and Output

| Symptom | Likely cause | Action |
| --- | --- | --- |
| DICOM output requested from NIfTI input | DICOM SEG/RTSTRUCT require DICOM input metadata | Use DICOM input or choose NIfTI output. |
| DICOM SEG/RTSTRUCT import error | Missing `highdicom` or `rt_utils` | Install the feature-specific dependency, then rerun DICOM preflight. |
| `save_lowres` rejected | `--save_lowres` requires `--fast`/`--fastest` and NIfTI output | Add the speed flag and avoid DICOM output, or remove `--save_lowres`. |
| Automation cannot find output masks | Single-file output, ROI filtering, or `--skip_saving` | Inspect `run_report.json` and expected output mode before requiring per-class files. |
| Statistics file is empty/zero for a class | Empty mask or border-exclusion behavior | Use `--stats_include_incomplete` only when incomplete border masks should be measured. |

## Safe Debugging Order

1. Run `totalseg_info --json` to prove registry discovery works.
2. Run `python scripts/check_install.py --task <task> --json` for import, version, task, class, and console-script checks.
3. Use the relevant command-builder helper before running any model.
4. Add `--report <path.json>` to every automated segmentation run.
5. Parse `run_report.json` and statistics files with bundled inspectors.
6. Record heavyweight model, network, license, GPU, or training checks as skipped unless the user explicitly asked to run them.
