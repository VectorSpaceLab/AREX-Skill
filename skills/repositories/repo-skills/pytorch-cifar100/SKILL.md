---
name: pytorch-cifar100
description: "Operate the script-based PyTorch CIFAR-100 model zoo, training,
  and checkpoint evaluation workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NO_LICENSE
---

# pytorch-cifar100

Use this repo skill when a task involves the `pytorch-cifar100` checkout, its CIFAR-100 CNN architectures, `train.py`, `test.py`, checkpoint folders, TensorBoard logs, or PyTorch/TorchVision setup.

This repository is a script-style PyTorch project rather than an installable Python package. Future agents usually run commands from a checkout root, with the checkout root on the Python import path.

## Start with setup and provenance

- Read `references/repo-provenance.md` before relying on this skill for a different commit or a dirty checkout.
- Read `references/configuration.md` for shared dependencies, paths, constants, data side effects, and backend policy.
- Read `references/troubleshooting.md` for install/import, CUDA, TorchVision data, checkpoint, TensorBoard, and optional dependency failures.
- Run `scripts/check_environment.py --repo-root <checkout>` for a safe import/backend/model-factory probe. It does not download CIFAR-100 or run training.

## Route by task

| User task | Read next | Why |
| --- | --- | --- |
| Pick a model name, validate an architecture, compare supported CNN families, or debug unsupported `-net` values. | `sub-skills/model-zoo/SKILL.md` | Owns the model catalog, `utils.get_network` contract, and shape/parameter smoke helper. |
| Build or explain a `train.py` run, warmup/LR schedule, TensorBoard output, checkpoint save/resume, data download, or LR-finder workflow. | `sub-skills/training/SKILL.md` | Owns long-running CIFAR-100 training and safe command construction. |
| Evaluate a trained checkpoint with `test.py`, validate `-weights`, choose batch/GPU options, or interpret top-1/top-5 errors. | `sub-skills/evaluation/SKILL.md` | Owns checkpoint evaluation, metrics, and command validation. |

## Minimal setup guidance

1. Use a Python environment with PyTorch, TorchVision, NumPy, TensorBoard, and Matplotlib.
2. For legacy `dataset.py` import or custom CIFAR-100 pickle work, also install scikit-image; for `lr_finder.py`, OpenCV is needed.
3. Use CUDA only when the PyTorch build and host driver are compatible. The selected minimum skill verification treats CUDA as optional because the repo CLIs support CPU mode when `-gpu` is omitted.
4. From a checkout root, a minimal import/model check is:

```bash
python - <<'PY'
from argparse import Namespace
import torch
from utils import get_network
net = get_network(Namespace(net='resnet18', gpu=False))
out = net(torch.randn(1, 3, 32, 32))
print(tuple(out.shape))
PY
```

Expected output shape is `(1, 100)`.

## Operational cautions

- `train.py`, `test.py`, and `lr_finder.py` can download CIFAR-100 into `./data` through TorchVision.
- Full training is expensive: 200 epochs, TensorBoard logs under `runs/`, checkpoints under `checkpoint/`, and optional CUDA memory requirements.
- No pretrained checkpoints are bundled. Evaluation needs a user-supplied state-dict file whose architecture matches the `-net` key.
- `lr_finder.py` is optional/reference-only for ordinary tasks because it imports OpenCV, assumes CUDA inside the loop, uses CIFAR-100 data, and writes `result.jpg`.

## Verification status

This skill was built with an agent-confirmed scope. Safe verification covers parser/help checks, import/backend checks, representative model forward passes, generated helper checks, and assertion-backed usability cases. Full CIFAR-100 download, 200-epoch training, and checkpoint evaluation against user weights are intentionally not automatic verification gates.
