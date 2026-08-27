# Performance and Batching

This reference covers Hummingbird performance knobs that are safe to use during normal operating tasks: thread counts, fixed-size batching, TVM padding, and benchmark boundaries. It does not replace a real benchmark plan for production performance claims.

## Thread control with `N_THREADS`

Hummingbird sets `extra_config[constants.N_THREADS]` to the number of physical CPU cores by default. During conversion/container setup it sets PyTorch intra-op threads to this value and sets inter-op threads to 1. ONNX Runtime containers use the same `n_threads` setting for intra-op session options with inter-op threads set to 1.

```python
from hummingbird.ml import convert, constants

hb_model = convert(
    trained_model,
    "torch",
    test_input=X_small,
    extra_config={constants.N_THREADS: 1},
)
```

Use explicit `N_THREADS` when the user needs reproducible latency comparisons, shared-machine friendliness, or single-core parity checks. Be cautious about repeatedly changing PyTorch threading in a long-lived process; prefer a fresh process for clean performance measurements.

## `convert_batch(...)` fixed-batch workflow

`convert_batch(model, backend, test_input, remainder_size=0, device="cpu", extra_config={})` creates a batch-aware container. The number of rows in `test_input` is interpreted as the main batch size. At prediction time, supported inputs can have row count:

```text
main_batch_size * k + remainder_size
```

where `k` is any integer. If `remainder_size` is nonzero, Hummingbird creates or reuses an auxiliary remainder path depending on the backend.

Typical uneven-row pattern:

```python
from hummingbird.ml import convert_batch

batch_size = 10
X_trace = X_train[:batch_size]
remainder_size = X_eval.shape[0] % batch_size

hb_model = convert_batch(
    trained_model,
    "torch.jit",
    test_input=X_trace,
    remainder_size=remainder_size,
)
pred = hb_model.predict(X_eval)
```

The same pattern is used by PyTorch, TorchScript, ONNX, and TVM tests. TVM benefits the most because plain `convert(..., "tvm", test_input=X)` is shape-specialized.

## `BATCH_SIZE` extra configuration

`constants.BATCH_SIZE` is a converter-level configuration distinct from `convert_batch`'s `test_input` row count. Hummingbird documents it as selecting whether to partition the input dataset at inference time in `batch_size` partitions, and KNeighbors converters require an explicit `BATCH_SIZE` value.

```python
from hummingbird.ml import convert, constants

hb_knn = convert(
    trained_knn_model,
    "torch",
    test_input=X_small,
    extra_config={constants.BATCH_SIZE: X_small.shape[0]},
)
```

Do not assume `BATCH_SIZE` replaces `convert_batch` for TVM shape flexibility. Use `convert_batch` when the prediction row count must be `batch_size * k + remainder_size`.

## TVM performance controls

### `TVM_MAX_FUSE_DEPTH`

TVM compilation can be expensive. Hummingbird defaults the Relay fuse-depth configuration to 50. The package exposes `constants.TVM_MAX_FUSE_DEPTH` so agents can reduce or tune this value; tests commonly use 30, and some tree traversal cases use 10.

```python
from hummingbird.ml import convert, constants

hb_tvm = convert(
    trained_model,
    "tvm",
    test_input=X_trace,
    extra_config={constants.TVM_MAX_FUSE_DEPTH: 30},
)
```

If compilation appears to run indefinitely, lower the fuse depth before increasing hardware scope or retrying repeatedly.

### `TVM_PAD_INPUT`

TVM statically compiles fixed input shapes. With plain `convert(..., "tvm", X_trace)`, prediction on a different batch size can raise an assertion. `constants.TVM_PAD_INPUT` pads the input batch dimension with zeros so shorter batches can be accepted, but the package warns this may considerably hurt performance.

```python
hb_tvm = convert(
    trained_model,
    "tvm",
    test_input=X_trace,
    extra_config={constants.TVM_PAD_INPUT: True},
)
```

Prefer `convert_batch` when a predictable batch/remainder pattern exists. Use padding when the user explicitly values flexibility over speed and has validated output parity.

## Minimal performance validation checklist

For a lightweight, bounded check:

1. Run the backend probe script and record backend/CUDA/TVM availability.
2. Convert a representative trained model with the intended backend and any `extra_config` knobs.
3. Compare predictions against the source model on a small held-out batch with an appropriate tolerance.
4. Time warm and measured prediction calls separately; avoid including model training or conversion time unless the user asks for end-to-end cost.
5. State CPU/GPU, thread count, backend, batch shape, and package versions with any timing.

## Benchmark boundary

Hummingbird benchmark suites cover tree, operator, and pipeline experiments from the research evaluation. Complete benchmark runs are expensive and can take several days. Do not run those benchmark suites as routine skill validation. Treat benchmark scripts as reference-only unless the user explicitly asks for them, provides datasets, and accepts the runtime budget.
