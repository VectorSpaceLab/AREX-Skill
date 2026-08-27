# Cross-Cutting Troubleshooting

Use this page when a failure does not clearly belong to one sub-skill yet. After identifying the surface, route to the nearest sub-skill troubleshooting reference for details.

## Import and Install Failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'monai'` | MONAI is not installed in the active Python. | Install `monai` in that environment or use the Python where it is installed. |
| `ModuleNotFoundError` for `torch` or `numpy` | Base dependencies are missing or installation was incomplete. | Reinstall base MONAI dependencies and run `python -m pip check`. |
| Error importing `nibabel`, `pydicom`, `itk`, `openslide`, or `cucim` | Optional image reader/writer dependency missing. | Install only the package needed for the file format, then route to `sub-skills/data-transforms/`. |
| Error importing `ignite` | Training engines or handlers require `pytorch-ignite`. | Install the Ignite extra or use a plain PyTorch loop; route to `sub-skills/training-evaluation/`. |
| `python -m monai.bundle` fails before command help | Python Fire is absent or package install is broken. | Install `fire`, rerun command help, then route to `sub-skills/bundle-config/`. |
| CUDA unavailable despite GPUs | CPU Torch wheel, missing container GPU passthrough, driver/wheel mismatch, or unsupported CUDA runtime. | Verify `torch.cuda.is_available()` and install a compatible Torch backend before GPU claims. |

## Data and Shape Failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Transform reports missing dictionary key | Input item schema does not match transform `keys`. | Inspect one item, fix keys, or set `allow_missing_keys=True` only when missing keys are expected. |
| Network or loss shape mismatch | Channel-first tensors, one-hot labels, or activation settings are inconsistent. | Route to `sub-skills/modeling-inference/`; verify `(B, C, spatial...)` layout and loss flags. |
| Metric values look stale or accumulate across epochs | Metric object was not reset or outputs were not decollated/postprocessed. | Route to `sub-skills/modeling-inference/` for metric lifecycle or `sub-skills/training-evaluation/` for handler wiring. |
| Inverse transform fails or affine is wrong | Metadata was dropped, lazy operations remain pending, or batch was not decollated. | Route to `sub-skills/data-transforms/` and inspect `MetaTensor` metadata/applied operations. |

## Config, Bundle, and App Failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Bundle `_target_` cannot instantiate | Typo, missing import path, optional dependency absent, or bad argument names. | Route to `sub-skills/bundle-config/`; inspect config syntax and try parser-only smoke checks. |
| CLI override ignored or parsed oddly | Shell quoting or MONAI Bundle id syntax is wrong. | Quote keys containing `#`, `@`, `%`, or `$`; verify with `ConfigParser` before running workflows. |
| Auto3DSeg stops during analysis or bundle generation | Datalist schema, image-label layout, datastats, optional HPO dependency, or expensive training path. | Route to `sub-skills/apps-auto3dseg/`; inspect config before launching jobs. |
| Dataset helper tries to download data | App dataset wrapper has `download=True` or default cache behavior. | Ask before network downloads; use local paths or tiny synthetic fixtures when possible. |

## Safe Recovery Pattern

1. Run `../scripts/check_monai_environment.py` to identify installed MONAI, Torch backend, optional packages, and safe CLI availability.
2. Reproduce on a tiny CPU fixture or parser-only config before using real medical volumes, training loops, exports, downloads, or HPO.
3. Route to the specific sub-skill and run its smoke script when available.
4. Document optional dependencies and skipped expensive checks instead of pretending every MONAI feature is verified.
