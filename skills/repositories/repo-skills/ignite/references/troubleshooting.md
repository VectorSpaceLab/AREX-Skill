# Troubleshooting

This file collects cross-cutting failures that do not belong to a single sub-skill.

## Import and install failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ImportError` from `torch._C` or `libtorch_cpu.so` mentioning `iJIT_NotifyEvent` | Mixed or incompatible PyTorch binaries from conda and pip. | Remove the conflicting `torch` / `torchvision` packages and reinstall one consistent wheel stack. In a clean private environment, keep PyTorch, torchvision, and their dependencies from the same distribution source. |
| `ModuleNotFoundError: No module named 'ignite'` | The package is not installed in the active interpreter. | Install `pytorch-ignite` or use an editable install from the source checkout. |
| `DeprecationWarning` from `ignite.contrib.*` | Old import path is still in use. | Move to the modern `ignite.engine`, `ignite.handlers`, `ignite.metrics`, or `ignite.handlers.logger_utils` API. |

## Optional dependency failures

| Surface | Missing package(s) | Recovery |
| --- | --- | --- |
| ROC/PR/Average Precision, classification report, clustering, some regression metrics | `scikit-learn` | Install `scikit-learn` and rerun the metric or test. |
| FID, Inception Score, correlation helpers that use SciPy | `scipy` | Install `scipy`; if you are using default Inception-based features, keep `torchvision` available too. |
| Object-detection mAP and Inception-based image metrics | `torchvision` | Install `torchvision` that matches your PyTorch build. |
| Fairness metrics | `fairlearn` | Install `fairlearn` before using fairness metrics or fairness-focused tests. |
| BLEU / ROUGE test helpers | `nltk`, sometimes `filelock` | Install `nltk`; the test helpers may also download NLTK data when running those comparisons. |
| GPU info metric | `pynvml<12` and an NVIDIA GPU | Install the pinned `pynvml` version and run on a machine with CUDA-capable hardware. |
| Progress bar / logging helpers | `tqdm`, `tensorboardX`, `tensorboard` | Install the helper package that matches the logger or progress feature you are using. |
| Experiment tracking loggers | `clearml`, `mlflow`, `neptune-client`, `polyaxon`, `wandb`, `visdom` | Install only the logger package you are using and configure its service or credentials. |
| Distributed backends | `horovod`, `torch_xla`, or other backend-specific packages | Select the matching backend route and install the matching runtime package. |

## Engine and training-loop errors

- `max_epochs` and `max_iters` are mutually exclusive in `Engine.run(...)`.
- `epoch_length` is required if you call `run()` with `data=None`.
- `amp_mode` cannot be combined with `mps` or `xla` device modes.
- `scaler` only makes sense when `amp_mode="amp"`.
- `gradient_accumulation_steps` must be positive.
- When resuming, keep `epoch_length` consistent with the saved state.

## Checkpoint and logging issues

- `Checkpoint` and `output_path` / `save_handler` are mutually exclusive in the common helper path.
- `hash_checkpoint()` moves the file into the target directory; do not call it if you still need the original path.
- `setup_logger()` uses the current distributed rank by default. If only rank 0 should log, keep the default behavior.
- `ProgressBar` depends on `tqdm`; TensorBoard helpers depend on the matching TensorBoard package.

## Distributed-backend confusion

- `ignite.distributed.available_backends()` reflects the backends available in the current environment. In a CPU-only setup it may only report `('gloo',)`.
- `Parallel(backend=None)` is the serial path. Use it when you only want the distributed helper namespace without initializing a process group.
- `torchrun`, `horovodrun`, and TPU/XLA flows all need their matching backend package and runtime support.
- If `Parallel` complains about `tcp://` init methods, switch to `env://` or provide `MASTER_ADDR` / `MASTER_PORT`.

## Metric-shape and data-format problems

- Most metrics expect `output_transform` to return `(y_pred, y)` or an equivalent mapping.
- ROC/PR metrics expect binary labels and scores or probabilities.
- `SSIM` needs a valid `data_range` and the expected 2D or 3D image shape.
- Object-detection metrics expect dictionaries or tensor lists in the documented box format.
- `NotComputableError` usually means the metric has not seen enough valid examples yet.

## When in doubt

If a failure is not obvious, start with the smallest synthetic smoke check in `scripts/core_smoke.py`, then drill down into the owning sub-skill.
