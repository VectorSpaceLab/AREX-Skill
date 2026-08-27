---
name: composer
description: "Use MosaicML Composer for PyTorch training loops, speedup methods,
  loggers, checkpoints, distributed launch, profiling, and model export."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# MosaicML Composer Repo Skill

Use this repo skill when a task involves MosaicML Composer, the `mosaicml` Python distribution, or the importable `composer` package for PyTorch training engines, efficient training methods, callbacks/loggers, checkpoints, distributed launch, profiling, or model export.

Public install:

```bash
pip install mosaicml
```

Minimal import check:

```bash
python - <<'PY'
import composer
print(composer.__version__)
from composer import Trainer
print(Trainer)
PY
```

For optional integrations, read [installation and package map](references/installation-and-package-map.md) before adding extras.

## Route by task

- **Build, run, resume, or debug a training workflow**: read [training](sub-skills/training/SKILL.md).
  This route owns `Trainer`, `ComposerModel`, `ComposerClassifier`, `DataSpec`, `Evaluator`, `Time`, `State`, manual checkpoint load, autoresume, and basic device/precision choices.
- **Add or debug Composer speedup methods**: read [methods](sub-skills/methods/SKILL.md).
  This route owns `composer.algorithms`, `composer.functional`, MixUp/CutMix/LabelSmoothing, model surgery, batch-key routing, and method recipe placement.
- **Make run state visible**: read [observability](sub-skills/observability/SKILL.md).
  This route owns loggers, monitoring callbacks, local/remote file upload, profiler traces, `composer_collect_env`, and observability troubleshooting.
- **Launch or reason about distributed/backend workflows**: read [distributed](sub-skills/distributed/SKILL.md).
  This route owns the `composer` launcher, rank/world-size helpers, distributed samplers, `get_device`, FSDP/FSDP2/TP basics, and auto microbatching caveats.
- **Export models for inference**: read [inference-export](sub-skills/inference-export/SKILL.md).
  This route owns `export_for_inference`, `ExportForInferenceCallback`, TorchScript/ONNX validation, checkpoint-backed export, and optional HuggingFace/PEFT caveats.

## Root references and scripts

- [Installation and package map](references/installation-and-package-map.md): distribution/import names, optional extras, top-level namespaces, console entry points, and first checks.
- [Troubleshooting](references/troubleshooting.md): cross-cutting install/import, backend, optional dependency, CLI, and package-surface failures.
- [Repo provenance](references/repo-provenance.md): source commit, branch, package version, dirty-state baseline, and relative evidence paths.
- [Routing metadata](references/repo-routing-metadata.json): structured scenario placement for managed repo-skill import.
- [check_import.py](scripts/check_import.py): safe JSON import/backend probe for Composer and PyTorch.
- [run_smokes.py](scripts/run_smokes.py): runs bundled sub-skill smoke scripts with the current Python.

## Fast operating workflow

1. Verify installation with `python scripts/check_import.py` from this skill root.
2. Pick the closest sub-skill route from the task wording and load only the references/scripts it names.
3. Start with CPU/tiny-data scripts when debugging model, data, or API issues.
4. Add optional extras only for the integration in use; do not install `mosaicml[all]` unless the task truly spans many optional backends.
5. For GPU/distributed issues, run the distributed `device_probe.py` before launching training.
6. For checkpoint/export issues, decide whether the task is about training-state resume or inference artifact export; route accordingly.
7. Keep generated project code independent of this skill's source provenance and do not copy private machine paths into user scripts.

## Composer concepts to recognize

- `Trainer` is the high-level training loop that manages fit/eval/predict, checkpoint save/load, callbacks, algorithms, logging, precision, devices, and distributed integration.
- `ComposerModel` is the model contract for batches; `ComposerClassifier` wraps simple `(input, target)` classification modules.
- `Algorithm` classes integrate methods through Trainer events; `composer.functional` helpers are for custom loops or one-off model/batch mutation.
- `LoggerDestination` subclasses receive metrics and uploaded files; callbacks and trace handlers generate many of those files.
- The `composer` console entry point launches multi-process distributed jobs and configures rank environment variables.
- `export_for_inference` and `ExportForInferenceCallback` produce TorchScript or ONNX artifacts after optional load/surgery/transform steps.

## Avoid using this skill when

- The task is ordinary PyTorch with no Composer APIs, errors, configs, or artifacts.
- The user is actually using PyTorch Lightning, Accelerate, DeepSpeed, or another training framework without Composer.
- The task is model-family-specific and only incidentally mentions a project that once used Composer.
- The user asks to edit the Composer repository itself rather than operate the package; this skill is for package/runtime use, not maintainer development.

## Verification posture

The generated skill favors CPU-safe, no-download workflows first and documents CUDA/distributed behavior with backend caveats. Optional CUDA was available during construction and a PyTorch CUDA smoke passed, but production-scale multi-rank training should still be verified in the user's target environment before relying on it.
