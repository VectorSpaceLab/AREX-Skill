---
name: training
description: "Plan and diagnose legacy Frustum PointNets v1 or v2 training runs,
  including flags, data contracts, checkpoints, and backend gates."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Training

Use this route when a Researcher wants to train or resume Frustum PointNets.
Read [CLI reference](references/cli-reference.md), then
[training workflow](references/training-workflow.md) before launching. This
release assumes generated frustum pickles and a TensorFlow-1 graph runtime.

## Safe route

1. Validate KITTI inputs and generated pickle ownership through
   `../kitti-data-preparation/SKILL.md`.
2. Choose `frustum_pointnets_v1` for a pure-TensorFlow graph path. Choose v2
   only after `../runtime-and-custom-ops/SKILL.md` proves all custom operators.
3. Run `python scripts/inspect_training_args.py --help` and use its preflight
   before allocating a GPU or creating logs.
4. Set a new log directory, explicit model, point count, channel mode, and
   restore path. Start with a short, separately approved smoke run; the
   repository's default is 201 epochs and is not a smoke test.

Training writes model-source copies, `log_train.txt`, TensorBoard summaries,
and periodic `model.ckpt` files under the log directory. Keep these outputs
outside the source tree when possible and never overwrite a checkpoint from a
different model/point/channel configuration.

## Backend boundary

The verified CPU TensorFlow-1 graph smoke supports API inspection and bounded
v1 checks only. GPU placement, v2 custom ops, and practical training speed are
not verified here. The route does not turn a CPU run into CUDA evidence. Route
post-training validation to `../inference-and-evaluation/SKILL.md`.
