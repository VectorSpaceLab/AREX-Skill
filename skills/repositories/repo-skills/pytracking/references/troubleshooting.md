# PyTracking Cross-Cutting Troubleshooting

## Import fails for `pytracking` or `ltr`

**Symptoms**: `ModuleNotFoundError: pytracking`, `ModuleNotFoundError: ltr`, or imports work only from one directory.

**Likely causes**: PyTracking is source-tree-style without package metadata; the target checkout root is not on `PYTHONPATH` and the command is not run from the checkout root.

**Recovery**:

- Run from the target checkout root or add that root to `PYTHONPATH` for the current command.
- Verify both packages:
  ```bash
  python - <<'PY'
  import pytracking, ltr
  print(pytracking.__file__)
  print(ltr.__file__)
  PY
  ```
- Do not assume `pip install .` works; this repository does not expose standard package metadata in this snapshot.

## Missing optional Python dependency

**Symptoms**: import errors for `jpeg4py`, `visdom`, `pycocotools`, `lvis`, `skimage`, or `gdown`.

**Likely causes**: upstream install steps were skipped or the selected workflow needs an optional dataset/visualization/download package.

**Recovery**:

- Install only the dependency needed by the selected workflow, not the broad installer by default.
- `visdom` is only needed for debug visualization paths and a server must run separately.
- `pycocotools`/`lvis` are needed for COCO/LVIS dataset loaders and some training settings.
- `gdown` is needed for upstream Google Drive downloads; downloads require user approval.
- `jpeg4py` may additionally need system `libturbojpeg`; if that host package cannot be installed, use workflows that can read images through OpenCV or document the limitation.

## CUDA/backend failure

**Symptoms**: `torch.cuda.is_available()` false, CUDA OOM, device mismatch, or tracker/training silently falls back to slow CPU.

**Likely causes**: incompatible torch/CUDA wheel, no visible NVIDIA GPU, missing driver/container passthrough, too many workers/runs, or model too large for available memory.

**Recovery**:

1. Check torch and tiny allocation:
   ```bash
   python - <<'PY'
   import torch
   print(torch.__version__, torch.version.cuda, torch.cuda.is_available())
   if torch.cuda.is_available():
       print(torch.cuda.get_device_name(0), torch.cuda.get_device_capability(0))
       torch.empty((1,), device='cuda')
   PY
   ```
2. Reduce `--threads`, batch size, or training workers.
3. Start with one short sequence or a tiny command-building check before full benchmarks.
4. Do not call a CPU import or static command check a full verification of CUDA-backed tracker/training behavior.

## `local.py` exists but paths are still wrong

**Symptoms**: dataset not found, checkpoint not found, no results written, `workspace_dir` empty, or training checkpoints go to an unexpected place.

**Likely causes**: generated local templates contain empty strings or default repo-relative output paths that are not suitable for the current machine.

**Recovery**:

- Run the bundled checker:
  ```bash
  python scripts/check_pytracking_setup.py --repo-root /path/to/checkout --require-dataset otb --require-training
  ```
- Edit evaluation config for runtime/dataset paths and LTR config for workspace/dataset/checkpoint paths.
- Re-run the checker, then execute the smallest safe command.

## Broad installer is tempting but unsafe

**Symptoms**: request asks to run `install.sh` or reproduce upstream install exactly.

**Risk**: the upstream installer creates/modifies Conda environments, installs CUDA10-era packages, invokes `sudo`, prompts interactively, and downloads model files.

**Recovery**:

- Ask before any host mutation, sudo command, network model download, or environment replacement.
- Translate install docs into minimal per-workflow packages and backend checks.
- Prefer a private environment when inspecting the repository.

## Empty external submodule or compiled extension missing

**Symptoms**: failure related to PreciseRoIPooling or compiled CUDA/C++ extension.

**Likely causes**: the `ltr/external/PreciseRoIPooling` submodule is uninitialized or its build dependencies/toolkit are unavailable.

**Recovery**:

- Initialize submodules only in the user's target checkout and only when the selected workflow needs the extension.
- Verify compiler/toolkit availability before long source builds.
- Record extension absence as a workflow-specific limitation if the selected tracker/training path can avoid it.

## Network/data/service blockers

**Symptoms**: Google Drive download failures, VOT workspace failures, Visdom connection failures, webcam/video display errors, or notebook analysis failures.

**Recovery**:

- Treat downloads, VOT toolkit/MATLAB/TraX setup, Visdom server startup, cameras, displays, notebooks, and full datasets as external resources.
- Ask for approval and paths before side effects.
- Use command builders, setup checker, and static analysis references to prepare the action before execution.
