---
name: core-xconv-and-operators
description: "Build and adapt PointCNN X-Conv and X-DeConv graphs, pointfly
  operators, model heads, and legacy sampling diagnostics."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Core X-Conv and operators

Use this route when a task asks to inspect, adapt, or construct the PointCNN
core graph: X-Conv/X-DeConv layers, pointfly geometry and sampling operators,
classification or segmentation heads, setting tuples, or the FPS custom
operator. This is a TensorFlow 1.x graph-mode contract. It is not a training,
data-conversion, checkpoint, or evaluation workflow.

## Runtime boundary

- The implementation requires the legacy TensorFlow 1.x graph APIs, including
  `tf.contrib`, `tf.layers`, placeholders, `tf.py_func`, and sessions. A
  TensorFlow 2.x import, even when `tf.compat.v1` exists, is not by itself a
  compatible runtime for this contract.
- The FPS/probability/gather sampling kernels are registered for GPU only.
  There is no CPU fallback in the operator implementation. TensorFlow import,
  GPU discovery, graph construction, or shared-library loadability is not an
  FPS execution pass.
- Current runtime evidence is limited: TensorFlow 1.15 import and device
  discovery passed, while a minimal GPU/custom-op session timed out. Keep FPS
  status `BLOCKED_REQUIRED_BACKEND`; never report that the GPU operator passed.

## Start safely

1. From the installed skill directory, run the API probe before importing model
   modules:

   ```text
   python scripts/check_tensorflow_api.py --graph-smoke
   ```

   It performs an optional static graph build and fails clearly when TensorFlow
   or a required legacy API is unavailable. It does not create a session or
   enumerate devices.
2. Read [the API reference](references/api-reference.md) for signatures and
   tensor contracts, then [the architecture and settings guide](references/architecture-and-settings.md)
   before changing `K`, `D`, `P`, `C`, links, or decoder indices.
3. Validate every layer against the point count of its actual `pts` input. An
   X-Conv requests `K * D` neighbors and therefore needs `K * D <= M`; an
   inverse-density (`ids`) sampler also needs `K <= M`. For a newly selected
   query set, use `0 < P <= M`; `P == -1` means all current points, not a valid
   custom-op `npoint`.
4. For `sampling == 'fps'`, inspect prerequisites before any build or load:

   ```text
   python scripts/inspect_sampling_build.py --sampling-dir <sampling-dir>
   ```

   Add `--check-load` only for an intentional, existing
   `tf_sampling_so.so` load attempt. Add `--show-build-command` only to print a
   manual recipe for review. The diagnostic never compiles, downloads, trains,
   or runs a kernel.

## Core graph contracts

- `pointcnn.xconv` consumes `pts [N,M,3]`, optional `fts [N,M,F]`, and query
  points `qrs [N,P,3]`; it returns `[N,P,C]`, or `[N,P,C + C//4]` when the
  final layer enables global features. It selects `K*D` neighbors, retains
  every `D`-th neighbor, centers them at each query, optionally learns the
  `[K,K]` X transform, and applies a separable convolution over the neighbor
  axis.
- `PointCNN(points, features, is_training, setting)` stores point and feature
  tensors in `layer_pts` and `layer_fts`, then builds the configured X-Conv,
  optional X-DeConv, and pointwise FC stacks. Input features are split after
  the first three coordinate channels and projected before the first X-Conv.
- `xconv_params` entries are `(K, D, P, C, links)`. `K` is retained-neighbor
  count, `D` is dilation stride, `P` is query count, `C` is output channels,
  and `links` concatenate earlier feature tensors after they are sliced to the
  current query count. Links are supported only with `sampling == 'random'` in
  this implementation and must resolve to existing, row-aligned layers.
- `xdconv_params` entries are `(K, D, pts_layer_idx, qrs_layer_idx)`. The
  indexed coarse layer supplies source points/features and the indexed finer
  layer supplies query points/skip features. The query layer contributes its
  inherited `P` and `C`; the decoder X-Conv is fused with the skip tensor and
  projected back to `C`. Validate both layer indices and `K*D` against the
  coarse source point count.
- Sampling semantics are distinct: `random` takes the first `P` source points
  in this graph (it is not a random draw), `ids` uses inverse-density sampling
  through a Python/NumPy callback, and `fps` calls the CUDA custom operator.
  Do not use a `random` or `ids` graph smoke as evidence that an FPS graph or
  kernel works.
- `pointcnn_cls.Net` produces per-point training logits
  `[N,P,num_class]`, then conditionally averages the final point axis for
  inference to `[N,1,num_class]`. `pointcnn_seg.Net` keeps the point axis and
  produces `[N,P,num_class]` in both training and inference. The outer
  workflows apply softmax, argmax, and losses; those are not part of either
  `Net` constructor.

## Common routes

- **Change an X-Conv graph:** preserve coordinate rank `[N,M,3]` and feature
  rank `[N,M,F]`; choose queries with the setting sampler; account for the
  first-layer feature projection, link concatenation, optional global
  `C//4` widening, and final channel count.
- **Change a setting:** use the tuple names and layer-index rules in the
  architecture reference. Check the actual point count entering each layer,
  not only the original input size. Keep `P == -1` only where all current
  points are intended, and resolve a positive query count before calling FPS.
- **Use pointfly directly:** preserve the exact signatures and ranks in the API
  reference. In particular, `knn_indices_general` returns `[N,P,K,2]` gather
  indices, `get_indices` creates NumPy gather indices, and `augment` is a graph
  op. `inverse_density_sampling` and duplicate filtering use `tf.py_func`, so
  they require a local graph/session path and are not graph-free or remote-safe
  by implication.
- **Diagnose sampling ABI/toolkit failures:** inspect source markers, `nvcc`,
  C++ compiler, TensorFlow include/library paths, CUDA include/runtime paths,
  expected library name, and the legacy C++ ABI setting. A successful load only
  separates dynamic-link failures from later execution failures; it does not
  clear the required GPU gate.

## Boundaries and handoff

Route training and checkpoint production to the classification or segmentation
workflow sub-skills; route dataset layout/conversion to data preparation; and
route metrics and prediction artifacts to evaluation. For symptoms and recovery
rules, read [troubleshooting](references/troubleshooting.md).

Before handing off a graph adaptation, record:

- input and query shapes at every X-Conv/X-DeConv;
- `K*D`, `K`, `P`, link, decoder-index, and channel checks;
- selected sampler and whether it imports the custom-op wrapper;
- classification or segmentation head output shape for both `is_training`
  branches where applicable; and
- TensorFlow API result separately from GPU discovery, shared-library loading,
  and kernel execution.

A graph-only smoke can validate legacy API presence, static ranks, and some
X-Conv tensor algebra. It cannot prove the GPU FPS kernels. Preserve
`BLOCKED_REQUIRED_BACKEND` or a clearly partial status until a bounded GPU
operator session completes.
