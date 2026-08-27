# Pipeline troubleshooting and recovery

Diagnose the first failing boundary: reader/field metadata, decoder state,
NumPy/JIT stage, tensor conversion, device copy, torch module, or training
consumer. Keep a tiny `.beton` fixture and a one-batch reproduction; do not
start with a full dataset or long benchmark.

## Construction and schema errors

| Symptom | Likely cause | Recovery |
|---|---|---|
| `Impossible to use default decoder...` | A custom field has no usable default decoder, or the chosen decoder constructor needs arguments. | Supply the decoder explicitly in the sequence or `PipelineSpec.decoder`; verify `custom_fields` and the field class. |
| `Field <name> has no source` | `PipelineSpec` was constructed without a valid source. | Use the stored field name or a valid operation reference. |
| `Source can't be a node and also have a decoder` | A reference source was combined with an explicit decoder. | A node reference reuses an existing result; remove the decoder and keep transforms only. |
| `...not found in other pipelines` / `Reference ... ambiguous` | A `PipelineSpec` operation reference does not resolve exactly once. | Define the referenced operation in one pipeline and use the correct object identity. |
| Missing output or wrong tuple unpacking | Field entry is `None`, pipeline keys/order differ, or an operation reference changed leaf outputs. | Print active pipeline keys, keep field order explicit, and assert tuple length/shape on the first batch. |
| `SimpleRGBImageDecoder only supports constant image` | Image metadata has differing width/height. | Use `RandomResizedCropRGBImageDecoder` or `CenterCropRGBImageDecoder`, or rewrite storage to a fixed resolution. Adding `ToTensor` cannot fix decoder allocation. |

The default image decoder is strict even when later native transforms could
resize. A variable-resolution test should deliberately assert this failure so
future changes do not accidentally hide an invalid pipeline.

## State, dtype, and layout errors

| Symptom | Likely cause | Recovery |
|---|---|---|
| Numba typing/compilation error after a custom op | A torch object/module, Python object, unsupported closure, or torch dtype entered a JIT stage. | Move the stage after `ToTensor`, remove unsupported captures, or return a correct non-JIT state. Compare with `Compiler.set_enabled(False)` only to isolate the cause. |
| `Can't be in JIT mode and on the GPU` or torch dtype assertion | `declare_state_and_memory` returned an inconsistent state. | Use `replace`; NumPy states are CPU/JIT with NumPy dtypes, torch states are non-JIT with torch dtypes. |
| `torchvision` shape error | Module got HWC instead of BCHW, or a CPU module received CUDA data. | Use `[ToTensor(), ToDevice(...), ToTorchImage()]` before conventional image modules, and put module/device on the same device. |
| `ToTorchImage` assertion about channels-last | The preceding tensor is not in the expected channels-last contiguous layout, or a custom op returned an incompatible view. | Verify HWC tensor strides from `ToTensor`/`ToDevice`; use `channels_last=False` to request an explicit contiguous destination when appropriate. |
| `NormalizeImage` GPU import/runtime error | GPU path dependencies (`cupy`, `pytorch_pfn_extras`) are absent or prior state/device/layout is wrong. | Use CPU normalization, install/verify the optional GPU dependencies, or place `ToDevice` and `ToTorchImage` before it. Mark GPU verification optional if shared hardware/deps are unavailable. |
| Unexpected dtype/value scaling | `ToTorchImage` changes layout only; `Convert` changes dtype; native image transforms operate in uint8 range. | Record dtype/range after each stage. Normalize or scale explicitly; do not infer float normalization from `ToTensor`. |

A custom operation that changes shape, dtype, layout, or device must declare that
change even if the Python callable appears to work for one batch. The graph
uses the declaration to allocate downstream buffers and choose stages.

## Partial batches and stale rows

With `drop_last=False`, the final `batch_indices` may be shorter than
`batch_size`, while allocations remain full sized. Symptoms include extra
samples, shape mismatch, stale values, or a custom operation failing only at
the epoch tail.

Recovery:

1. Make every custom callable use `n = len(batch_indices)` or
   `n = input.shape[0]`.
2. Write and return `dst[:n]`; never return the entire allocation by default.
3. For tuples of buffers, slice every component consistently.
4. Test a dataset whose size is not divisible by batch size and count sample
   ids exactly. The built-in partial-batch tests are the baseline.

The iterator's output selection already slices operation buffers before passing
them to stages, but input arrays and custom temporary logic can still assume a
full batch incorrectly.

## Index-aware and random behavior

| Symptom | Cause | Recovery |
|---|---|---|
| Fixed corruption follows row positions instead of samples | Operation ignores `with_indices` or uses `range(batch_size)` as identity. | Set `generated_code.with_indices=True`, accept the third argument, and key lookup/randomness from `batch_indices`. |
| Index-aware op raises missing-argument error | `with_indices` attribute was set on the operation instead of the returned callable, or callable signature lacks the third argument. | Set it on the function returned by `generate_code` and use `(input, dst, batch_indices)`. |
| “Deterministic” augmentation changes after batch-size/order change | RNG was seeded from batch position or from the repository's batch-dependent mixup convention. | Derive per-sample keys from original dataset ids and an explicit seed; document any intentional batch coupling. |
| Parallel index op is nondeterministic | Rows race on shared RNG/state or shared output. | Use independent per-row keys, read-only captured tables, and disjoint output rows; disable `is_parallel` while debugging. |

Remember that `batch_indices` are original selected ids even when `indices` is
a subset. They are not local rank ids or positions in the subset.

## Device and mixed-mode failures

A safe boundary is:

```text
decoder -> native NumPy/JIT transforms -> ToTensor -> ToDevice ->
ToTorchImage -> torch/native module or GPU operation
```

If a native operation appears after `ToTensor`, move it earlier or replace it
with an equivalent torch module. If a torch module is unexpectedly slow, check
whether it remained on CPU; graph collection warns about this because FFCV
native CPU transforms are generally faster. If GPU copies are not overlapping,
verify pinned host buffers, `non_blocking=True`, CUDA stream use, and that the
consumer waits on the loader's stream only at the intended boundary.

Do not mix a pipeline-level `ToDevice` with unconditional `.cuda()` in the
training loop without measuring/understanding the duplicate copy. Pick one
placement policy and assert the first batch's `.device`.

## Ordering, subsets, and distributed failures

| Symptom | Likely cause | Recovery |
|---|---|---|
| `NotImplementedError` mentioning distributed quasi-random | `OrderOption.QUASI_RANDOM` with `distributed=True`. | Use `SEQUENTIAL` or `RANDOM`; retain a shared explicit seed. |
| Quasi-random `ValueError` about no benefit | Reader has no usable page-to-sample map. | Use sequential/random order or a process-cache-compatible dataset; do not force quasi-random. |
| Different ranks see inconsistent samples | Ranks used different `indices`, seed, order, batch size, or pipeline assumptions. | Construct equivalent loaders; initialize the process group; call no external sampler that changes FFCV's index stream. |
| Filtered ids are wrong for a prefiltered/distributed loader | `filter` performs a temporary sequential scan and derives ids from scan batch positions. | Build the predicate over explicit original ids and pass `indices` directly; treat filter as an eager convenience scan. |
| Validation misses examples | `drop_last=True` remained from training. | Set `drop_last=False`, count actual returned rows, and keep metric denominator based on observed rows. |
| Repeated epoch unexpectedly changes code | `recompile=True`. | Set false for static pipelines; retain true only for compile-time-changing operations. |

For distributed random order without a seed, Loader chooses zero after printing a
warning. Treat that as a recovery default, not a replacement for explicitly
configuring the experiment.

## Memory, queue, and CUDA failures

- A process-cache `MemoryError` occurs while entering an epoch when the page
  schedule cannot fit its slots. Reduce page overlap via order/batch size,
  reduce `batches_ahead`, or use OS cache if the file fits/shared caching is
  preferable. Record the change because it affects behavior/performance.
- Host/device memory grows after increasing `batches_ahead` because the loader
  allocates `batches_ahead + 2` operation/shared buffers and CUDA streams. Lower
  it to the smallest value that preserves overlap.
- A CUDA allocation failure can be caused by a large `batch_size`, multiple
  allocation queries, `ToDevice`, non-channels-last `ToTorchImage`, or queued
  batches. Inspect declared shapes/dtypes and ring-slot count before shrinking
  randomly.
- If an iterator is abandoned early, call/allow `close()` so its memory context
  and producer thread terminate. A daemon thread does not make resource leaks
  safe in a long-running process.

## Bounded diagnostic procedure

1. Reproduce with one or two fields and a tiny writer fixture.
2. Set `drop_last=False` and a batch size that guarantees a partial final batch.
3. Print/assert the output after each conceptual boundary: decoder, native
   transform, `ToTensor`, device, layout, module.
4. Run once with `Compiler.set_enabled(False)` and once enabled; if only JIT
   fails, inspect state/closure/parallel annotations.
5. Use a deterministic sequential order and explicit `indices` before testing
   random/distributed order.
6. Add one difficult feature at a time: variable-resolution decoder, index-aware
   operation, GPU stage, then distributed sampling.
7. Restore the intended order/cache/recompile configuration and record unresolved
   optional CUDA/dependency blockers instead of claiming verification.

## Evidence anchors

- `ffcv/loader/loader.py`, `epoch_iterator.py`, `pipeline/graph.py`, and
  `pipeline/state.py`: errors and execution boundaries.
- `ffcv/traversal_order/*.py`: order and distributed rejection behavior.
- `docs/making_dataloaders.rst`, `working_with_images.rst`, and examples:
  supported pipeline patterns.
- `tests/test_partial_batches.py`, `test_loader_filter.py`, `test_rrc.py`,
  `test_augmentations.py`, `test_image_normalization.py`, and
  `test_basic_pipeline.py`: regression anchors.
