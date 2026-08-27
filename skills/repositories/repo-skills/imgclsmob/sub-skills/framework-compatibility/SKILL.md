---
name: framework-compatibility
description: "Route TensorFlow 2, legacy TensorFlow 1 with Tensorpack,
  Keras/Keras-MXNet, and Chainer requests with explicit prerequisites,
  verification limits, and safe CPU fallbacks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Framework compatibility

Use this sub-skill when a request names TensorFlow 2, TensorFlow 1/Tensorpack,
Keras or Keras-MXNet, Chainer, a framework-specific model provider, or a
framework-specific training/evaluation/demo command.

## Route first

1. Identify the requested backend and read [the backend matrix](references/backend-matrix.md).
2. Check optional dependencies without importing a large framework or touching
   the network. The matrix and [troubleshooting](references/troubleshooting.md)
   define the package/distribution and import names.
3. Label the result **bounded-unverified** unless the caller supplies a
   separately verified backend environment. These four compatibility surfaces
   were not live-verified in this production run; do not report them as
   working merely because a provider or CLI exists.
4. For a no-network CPU smoke test or when an optional backend is absent, route
   to the verified CPU Gluon/PyTorch paths in
   [model-inference](../model-inference/SKILL.md). Route dataset-backed runs to
   [training-evaluation](../training-evaluation/SKILL.md).
5. Route any parameter conversion, TF2-to-TFLite export, or cross-framework
   checkpoint question to [conversion](../conversion/SKILL.md) after recording
   the backend gate.

## Safe defaults

- Prefer `pretrained=False`, an empty checkpoint argument, one small synthetic
  input, and `--num-gpus=0` for diagnostics. A pretrained flag can download
  weights and is not an offline smoke test.
- Run `python <entrypoint>.py --help` only to inspect a CLI. Do not start
  training, evaluate a downloaded dataset, or execute conversion tests while
  diagnosing availability.
- Do not infer CUDA support from a visible GPU, a CPU wheel, or a successful
  Python import. Require a matching framework/CUDA environment and a separate
  live verification.

For exact provider names, `prepare_model` signatures, entrypoint flags, and
failure recovery, use the bundled references rather than expanding this router.
