# Install and Backends

This reference covers installing TotalSegmentator, validating imports, optional dependency surfaces, and choosing a runtime device. It intentionally avoids building full segmentation commands; route those to `../segmentation-workflows/SKILL.md`.

## Install Baseline

TotalSegmentator 2.14.0 is distributed as the `TotalSegmentator` package and imports as `totalsegmentator`.

```bash
python -m pip install TotalSegmentator
TotalSegmentator --version
totalseg_info --json
```

Version facts:

- User-facing documentation recommends Python `>=3.10`.
- Package metadata declares `python_requires='>=3.9'`.
- The package requires PyTorch and, in 2.14.0 metadata, declares `torch>=2.1.2` plus `numpy`, `SimpleITK`, `nibabel>=2.3.0`, `tqdm>=4.45.0`, `xvfbwrapper`, `nnunetv2>=2.3.1`, `requests`, `dicom2nifti`, `pyarrow`, and `xmltodict`.
- Use `python -m pip show TotalSegmentator torch nnunetv2` to inspect installed versions without running models.

For automation, first prove the package and registry import before touching images or weights:

```bash
totalseg_info --list-tasks --json
python scripts/check_totalseg_runtime.py --json
```

`totalseg_info` and `totalsegmentator.registry` are safe discovery surfaces: they do not need model weights, a GPU, or input images.

## Optional Dependency Surfaces

Install optional packages only when the workflow needs them:

| Feature | Trigger | Extra dependency |
| --- | --- | --- |
| 3D preview PNG | `--preview` | system `xvfb` plus Python `fury`; package metadata already includes `xvfbwrapper` |
| DICOM SEG output | `--output_type dicom_seg` | `highdicom` |
| DICOM RTSTRUCT output | `--output_type dicom_rtstruct` | `rt_utils` |
| Radiomics statistics | `--radiomics` | `pyradiomics` |
| Body-stats helper CLI | `totalseg_get_body_stats` | `timm`, `monai`, and for xgboost backend `xgboost`; route workflow details to `../auxiliary-analysis/SKILL.md` |
| Phase/modality helper CLIs | `totalseg_get_phase`, `totalseg_get_modality` | `xgboost`; route workflow details to `../auxiliary-analysis/SKILL.md` |

DICOM layout and output interpretation belong to `../dicom-and-formats/SKILL.md`; run-report and statistics parsing belongs to `../outputs-and-statistics/SKILL.md`.

## Device Strings

The CLI and Python API accept these device strings:

- `cpu`
- `gpu`
- `gpu:N`, such as `gpu:1`
- `mps`

The default API/CLI device is `gpu`. Internally, `gpu` maps to CUDA device `cuda:0`; `gpu:N` maps to `cuda:N`. If CUDA is unavailable, TotalSegmentator falls back to CPU and warns that CPU can be slow. If a requested CUDA index is invalid, it also falls back to CPU.

Use the checker to inspect availability without inference:

```bash
python scripts/check_totalseg_runtime.py --device gpu --json
python scripts/check_totalseg_runtime.py --device gpu:1 --json
python scripts/check_totalseg_runtime.py --device mps --json
```

For CPU-only runs, prefer low-memory runtime choices when building segmentation commands elsewhere:

- `--fast` uses a lower-resolution model.
- `--roi_subset <class...>` narrows outputs and can reduce runtime/memory.
- `--save_lowres` only works with `--fast` or `--fastest` and saves model-resolution masks.
- `--nr_thr_saving 1` can reduce memory pressure while saving large outputs.

## PyTorch/CUDA Checks

Use this quick Python probe when diagnosing backend mismatch:

```bash
python - <<'PY'
import torch
print('torch', torch.__version__)
print('cuda_available', torch.cuda.is_available())
print('cuda_device_count', torch.cuda.device_count() if torch.cuda.is_available() else 0)
print('mps_available', bool(getattr(torch.backends, 'mps', None) and torch.backends.mps.is_available()))
PY
```

If `torch.cuda.is_available()` is false on a GPU host, verify that the installed PyTorch build matches the host CUDA driver/runtime. Reinstalling PyTorch is outside TotalSegmentator itself; use the PyTorch install selector appropriate for the target host.

## Import Smoke Checks

Recommended safe import sequence:

```bash
python - <<'PY'
import importlib.metadata
from totalsegmentator.registry import task_registry
print(importlib.metadata.version('TotalSegmentator'))
print(len(task_registry()['tasks']))
PY
```

Expected package facts for version 2.14.0:

- 47 selectable tasks in the registry.
- `total` has 117 classes.
- `total_mr` has 50 classes.
- 15 selectable tasks require a license.

If these counts differ, prefer the live registry over hard-coded values and consider whether the installed package version changed.
