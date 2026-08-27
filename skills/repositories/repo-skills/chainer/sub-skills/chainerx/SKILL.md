---
name: chainerx
description: "Routes ChainerX build, backend, device, ndarray, and fallback workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# ChainerX

Use this sub-skill when the user asks about ChainerX, `chainerx.ndarray`, `native:0` or `cuda:0` devices, ChainerX source builds, ChainerX CUDA support, or Chainer / ChainerX fallback behavior.

## Typical requests

- "Why is `chainerx.is_available()` false?"
- "How do I build ChainerX with CUDA?"
- "How do I select `native:0` or `cuda:0`?"
- "Can I wrap a ChainerX array in `chainer.Variable`?"
- "Why does an in-place update fail on a grad-tracked ChainerX array?"

## Read these first

- `references/install.md` for source build flags and CUDA knobs.
- `references/api-reference.md` for devices, arrays, backpropagation, and fallback.
- `references/troubleshooting.md` for common ChainerX failures and limitations.

## Use this script

- `../../scripts/chainerx_probe.py` to check whether ChainerX is built and whether a device can run a tiny array operation.

## Include here

- ChainerX source build and `CHAINER_BUILD_CHAINERX` options.
- Native and CUDA device selection.
- `chainerx.ndarray` creation, device transfer, and backpropagation.
- Chainer integration through `Variable`, `Link.to_device`, and backend helpers.
- ChainerX limitations and safe fallback decisions.

## Route elsewhere

- Ordinary Chainer training without ChainerX -> `../training/`
- Distributed ChainerMN and MPI -> `../distributed/`
- ONNX or Caffe export -> `../export/`

## Verification caveat

The default Chainer install can import the `chainerx` package but report `is_available() == False` when ChainerX was not built.
Treat that as a build configuration state, not as evidence that the API guidance is wrong.
