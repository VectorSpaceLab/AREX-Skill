---
name: loader-pipelines
description: "Build, inspect, and troubleshoot FFCV Loader pipelines: ordering,
  decoders, native and torch transforms, custom Operation contracts, subsets,
  partial batches, distributed sampling, and training integration."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# FFCV loader pipelines

Use this sub-skill when a Researcher must construct or debug an FFCV
`Loader`, its per-field `PipelineSpec`, or the operations between a field
decoder and a training step. It owns traversal/order semantics, decoder-first
pipeline construction, state and preallocated-memory contracts, NumPy/JIT to
PyTorch/CPU/GPU boundaries, index-aware operations, filtering/subsets,
partial batches, and distributed/training integration.

Do not use it for dataset writing/field encoding or broad cache and throughput
tuning; hand those concerns to the writer or performance sub-skill. Keep the
pipeline's exact field names, target shapes/dtypes/devices, order, seed,
subset, and `drop_last` policy explicit before changing code.

## Fast routing

1. Identify the `.beton` fields and desired outputs. Start with [pipelines.md](references/pipelines.md).
2. Choose explicit decoder and transform stages from [image-pipelines.md](references/image-pipelines.md)
   or the relevant field decoder. A decoder is first; put `ToTensor` before any
   torch operation and `ToDevice` before GPU-only work.
3. For a custom operation, read [custom-operations.md](references/custom-operations.md)
   and validate its state, allocation, callable signature, partial-batch, and
   optional `with_indices` behavior.
4. Apply subset/order/distributed/drop-last decisions and then use
   [training-integration.md](references/training-integration.md) for a bounded
   loop. Diagnose construction and runtime failures with
   [troubleshooting.md](references/troubleshooting.md).

## Non-negotiable rules

- A missing pipeline entry gets the field's default decoder plus `ToTensor()`;
  an explicit `None` disables that field. Do not confuse omitted with disabled.
- A sequence is normalized into a `PipelineSpec`; if its first operation is an
  instance of the field's decoder class, it is consumed as the decoder. A
  `PipelineSpec(source=..., decoder=..., transforms=...)` is useful for
  explicit sources and shared operation references.
- Native NumPy operations must remain before `ToTensor`/`ToDevice`. A
  `torch.nn.Module` is wrapped automatically as `ModuleWrapper`, but it is not
  a JIT/Numba operation; place it after tensor conversion and on the intended
  device. `ToTorchImage` changes HWC batches to BCHW.
- Every non-default operation must accurately advance `State` and return an
  allocation query when it writes a new output. Functions must accept the
  arguments the generated graph supplies, return the effective batch, and never
  assume `batch_size` samples when `drop_last=False`.
- `with_indices=True` receives the selected dataset indices, not positions in
  the current batch. Seed or key deterministic index-aware behavior from those
  indices; do not use an unstable worker/thread RNG as the identity.
- `SimpleRGBImageDecoder` rejects variable-resolution image datasets. Use a
  crop/resize decoder when a fixed output shape is required.
- `QUASI_RANDOM` is unavailable with `distributed=True`; use sequential or
  random order with a shared explicit seed instead.

## Verification handoff

For a new pipeline, verify a tiny synthetic `.beton` fixture: field count and
output order, exact shapes/dtypes/devices, all samples under both full and
partial batches, two epochs with the intended seed/order, and a deliberately
variable-resolution image case if images are involved. The installed facts for
this checkout support CPU synthetic loader smoke and tiny A100 CUDA allocation;
CUDA-specific native suites are optional because the GPU is shared.

Two high-value synthetic checks beyond the baseline tests are: (1) write 7 fixed-size images plus labels, load with `indices=[6, 1, 5, 0, 4, 2, 3]`, `drop_last=False`, and an index-aware transform that derives its output from each original id; assert the same id keeps the same result across sequential and seeded-random epochs and that the final one-row batch has no stale values; (2) write mixed-resolution images and run a crop-decoder -> native flip -> `ToTensor` -> `ToDevice` -> `ToTorchImage` -> torch module pipeline on a one-row tail, asserting HWC/BCHW layout, dtype, device, and active batch length at every boundary. Run these outside the runtime skill tree as verification cases.
