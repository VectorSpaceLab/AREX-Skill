# MUNIT Environment Troubleshooting

Use this guide after running the safe checker or after a failed import/setup attempt. Keep fixes scoped to an isolated MUNIT environment.

## Missing Python Packages

| Symptom | Likely missing package | Evidence and fix |
|---|---|---|
| `ImportError: No module named tensorboardX` or `ModuleNotFoundError: tensorboardX` | `tensorboardX` | `train.py` imports `tensorboardX.SummaryWriter`. Install tensorboardX in the legacy environment. |
| `ImportError: No module named yaml` | PyYAML | MUNIT imports `yaml` and reads all experiment configs from YAML. Conda package names vary between `pyyaml` and older `yaml`; pip package is `PyYAML`. |
| `ImportError: No module named PIL` | Pillow | `data.py` and image inference paths use `PIL.Image`. Install Pillow compatible with Python 2.7/3.6 and the selected TorchVision version. |
| `ImportError` involving `torchvision`, `torchvision.transforms`, or `torchvision.utils` | TorchVision | MUNIT uses transforms for preprocessing and `torchvision.utils.save_image` for outputs. Use a TorchVision 0.2.x build paired with PyTorch 0.4.1. |
| `ImportError: No module named scipy` during batch evaluation | SciPy | Only required for `test_batch.py` metric options that use entropy; not required for core setup checks. |

If installing a missing package upgrades PyTorch, TorchVision, Python, PyYAML, or NumPy, reject the transaction and rebuild from a clean legacy environment.

## Modern PyTorch `load_lua` ImportError

MUNIT's utility module imports:

```python
from torch.utils.serialization import load_lua
```

Modern PyTorch removed this API. Because the import is top-level, even code paths with `vgg_w: 0` can fail before training or inference starts. Typical error text includes:

```text
ImportError: cannot import name 'load_lua' from 'torch.utils.serialization'
```

Recommended resolution for faithful reproduction:

1. use PyTorch 0.4.1 with a compatible TorchVision 0.2.x build;
2. keep Python at 2.7 or 3.6;
3. keep CUDA at 9.x when execution, not just import, is required.

Porting alternatives are possible but no longer faithful setup work. They require replacing the Lua-weight loading path, auditing checkpoints, updating deprecated `Variable(..., volatile=True)` usage, retesting CUDA behavior, and revalidating training/inference outputs. Route that work to `model-internals` and workflow-specific sub-skills.

## PyYAML Loader Warning or Failure

MUNIT calls `yaml.load(stream)` without an explicit Loader. Outcomes depend on the installed PyYAML version:

- older PyYAML: usually works silently;
- PyYAML 5.1+: can emit a Loader deprecation/security warning;
- PyYAML 6.x: may raise `TypeError: load() missing 1 required positional argument: 'Loader'`.

For faithful reproduction, prefer a legacy PyYAML version compatible with Python 3.6 and PyTorch 0.4.1. If a modern PyYAML is unavoidable, a local code patch to `yaml.safe_load` or `yaml.load(..., Loader=yaml.FullLoader)` may be needed, but that changes the source behavior and must be recorded as a porting patch.

## CUDA 9.x Stack on Modern GPUs

The original scripts assume CUDA execution:

- `train.py`, `test.py`, and `test_batch.py` call `torch.cuda.manual_seed` and move tensors/models to CUDA;
- `trainer.py`, `networks.py`, and utility preprocessing create CUDA tensors directly;
- CPU-only imports do not prove the workflows are executable.

Common failure modes:

| Error pattern | Interpretation | Response |
|---|---|---|
| `Torch not compiled with CUDA enabled` | CPU-only PyTorch build | Use a CUDA-enabled PyTorch 0.4.1 build for execution, or limit work to static checks. |
| `CUDA driver version is insufficient` | Host driver/runtime mismatch | Use a compatible host driver/container runtime or a different machine. |
| `no kernel image is available for execution on the device` | New GPU architecture unsupported by old CUDA/PyTorch | Prefer P100/V100/Titan-era hardware; do not treat A100 as compatible with unmodified legacy MUNIT. |
| cuDNN symbol/load errors | cuDNN runtime mismatch | Use the CUDA 9.1 + cuDNN 7 pairing from the Docker blueprint or a matching conda setup. |

For A100/Ampere or newer GPUs, faithful execution is uncertain to blocked without a port. The safest setup output is a static/import report plus an explicit hardware limitation.

## Checkpoint, Dataset, and Weight Assets Are Not Bundled

Do not assume the following are present:

- pretrained MUNIT checkpoints under a `models` directory;
- full edges2shoes, edges2handbags, Yosemite, Synthia, or Cityscape datasets;
- the Lua VGG model or converted VGG weight needed when perceptual loss is enabled;
- Inception weights needed by optional batch metrics.

The original demo shell scripts perform network downloads, destructive dataset folder recreation, archive extraction, image conversion, and then launch training. They are intentionally not bundled as environment helpers. Acquire assets only after explicit user approval and route schema/path validation to `data-and-configuration`.

## Safe Checker Interpretation

- `OK` means the specific check passed.
- `WARN` means the environment may be usable for limited/static work but is not faithful or complete.
- `FAIL` means a required dependency or explicitly requested CUDA capability is missing.
- A modern PyTorch `load_lua` failure is effectively a runtime blocker for unmodified MUNIT imports.

Run the checker before and after environment changes. If the fix requires changing source code rather than installing legacy-compatible packages, record that as a porting decision instead of silently calling it setup.
