# Metrics, metadata, graph diff, and profiling

This reference covers static model inspection with `onnxsim.model_info` and
runtime simplification profiling with `onnxsim.simplify(..., profile=...)`.
These APIs work from an installed `onnxsim` package and do not require a source
checkout.

## Public inspection APIs

```python
from onnxsim.model_info import (
    ModelInfo,
    annotate_metadata,
    diff_graphs,
    print_graph_diff,
    print_simplifying_info,
)
from onnxsim.profile_merge import merge_ort_traces_into_profile
```

Installed API signatures of interest:

```python
ModelInfo(model: onnx.ModelProto)
annotate_metadata(model: onnx.ModelProto, prefix: str = "onnxsim.") -> onnx.ModelProto
diff_graphs(model_ori: onnx.ModelProto, model_opt: onnx.ModelProto) -> GraphDiff
print_graph_diff(model_ori: onnx.ModelProto, model_opt: onnx.ModelProto, limit: int = 50) -> None
merge_ort_traces_into_profile(profile_path: str, ort_dir: str) -> None
```

## `ModelInfo` metrics

`ModelInfo(model)` computes static metrics without running user inference data:

| Attribute | Meaning | Caveats |
| --- | --- | --- |
| `op_nums` | `defaultdict(int)` of op type to count. Initializers are counted as `Constant` in summary-style reporting. | Function op counts keep the authored function op name. |
| `model_size` | Serialized model size plus external-data byte lengths when recorded. | External data bytes are read from metadata, not loaded. |
| `macs` | Multiply-accumulate count for compute-dominant ops. | Best effort; unknown shapes contribute 0. |
| `flops` | `2 * macs`. | Same caveats as MACs. |
| `mem_access` | Bytes read and written across one forward pass: inputs, weights, outputs. | Unknown shape/dtype tensors contribute 0. |
| `memory_footprint` | Static peak resident bytes from a liveness pass. | Conservative around control-flow subgraphs. |
| `compute_density` | Arithmetic intensity, FLOPs per byte of memory traffic. | `0` when memory traffic is unknown or zero. |

MAC coverage includes common compute-heavy operators such as `Conv`,
`ConvTranspose`, `Gemm`, `MatMul`, `Attention`, and quantized counterparts such
as `ConvInteger`, `QLinearConv`, `MatMulInteger`, and `QLinearMatMul`. Function
bodies are expanded before counting when possible, so compute inside local
functions can be included even while `op_nums` still reports the function op.

### Dynamic and symbolic shapes

- If a dimension has a symbolic `dim_param` and `sympy` is installed, metrics may
  be symbolic formulas such as `21*batch` or terms involving `seq**2`.
- If `sympy` is not installed, named dynamic dimensions are treated as `1`, so
  counts are per-sample/best-effort rather than exact for all batch sizes.
- If a tensor rank, shape, or element width is not known, the affected node or
  tensor contributes `0` to MAC/memory totals instead of guessing.
- Shape inference failures are surfaced as warnings and can make metrics lower
  bounds.

### Minimal metric example

```python
import onnx
from onnx import TensorProto, helper
from onnxsim.model_info import ModelInfo

x = helper.make_tensor_value_info("x", TensorProto.FLOAT, [5, 7])
w = helper.make_tensor_value_info("w", TensorProto.FLOAT, [7, 3])
y = helper.make_tensor_value_info("y", TensorProto.FLOAT, [5, 3])
node = helper.make_node("Gemm", ["x", "w"], ["y"], name="gemm0")
model = helper.make_model(
    helper.make_graph([node], "g", [x, w], [y]),
    opset_imports=[helper.make_opsetid("", 18)],
)

info = ModelInfo(model)
print(info.op_nums)
print("macs", info.macs, "flops", info.flops)
print("memory", info.mem_access, info.memory_footprint)
```

Use [`../scripts/model_metrics_smoke.py`](../scripts/model_metrics_smoke.py) for
a ready-to-run version that also covers metadata and graph diff.

## `annotate_metadata`

`annotate_metadata(model, prefix="onnxsim.")` returns a shape-inferred copy of
the input model with metric strings written into `metadata_props`. The input
model is not mutated.

Default keys:

- Model and graph level:
  - `onnxsim.macs`
  - `onnxsim.flops`
  - `onnxsim.mem_access`
  - model only: `onnxsim.memory_footprint`, `onnxsim.compute_density`,
    `onnxsim.model_size`
- Node level:
  - `onnxsim.macs`
  - `onnxsim.flops`
  - `onnxsim.mem_access`
- Value level for graph inputs, outputs, value_info entries, and initializers:
  - `onnxsim.bytes`

Values are strings. Symbolic values are stored as formulas; concrete values are
stored as decimal strings. A custom prefix is allowed:

```python
from onnxsim.model_info import annotate_metadata

annotated = annotate_metadata(model, prefix="mytool.")
onnx.checker.check_model(annotated)
```

Use metadata annotation when downstream tools need model-local metric facts in
the ONNX file itself. Use plain `ModelInfo` when you only need a report.

## Graph diff APIs

`diff_graphs(original, optimized)` returns a `GraphDiff` dataclass:

```python
GraphDiff(
    removed_nodes=[...],
    added_nodes=[...],
    changed_nodes=[(before, after), ...],
    removed_values=[...],
    added_values=[...],
)
```

Nodes are matched by their output tensor names, not by position. This makes the
diff useful for simplification because an op that keeps the same output name but
changes op type or inputs is reported as changed instead of unrelated remove/add
noise.

`print_graph_diff(original, optimized, limit=50)` prints a capped rich-text
summary with sections for removed, added, changed nodes and values. CLI users can
ask onnxsim to print this after simplification with `--graph-diff`.

Caveats:

- Only the top-level graph is compared.
- Control-flow subgraph bodies are not matched across models.
- Attribute-only changes are not reported unless op type or inputs also change.
- Value names are central; tools that rename everything will produce noisier
  diffs.

## `print_simplifying_info`

`print_simplifying_info(original, optimized)` prints the table onnxsim normally
shows after CLI simplification. It reports op counts, model size, MACs, FLOPs,
memory access, memory footprint, and compute density for both models. Use this
when a human-readable before/after table is enough; use `diff_graphs` when you
need machine-readable changed node/value lists.

## Profiling onnxsim's fixed point

`simplify(profile=...)` profiles every simplification fixed-point function:
shape inference, optimizer passes, constant folding, and any custom rewriter.
It writes Chrome Trace Event Format JSON and prints a per-function summary.

```python
import onnxsim

model_simp, ok = onnxsim.simplify(model, profile="profile.json")
```

CLI equivalent:

```bash
onnxsim input.onnx output.onnx --profile profile.json
```

If the path is an empty string or CLI `--profile` is passed without a value, the
default output file is `onnxsim_profile.json` in the current working directory.
Open the trace with a Chrome trace viewer or Perfetto.

Expected trace/span facts:

- Root and pipeline spans include `Simplify`, `Pipeline`, `OptAndShape`,
  `InferShapes`, `Optimize`, and `FoldConstant`.
- When constant folding actually runs executor sessions, `OrtSession` spans
  appear under `FoldConstant`.
- Complete events include `ts`, `dur`, `args.peak_rss_mb`, and `args.cpu_ms`.
- `cpu_ms` may exceed wall time when underlying execution uses multiple threads.

Environment variables:

| Variable | Effect |
| --- | --- |
| `ONNXSIM_PROFILE=profile.json` | Enables onnxsim fixed-point profiling from any binding. |
| `ONNXSIM_PROFILE_INTERVAL_MS=5` | Sampling interval for peak RSS; default is 5 ms. |

Python `profile=` and CLI `--profile` set `ONNXSIM_PROFILE` only for the call and
restore prior values afterwards.

## ONNX Runtime session profiling

`ort_profile=` enables ONNX Runtime's own per-operator profiler for ONNX Runtime
sessions that onnxsim runs during constant folding and correctness checks.

```python
model_simp, ok = onnxsim.simplify(model, ort_profile="ort_profile")
```

CLI equivalent:

```bash
onnxsim input.onnx output.onnx --ort-profile ort_profile
```

The value is a file prefix, not one fixed filename. ONNX Runtime writes one
`<prefix>_<timestamp>.json` trace per profiled session. The trace can exist only
when an ONNX Runtime session actually ran; if constant folding skipped all
executor work in the current environment, no ORT session trace may be produced.

Environment variable:

| Variable | Effect |
| --- | --- |
| `ONNXSIM_ORT_PROFILE=prefix` | Enables ONNX Runtime session traces from any binding. |

Python `ort_profile=` and CLI `--ort-profile` restore prior environment values
after the call.

## Merging ORT profile events into onnxsim trace

`merge_ort_profile=True` captures ONNX Runtime per-operator traces and merges
them into onnxsim's `profile` trace under each `OrtSession` span. It implies
`profile` if no profile path is given.

```python
model_simp, ok = onnxsim.simplify(
    model,
    profile="profile.json",
    merge_ort_profile=True,
)
```

CLI equivalent:

```bash
onnxsim input.onnx output.onnx --profile profile.json --merge-ort-profile
```

Binding-level environment variable:

| Variable | Effect |
| --- | --- |
| `ONNXSIM_MERGE_ORT_PROFILE=1` | Requests ORT profile merging in the core. It implies `ONNXSIM_PROFILE` if needed. |

Python merge behavior is best effort: if the onnxsim trace or ORT trace files
are missing/unreadable, simplification should still succeed and the onnxsim trace
is left as-is. Temporary ORT traces used for merging are removed after the merge.

## Manual trace merge helper

If you already have an onnxsim trace and a directory of ORT trace JSON files,
merge them manually:

```python
from onnxsim.profile_merge import merge_ort_traces_into_profile

merge_ort_traces_into_profile("profile.json", "ort_trace_dir")
```

Operational details:

- ORT trace files are consumed in modification-time order, matching session
  creation order.
- Extra ORT traces beyond the number of `OrtSession` spans are ignored.
- ORT events are placed on dedicated `onnxruntime` tracks.
- A missing profile file is a no-op, not an exception.

## Safe profiling practice

- Write trace outputs to a scratch or user-selected directory, not into a runtime
  skill tree.
- Profile with `check_n=0` first if correctness checks would create many extra
  ORT sessions.
- Use `ort_profile` for per-kernel ONNX Runtime analysis; use `profile` for
  onnxsim pipeline attribution; use both or merge when both views are needed.
- After a scripted run, verify expected trace paths and confirm profile-related
  environment variables were not unintentionally left set.
