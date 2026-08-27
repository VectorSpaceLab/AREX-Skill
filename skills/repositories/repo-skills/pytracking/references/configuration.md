# PyTracking Configuration and Environment

## When to read

Read this before using any PyTracking runtime, result analysis, or LTR training workflow. Most failures are caused by an import environment that lacks optional dependencies, missing CUDA/checkpoints, or local configuration files with empty dataset/workspace paths.

## Installation shape

PyTracking is an older source-tree-style project: this checkout has no `pyproject.toml`, `setup.py`, or `setup.cfg`. Typical usage is from a cloned checkout with the repository root on `PYTHONPATH` or as the current working directory.

The upstream docs recommend a Conda environment, PyTorch with CUDA, and additional packages such as OpenCV, Matplotlib, pandas, tqdm, Visdom, scikit-image, gdown, pycocotools, LVIS, and jpeg4py. Do **not** run the broad upstream shell installer automatically: it creates a Conda environment, installs packages, invokes `sudo`, downloads model files, and prompts interactively.

Minimum practical checks before work:

```bash
python - <<'PY'
import torch
import pytracking, ltr
print('pytracking ok', pytracking.__file__)
print('ltr ok', ltr.__file__)
print('torch', torch.__version__, 'cuda', torch.cuda.is_available())
if torch.cuda.is_available():
    torch.empty((1,), device='cuda')
PY
```

CPU-only import checks can validate documentation and command construction, but they do not prove full tracker/training runtime for the published network-backed trackers.

## Evaluation local configuration

PyTracking runtime/evaluation uses `pytracking/evaluation/local.py`. Generate a default template in the target checkout when missing:

```bash
python -c "from pytracking.evaluation.environment import create_default_local_file; create_default_local_file()"
```

Important fields:

| Field | Used for |
| --- | --- |
| `results_path` | Saved bounding-box result text files. |
| `segmentation_path` | Saved segmentation outputs for VOS/segmentation trackers. |
| `network_path` | Pretrained tracker network checkpoints. |
| `result_plot_path` | Analysis/plot outputs. |
| `otb_path`, `nfs_path`, `uav_path`, `tpl_path`, `vot_path` | Short-term tracking benchmark roots. |
| `got10k_path`, `lasot_path`, `lasot_extension_subset_path`, `trackingnet_path`, `oxuva_path` | Larger tracking benchmark roots. |
| `davis_dir`, `youtubevos_dir` | VOS dataset roots. |
| `got_packed_results_path`, `got_reports_path`, `tn_packed_results_path` | Benchmark packaging/report locations. |

Use the root checker before execution:

```bash
python scripts/check_pytracking_setup.py --repo-root /path/to/checkout --require-dataset otb
```

## LTR training local configuration

LTR training uses `ltr/admin/local.py`. Generate a default template in the target checkout when missing:

```bash
python -c "from ltr.admin.environment import create_default_local_file; create_default_local_file()"
```

Important fields:

| Field | Used for |
| --- | --- |
| `workspace_dir` | Base directory for checkpoints and training state. |
| `tensorboard_dir` | TensorBoard event output directory, often derived from `workspace_dir`. |
| `pretrained_networks` | Pretrained backbones and initialization checkpoints. |
| `pregenerated_masks` | RTS/LWL-style pregenerated masks when required. |
| `lasot_dir`, `got10k_dir`, `trackingnet_dir`, `coco_dir`, `lvis_dir`, `sbd_dir`, `imagenet_dir`, `imagenetdet_dir`, `davis_dir`, `youtubevos_dir` | Training dataset roots used by selected training settings. |
| `lasot_candidate_matching_dataset_path` | KeepTrack target-candidate dataset path. |

Check both evaluation and training configuration:

```bash
python scripts/check_pytracking_setup.py --repo-root /path/to/checkout --require-dataset lasot --require-training
```

## Checkpoints and external data

- Pretrained tracker models are hosted externally and should be downloaded only with user approval.
- `MODEL_ZOO.md` maps tracker display names to model links and benchmark numbers; runtime parameter files determine concrete checkpoint filenames.
- Full training settings may require pretrained backbones, pregenerated masks, target-candidate JSON files, or converted annotations.
- Datasets are not bundled; each workflow should validate the relevant local path before execution.

## Optional dependencies and services

- `visdom` is used for debug visualizations when `debug > 0`; the server is a separate service.
- `jpeg4py` can improve image loading but may require system `libturbojpeg`. Without the system library, image loading may fall back or fail depending on the path used.
- `spatial-correlation-sampler` is documented for KYS; install/build only when that workflow is selected.
- `pycocotools` and `lvis` are needed for COCO/LVIS dataset loaders and some training settings.
- `PreciseRoIPooling` is an external submodule/compiled dependency in upstream instructions; missing or uninitialized submodule state affects workflows that need it.
- VOT workflows require the VOT toolkit and, for older MATLAB integration, TraX/MATLAB setup.

## Safe workflow policy

- Start with read-only setup checks and command builders.
- Do not run full benchmark datasets, webcam/video GUI sessions, downloads, VOT workspaces, or training epochs unless the user has approved the data, hardware, side effects, and runtime budget.
- Use CUDA smoke checks for GPU-backed claims; do not treat CPU import as proof of network-backed tracker performance.
