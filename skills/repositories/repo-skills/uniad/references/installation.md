# UniAD installation and import guidance

## Public v2.0 stack

The UniAD v2.0 docs describe a Python 3.9 CUDA/OpenMMLab stack:

```bash
conda create -n uniad2.0 python=3.9 -y
conda activate uniad2.0
pip install torch==2.0.1 torchvision==0.15.2 torchaudio==2.0.2 --index-url https://download.pytorch.org/whl/cu118
pip install -v mmcv-full==1.6.1 -f https://download.openmmlab.com/mmcv/dist/cu118/torch2.0/index.html
pip install mmdet==2.26.0 mmsegmentation==0.29.1 mmdet3d==1.0.0rc6
pip install -r requirements.txt
```

Use these versions first for result reproduction. If a package index no longer serves a compatible wheel for the exact combination, do not silently mix arbitrary OpenMMLab releases: record the substitution, verify imports, and run a config parse before starting a long job.

## Repository import model

UniAD does not expose a normal installed Python distribution in this checkout. It is used as an OpenMMLab plugin package rooted at `projects.mmdet3d_plugin`. Run commands from the repository root or set `PYTHONPATH` so Python can import `projects`.

Minimal check:

```bash
PYTHONPATH="$(pwd)":$PYTHONPATH python - <<'PY'
import torch, mmcv, mmdet, mmseg, mmdet3d
print(torch.__version__, torch.version.cuda, torch.cuda.is_available())
print(mmcv.__version__, mmdet.__version__, mmseg.__version__, mmdet3d.__version__)
import projects.mmdet3d_plugin
print('UniAD plugin import ok')
PY
```

## What belongs in the environment

- Torch/TorchVision/Torchaudio with the CUDA tag required by the selected MMCV wheel.
- `mmcv-full`, not CPU-only/lite MMCV, for full model ops.
- `mmdet==2.26.0`, `mmsegmentation==0.29.1`, and `mmdet3d==1.0.0rc6` per docs.
- `requirements.txt` packages, notably `numpy==1.22.4`, `opencv-python==4.8.0.76`, `einops`, `casadi`, `pytorch-lightning`, `torchmetrics`, `motmetrics`, and `networkx==2.5`.

## Compatibility cautions

- `mmdet3d==1.0.0rc6` has old dependency metadata in some environments. Prefer the repo's documented/pinned requirements when they are needed for import or Python-version compatibility, but keep the conflict visible in reports.
- NumPy 2.x can break binary extensions built against NumPy 1.x; UniAD pins NumPy 1.22.4.
- The legacy Dockerfile in this repo targets older CUDA/Torch/OpenMMLab versions than v2.0 docs. Treat it as historical context unless the user explicitly asks for a legacy environment.
- A CPU-only environment can parse configs and inspect scripts but does not validate UniAD train/eval behavior.
