# Runtime Troubleshooting

Use this matrix for install/import, backend, config, weights, license, optional dependency, and telemetry failures. Route segmentation-specific input/output errors to sibling sub-skills.

| Symptom | Likely cause | Safe diagnosis | Recovery |
| --- | --- | --- | --- |
| `ModuleNotFoundError: totalsegmentator` | Package not installed in the active Python environment | `python -m pip show TotalSegmentator`; `python scripts/check_totalseg_runtime.py --json` | Install with `python -m pip install TotalSegmentator`; verify `TotalSegmentator --version` and `totalseg_info --json` |
| Import fails inside `torch`, `nnunetv2`, `SimpleITK`, or `nibabel` | Broken or partial dependency install | `python -m pip show torch nnunetv2 SimpleITK nibabel`; checker import error | Reinstall the package and its dependencies in a clean environment; avoid mixing system Python and virtualenv packages |
| Docs say Python `>=3.10`, package installs on `>=3.9` | README recommendation differs from package metadata | `python --version`; `python -m pip show TotalSegmentator` | Prefer Python `>=3.10` for new environments; treat `>=3.9` as metadata compatibility, not the recommended baseline |
| `No GPU detected. Running on CPU` | Default `gpu` requested but PyTorch cannot see CUDA | `python scripts/check_totalseg_runtime.py --device gpu --json`; inspect `torch.cuda.is_available()` | Install a CUDA-enabled PyTorch build matching the host driver, or run with `--device cpu --fast` and/or `--roi_subset` |
| Requested `gpu:N` falls back to CPU | CUDA index is outside `torch.cuda.device_count()` | `python scripts/check_totalseg_runtime.py --device gpu:N --json` | Choose an existing GPU index or omit `:N` for `gpu`/`cuda:0` |
| CPU run is too slow or memory-heavy | Full-resolution full-task inference on CPU | Use checker to confirm CPU-only state, then route command construction to segmentation workflows | Add `--fast`, narrow with `--roi_subset`, use `--nr_thr_saving 1`, or run on GPU/MPS when available |
| `mps` is selected but runtime fails or is slow | Apple MPS support depends on PyTorch and nnU-Net operation coverage | `python scripts/check_totalseg_runtime.py --device mps --json` | Upgrade PyTorch if appropriate, or fall back to `--device cpu --fast`; validate with a small non-critical case before batch use |
| Offline run tries to download weights or fails with missing model files | Required weights were not staged where TotalSegmentator looks | `python scripts/check_totalseg_runtime.py --offline --show-paths --json`; inspect `TOTALSEG_HOME_DIR`/`TOTALSEG_WEIGHTS_PATH` | Pre-stage weights with `totalseg_download_weights -t <task>` on an online machine; copy/mount the resolved home and weights directories; set env vars before running |
| Open tasks list correctly but a licensed task exits | Registry discovery does not require license, but licensed inference does | `totalseg_info --list-tasks --json`; `python scripts/check_totalseg_runtime.py --task <licensed-task> --offline --json` | Run `totalseg_set_license -l <license>` in the same `TOTALSEG_HOME_DIR`; for offline installs, ensure `config.json` with the license is copied or created before inference |
| `totalseg_set_license` says invalid license | Wrong prefix/length or backend validation rejected it | Check only the shape locally; do not print the full license | License must start with `aca_` and be 18 characters; re-enter the key; use `--skip_validation` only when intentionally staging a known-valid license without network |
| License validation times out | Network/backend unavailable during `totalseg_set_license` | Confirm outbound HTTPS access if validation is expected | Retry later or use `--skip_validation` only for a known-valid license; licensed segmentation still requires a saved 18-character license locally |
| Config writes go to an unexpected user/global location | `TOTALSEG_HOME_DIR` was not set for the service/test process | `python scripts/check_totalseg_runtime.py --show-paths --json` | Set `TOTALSEG_HOME_DIR` before starting the process; isolate config per service, test, or container |
| Shared weights are not found | `TOTALSEG_WEIGHTS_PATH` is unset or points at the wrong directory level | Checker with `--show-paths`; inspect existence of the weights directory | Point `TOTALSEG_WEIGHTS_PATH` at the directory that should become `nnUNet_results`; otherwise use the default `<totalseg_home>/nnunet/results` |
| Usage stats are unwanted | `send_usage_stats` defaults to true in new config | `python scripts/check_totalseg_runtime.py --json` reports `send_usage_stats` when config exists | Run `setup_totalseg(); set_config_key('send_usage_stats', False)` before segmentation; preserve other config keys |
| `--preview` fails with display/rendering errors | Missing system `xvfb` or Python `fury`; headless rendering issue | Check optional packages and system `xvfb`; route actual preview command to segmentation workflows | Install system `xvfb` and `pip install fury`; retry after confirming `xvfbwrapper` is installed |
| `--output_type dicom_seg` import error | Missing `highdicom` | Import probe: `python -c "import highdicom"` | `python -m pip install highdicom`; route DICOM details to `../dicom-and-formats/SKILL.md` |
| `--output_type dicom_rtstruct` import error | Missing `rt_utils` | Import probe: `python -c "import rt_utils"` | `python -m pip install rt_utils`; route DICOM details to `../dicom-and-formats/SKILL.md` |
| `--radiomics` import error | Missing `pyradiomics` | Import probe: `python -c "import radiomics"` | `python -m pip install pyradiomics`; route output interpretation to `../outputs-and-statistics/SKILL.md` |
| Body-stats, phase, or modality helper CLI import error | Optional auxiliary dependencies missing | Inspect the specific helper CLI error | Install only the needed extras (`timm`, `monai`, `xgboost` as appropriate) and route workflow details to `../auxiliary-analysis/SKILL.md` |

## Safe Escalation Order

1. Run `totalseg_info --json` to prove the package registry is available.
2. Run `python scripts/check_totalseg_runtime.py --json` to inspect imports, config, task counts, and backend visibility without model side effects.
3. Add `--task <task>` to the checker to verify license flag and class count for the intended task.
4. Add `--offline` to make the checker report whether a licensed task has a locally shaped saved license and whether a weights directory exists.
5. Use `--show-paths` only in private logs when path resolution itself is the problem.
6. Only after these checks pass, route to `../segmentation-workflows/SKILL.md` to build or run actual segmentation.

## Do Not Do

- Do not parse TotalSegmentator progress text for automation; use `--report` after real runs and route report parsing to `../outputs-and-statistics/SKILL.md`.
- Do not run `totalseg_download_weights -t all` as a casual smoke test; it can download many models.
- Do not validate licenses by printing or sharing the license value.
- Do not assume a registry task is runnable offline just because `totalseg_info` lists it; registry discovery intentionally ignores weights and license state.
