---
name: active-learning-and-deployment
description: "Operate PhysicsNeMo active-learning orchestration, support
  utilities, and ONNX export/runtime checks."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Active learning and deployment

Use this sub-skill when the task mentions PhysicsNeMo active learning, acquisition/query strategies, label or metrology loops, active-learning checkpoint/restart, experiment logging around iterative fine-tuning, optimizer/metric helpers for those loops, or ONNX export/runtime checks.

## Route decisions

- **Active learning route:** Use when the user is not just training a fixed dataset, but iteratively performs `training -> metrology -> query -> labeling -> data integration`. Start with [active-learning-and-deploy](references/active-learning-and-deploy.md).
- **Ordinary training route:** If the user only needs a model family, a datapipe, distributed launch, mesh preprocessing, or diffusion sampler/training recipe, route to the corresponding sibling sub-skill instead of forcing the active-learning `Driver`.
- **Deployment/export route:** Use this sub-skill for `physicsnemo.deploy.onnx.export_to_onnx_stream`, ONNX byte-stream checks, optional `onnxruntime` inference, and export caveats. For model architecture support, first use `../model-selection/`.
- **Support utility route:** Use this sub-skill for the active-learning-facing subset of `physicsnemo.utils` logging/checkpoint/capture helpers, `physicsnemo.metrics` metrology choices, and `physicsnemo.optim.CombinedOptimizer`. For distributed checkpoint/domain-parallel details, route to `../distributed-and-domain-parallel/`.
- **Sibling routes:** Data loading and TensorDict/file-format questions go to `../datapipes/`; mesh object validation and geometry go to `../mesh-and-geometry/`; diffusion/generative internals go to `../diffusion-and-generative/`; model-family selection goes to `../model-selection/`.

## Operating sequence

1. Confirm whether the workflow is an active-learning loop, an ONNX/export check, or a support-utility question.
2. For active learning, identify the learner, mutable training data pool, unlabeled pool, query strategy, label strategy or oracle, metrology strategy, queue type, checkpoint policy, logging backend, and CPU/CUDA/distributed constraints.
3. Compose the root-exported active-learning configs and driver. Import protocols from `physicsnemo.active_learning.protocols`, not from the active-learning package root.
4. Register custom strategies if they must be serialized or reconstructed from checkpoints.
5. For ONNX export, run the bundled tiny smoke first when possible: `scripts/onnx_export_smoke.py`. Treat `onnxruntime` as optional and only needed for runtime inference, not for export.
6. If anything fails, use [troubleshooting](references/troubleshooting.md) before changing model/data code.

## High-value checks

- Root active-learning exports are limited to the driver, default loop, config classes, and registry; protocol classes live in the protocols submodule.
- Config JSON does not carry large/non-serializable data pools, distributed manager objects, collate functions, devices, or strategy runtime state; re-provide them at restart.
- Active-learning queues should be serializable via `to_list()`/`from_list()` or picklable if queue state matters.
- Avoid credentialed tracking defaults. Initialize W&B/MLflow explicitly only when the user supplied the needed project/entity/tracking details or requested offline logging.
- ONNX export moves inputs and model through CPU. Do not export in the middle of CUDA graph/static-capture training.
