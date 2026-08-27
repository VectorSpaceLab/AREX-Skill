# NanoTrack Split Export Reference

## Status and Evidence Boundary

NanoTrack's `pytorch2onnx.py` expresses an intended split between a MobileNetV3
backbone and a BAN head. It loads a configuration and snapshot, chooses CUDA
when available, exports two ONNX files with opset 14, and contains commented
optional simplification steps. The source workflow hard-codes output locations
and does not perform ONNX syntax or runtime-parity checks.

This reference distills that behavior into a safer contract. It does **not**
assert that a checkpoint was available, that export succeeded, or that either
graph ran in ONNX Runtime, NCNN, or a mobile application.

## NanoTrackV3 Tensor Contract

Shapes are NCHW and batch size is one.

| Stage | Graph name | Tensor name | Shape | Meaning |
| --- | --- | --- | --- | --- |
| search image | backbone | `input` | `[1,3,255,255]` | normalized image tensor; preprocessing is owned by inference |
| search feature | backbone | `output` | `[1,96,16,16]` | MobileNetV3-small-v3 feature |
| template feature | head | `input1` | `[1,96,8,8]` | feature derived from the `127x127` template path |
| search feature | head | `input2` | `[1,96,16,16]` | backbone search feature |
| classification | head | `output1` | `[1,2,15,15]` | two-channel classification logits |
| localization | head | `output2` | `[1,4,15,15]` | four positive values after the head's exponential transform |

The split export intent uses opset 14 and no declared dynamic axes. Output file
names such as `backbone-v3.onnx` and `head-v3.onnx` are examples only. Names do
not identify the model variant reliably; pair artifacts with a manifest. The
source filename `pytorch2onnx.py` is evidence of intent, not a bundled command:
its hard-coded paths and CUDA selection are deliberately not copied here.

### Where the shapes come from

- The V3 backbone ends at 96 channels. Its stride pattern maps a `255x255`
  search tensor to `16x16` and a `127x127` template tensor to `8x8`.
- `ModelBuilder.template(z)` caches a backbone template feature. `track(x)` runs
  the backbone on the search tensor and calls the BAN head with cached template
  and current search features.
- The V3 BAN head receives `96x8x8` and `96x16x16`, combines pixelwise and
  depthwise correlation paths, and returns `2x15x15` classification and
  `4x15x15` localization tensors.
- The V3 configuration uses exemplar size 127, instance size 255, stride 16,
  and output size 15.

The split head bypasses `ModelBuilder.track` and accepts features directly.
Postprocessing, windowing, penalties, coordinate decoding, and frame-to-frame
state belong to the `inference` sub-skill.

## Static Backbone Ambiguity

Exporting the backbone with only `[1,3,255,255]` and no `dynamic_axes` normally
fixes its spatial input to `255x255`. That graph does not, by itself, establish a
way to create the required `96x8x8` template feature. Before deployment, select
one explicit architecture and validate it end to end:

1. **Dynamic spatial backbone:** permit the intended spatial axes and test both
   `127x127 -> 96x8x8` and `255x255 -> 96x16x16`. Confirm the target backend
   supports the resulting dynamic graph.
2. **Separate static backbones:** export template and search artifacts from the
   same weights with inputs `127x127` and `255x255`; compare their parameters or
   hashes to prevent variant drift.
3. **Backend-specific template path:** accept only when the implementer can
   document how `96x8x8` is produced and prove parity. Do not infer this path
   from the two source export calls.

Do not silently resize a `16x16` feature to `8x8`; that changes model semantics.

## Safe Export Procedure

### 1. Resolve the model tuple

Treat these as one indivisible tuple:

- NanoTrack version;
- configuration values;
- backbone implementation and channel count;
- active head implementation;
- checkpoint key/shape layout;
- preprocessing contract.

The head module selection can be source-wiring dependent. A V1/V2 configuration
paired with a V3 head or a V3 checkpoint paired with a 64-channel head is not a
valid export just because construction succeeds.

### 2. Validate weights before export

Use a caller-provided, trusted checkpoint. Refuse a missing, empty, unreadable,
or unexpected object. Report missing and unexpected keys and tensor shape
mismatches. Do not silently export random initialization, and do not download a
replacement as a side effect. If non-strict loading is intentional, record each
accepted mismatch in the manifest.

### 3. Prepare the model deterministically

Instantiate once, load weights once, switch to evaluation mode, and disable
gradient recording. Prefer CPU export when operators and memory allow. A source
workflow may automatically choose CUDA, but a visible GPU is not a reason to
change export semantics. Record dtype, device, PyTorch version, exporter mode,
and opset.

Run representative framework forwards before export:

- backbone on `1x3x127x127` and `1x3x255x255`;
- head on `1x96x8x8` and `1x96x16x16`;
- assert finite outputs and exact V3 shapes.

Random tensors prove only structural execution. Numerical usefulness requires
trusted weights and realistic preprocessing.

### 4. Stage artifacts without overwrite

Choose a caller-owned staging root. Keep names relative to that root and reject
`..` traversal, absolute names, symlink surprises, duplicate destinations, and
existing output files unless the caller explicitly approves replacement.
Prefer a temporary file followed by an atomic rename after validation.

Use the bundled planner before export:

```bash
python scripts/export_shape_check.py \
  --artifact-root artifacts \
  --backbone-name candidate/backbone-v3.onnx \
  --head-name candidate/head-v3.onnx
```

The names and path are examples. The checker writes nothing.

### 5. Export and inspect

For the source-compatible split, use the exact tensor names in the contract and
opset 14. Decide static versus dynamic axes explicitly; do not add dynamic axes
only to make a checker pass. After export:

1. load each graph with `onnx` and run its checker;
2. verify opset, graph inputs/outputs, dtypes, and dimensions;
3. run inference in the selected ONNX runtime;
4. compare outputs against framework outputs using documented absolute and
   relative tolerances;
5. test at least one nontrivial input in addition to zeros;
6. reject NaN/Inf and large localization divergence.

When `onnx` is installed, the bundled checker validates structure without
executing the graph:

```bash
python scripts/export_shape_check.py \
  --backbone-model artifacts/backbone.onnx \
  --head-model artifacts/head.onnx
```

### 6. Simplify only as a derived artifact

`onnxsim` is optional. Preserve the original graph and write simplification to
a distinct path. Check the simplifier's boolean result, rerun ONNX validation,
and rerun numerical parity. Simplification can alter operator fusion, constant
folding, shapes, and backend compatibility. A smaller file or successful parser
load is not a parity result.

The MobileNetV3 implementation uses `Hardsigmoid` and `Hardswish` to improve
ONNX optimization relative to manually expanded hard activations. The target
runtime must still support the emitted operators at the selected opset.

## Artifact Manifest

Store a machine-readable or plain-text manifest next to the two graphs with:

- model variant and configuration digest;
- trusted checkpoint digest, without embedding credentials or download URLs;
- framework/exporter/ONNX versions and opset;
- static or dynamic axis policy;
- exact input/output names, shapes, and dtypes;
- preprocessing and output-decoding contract revision;
- unsimplified and simplified graph hashes;
- ONNX checker and parity results with tolerances;
- target backend/tool version when conversion occurs.

Graph file size is an artifact property, not a substitute for parameter count,
MACs, numerical parity, or measured device latency.

## NCNN and Mobile Handoff Boundary

This sub-skill can prepare a handoff; it cannot claim Android, iOS, macOS, C++,
or NCNN build success. External conversion websites are unverified,
documentation-only options and should not receive private weights by default.
A deployment owner must independently establish:

- conversion tool provenance and exact version;
- target support for every ONNX operator, shape rule, and dtype;
- image color order, normalization, resize/crop, and tensor layout;
- template initialization and cache lifetime;
- head output ordering and tracker postprocessing;
- numerical parity at backbone, head, and decoded box levels;
- device-specific latency, thread count, warmup, memory, and thermal behavior;
- packaging, ABI, compiler, and mobile permission requirements.

Conversion success is only a format handoff. Route tracker behavior to
`inference`; route dataset accuracy to `evaluation`.
