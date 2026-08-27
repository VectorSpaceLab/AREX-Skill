# Cross-Cutting Troubleshooting

## Source modules are not importable

RobustVideoMatting is source-checkout and TorchHub oriented in this snapshot; it
has no `setup.py` or `pyproject.toml` package metadata. Local imports such as
`from model import MattingNetwork` require the repository root on `PYTHONPATH` or
a helper's `--repo-root` option.

Use the root environment check:

```bash
python scripts/check_rvm_environment.py --repo-root /path/to/RobustVideoMatting
```

## Legacy requirement pins do not install

The repo requirement files pin historical versions (`torch==1.9.0`,
`torchvision==0.10.0`). Modern Python versions may not have compatible wheels.
For API inspection or skill helpers, use compatible modern PyTorch/TorchVision
packages. For paper reproduction, record any dependency deviation explicitly.

## Network access is unexpectedly needed

Possible sources of network access:

- TorchHub source or pretrained RVM checkpoint downloads.
- `pretrained_backbone=True` downloading TorchVision backbone weights.
- Dataset downloads described by the training docs.

Generated helper scripts do not download weights or data. Ask the user to
provide local checkpoint/data paths when offline or when reproducibility matters.

## CUDA visibility and optional backends

CPU checks validate API and small workflow contracts only. CUDA is optional for
this generated no-import skill's selected verification scope but required for
realistic speed, HR evaluation, and full training.

If CUDA is required by the user's task, check both host visibility and the
Python framework build:

```python
import torch
print(torch.cuda.is_available(), torch.cuda.device_count())
```

A visible GPU in `nvidia-smi` is not enough if PyTorch is CPU-only.

## Media IO failures

Video conversion depends on PyAV/PIMS and available codecs. Prefer sorted PNG
sequence workflows for debugging. If a video-specific task fails, isolate:

1. can the input video be opened,
2. can the output container/codec be created,
3. can the model run on one synthetic frame,
4. can PNG sequence output work.

## Original repo files versus bundled helpers

This skill does not require future agents to open source docs or scripts. When
a workflow needs an executable helper, use a bundled script under this skill's
`scripts/` or the nearest sub-skill's `scripts/` directory. Original repo paths
remain provenance evidence, not runtime dependencies.

## Which sub-skill owns the failure?

- Import, dependency, backend, or general source-layout issues: this root
  troubleshooting file and [scripts/check_rvm_environment.py](../scripts/check_rvm_environment.py).
- Model tensor shape/recurrent-state issues:
  [model-api troubleshooting](../sub-skills/model-api/references/troubleshooting.md).
- Converter, checkpoint, video IO, and exported runtime issues:
  [inference-workflows troubleshooting](../sub-skills/inference-workflows/references/troubleshooting.md).
- Dataset, training config, dataloader, NCCL, and OOM issues:
  [training-data troubleshooting](../sub-skills/training-data/references/troubleshooting.md).
- Metric directory, LR/HR evaluator, and speed benchmark issues:
  [evaluation-tools troubleshooting](../sub-skills/evaluation-tools/references/troubleshooting.md).
