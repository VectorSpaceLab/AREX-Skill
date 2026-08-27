# Installation and package map

Composer is published as the `mosaicml` distribution and imported as `composer`.

## Install commands

Base install:

```bash
pip install mosaicml
```

Common optional extras:

```bash
pip install 'mosaicml[nlp]'          # HuggingFace/transformers datasets support
pip install 'mosaicml[peft]'         # PEFT integration for supported adapters
pip install 'mosaicml[wandb]'        # Weights & Biases logger
pip install 'mosaicml[mlflow]'       # MLflow logger/object store helpers
pip install 'mosaicml[comet_ml]'     # Comet ML logger
pip install 'mosaicml[neptune]'      # Neptune logger
pip install 'mosaicml[tensorboard]'  # TensorBoard logger
pip install 'mosaicml[streaming]'    # MosaicML StreamingDataset support
pip install 'mosaicml[onnx]'         # ONNX export validation/runtime support
pip install 'mosaicml[libcloud]'     # libcloud-backed object store uploads
pip install 'mosaicml[coco]'         # COCO metric/data utilities
```

Use `mosaicml[dev]` only for repository development, documentation, or broad native test execution. Avoid `mosaicml[all]` unless the task truly needs many optional integrations; it pulls many unrelated dependencies.

## First checks

```bash
python - <<'PY'
import composer
from composer import Trainer, Time
print(composer.__version__)
print(Time.from_timestring('2ba'))
print(Trainer)
PY
```

For backend checks, prefer the root bundled helper:

```bash
python scripts/check_import.py
python scripts/check_import.py --require-cuda
```

## Top-level imports

The `composer` namespace exposes:

- `Trainer`
- `ComposerModel`
- `Algorithm`, `Callback`, `Engine`, `Event`, `State`
- `DataSpec`, `Evaluator`
- `Time`, `Timestamp`, `TimeUnit`
- `Logger`

Key packages:

| Namespace | Use |
| --- | --- |
| `composer.trainer` | High-level `Trainer` loop and fit/eval/predict orchestration. |
| `composer.models` | `ComposerModel`, `ComposerClassifier`, HuggingFace wrapper, initializers. |
| `composer.algorithms` | Algorithm classes for Trainer event integration. |
| `composer.functional` | Functional methods for custom PyTorch loops and one-off mutation. |
| `composer.callbacks` | Training lifecycle callbacks, checkpoint saver, export callback, monitors. |
| `composer.loggers` | Logger destinations for metrics, local files, trackers, and remote upload. |
| `composer.profiler` | Profiler, schedules, JSON traces, system and torch profiler integrations. |
| `composer.checkpoint` | Checkpoint state-dict save/load helpers and monolithic checkpoint download. |
| `composer.distributed` | DDP/FSDP/TP preparation and parallel model helpers. |
| `composer.devices` | Device abstractions for CPU, GPU, MPS, TPU, HPU, and Neuron. |
| `composer.optim` | Decoupled optimizers and Composer time-aware schedulers. |
| `composer.utils` | File helpers, environment collection, object stores, inference export, dist helpers, misc utilities. |

## Console entry points

| Command | Use |
| --- | --- |
| `composer` | Distributed training launcher; supports `--version`, `--nproc`, rank topology flags, and script/module/command launch. |
| `composer_collect_env` | Prints system, Python, PyTorch, CUDA, and Composer environment information. |
| `composer_validate_remote_path` | Validates a remote path; expects a remote URI rather than a conventional help flag. |

## Version and compatibility notes

- Composer requires Python 3.10+ in the source metadata used for this skill.
- The source metadata selected `torch>=2.6.0,<2.7.1` and `torchvision>=0.21.0,<0.22.1`.
- CPU workflows can validate model/data/control logic, but CUDA, FSDP, auto microbatching, and GPU profiler behavior must be tested on the target accelerator stack.
- Optional tracker, object-store, ONNX, HuggingFace, PEFT, and Streaming workflows need their matching extras and often credentials or model/data availability.
