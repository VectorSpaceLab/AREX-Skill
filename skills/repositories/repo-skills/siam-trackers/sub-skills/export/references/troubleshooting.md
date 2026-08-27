# NanoTrack Export and Performance Troubleshooting

## Diagnostic Order

Check failures in this order:

1. model variant and configuration;
2. trusted checkpoint presence and state-dict compatibility;
3. framework forward shapes and finite outputs;
4. export arguments and staging paths;
5. ONNX graph structure and runtime parity;
6. optional simplification;
7. target converter/runtime compatibility;
8. benchmark boundary and timing correctness.

This order prevents a conversion or speed tool from hiding an earlier model
assembly error.

## Failure Matrix

| Symptom | Likely cause | Safe diagnosis | Resolution |
| --- | --- | --- | --- |
| Snapshot path is missing | Export/speed workflow assumes a local checkpoint | Check the caller-supplied path before model construction; do not search unrelated directories or download | Ask for a trusted compatible checkpoint and record its digest |
| Many missing/unexpected keys | Variant or wrapper mismatch; checkpoint nesting/prefix differs | Print key categories and tensor shape mismatches without exposing credentials | Normalize only a known prefix; otherwise select the matching config/head/checkpoint tuple |
| Head expects 64 channels but receives 96, or conversely | V1/V2 and V3 components were mixed | Check backbone type, adjust channels, active head implementation, and checkpoint together | Rebuild one coherent variant; do not add an arbitrary projection |
| Backbone search output is not `[1,96,16,16]` | Wrong variant, image shape, layout, or modified stride | Run a no-grad framework shape probe | For this contract use V3 NCHW `[1,3,255,255]`; treat intentional variants as new contracts |
| Head template/search dimensions are rejected | Inputs are swapped or template feature was not produced from the 127 path | Validate `input1=[1,96,8,8]`, `input2=[1,96,16,16]` | Correct ordering; never resize a 16x16 feature as a silent substitute |
| One static backbone rejects the template image | It was exported only with static `255x255` input | Inspect ONNX input dimensions | Export validated dynamic spatial axes, separate template/search graphs, or document another proven backend path |
| Outputs are not `2x15x15` and `4x15x15` | Wrong head implementation/config or graph outputs | Probe the framework head first, then inspect ONNX names and shapes | Restore the V3 head and output-size-15 contract before export |
| Export overwrites or lands in an unexpected directory | Hard-coded or current-working-directory-relative output path | Run `export_shape_check.py` with a caller-owned staging root | Use unique relative names; preserve previous graphs and manifests |
| `onnx` import fails | Optional structural-check dependency is absent/incompatible | Probe `python -c 'import onnx; print(onnx.__version__)'` in the caller-controlled environment | Install a currently compatible ONNX release; do not copy historical pins blindly |
| ONNX Runtime import/session fails | Missing/incompatible runtime provider or unsupported graph | Record runtime/provider versions and inspect graph with `onnx` first | Choose a compatible runtime/provider; separate parser success from numerical parity |
| Opset is not 14 | Export defaults or exporter behavior changed | Inspect the model opset import | Re-export intentionally at 14 for this contract, or treat another opset as a separately validated target |
| Hardswish/Hardsigmoid conversion fails | Target runtime lacks emitted operator support | List emitted operators and target capability/version | Upgrade target runtime or make an evidence-backed graph change, then rerun parity |
| `onnxsim` is unavailable | Optional simplifier was not installed | Confirm unsimplified graph already validates | Skip simplification or install a compatible simplifier; simplification is not required for ONNX correctness |
| Simplifier returns false or parity drifts | Unsupported rewrite, shape inference issue, or numerical change | Preserve and compare unsimplified graph; inspect simplifier check flag | Reject simplified artifact until syntax and numerical parity both pass |
| THOP fails or reports unsupported operations | `thop` missing or correlation/operator hooks unsupported | Capture warnings and compare split/full profiles | Install a compatible THOP release and add reviewed custom counters; never guess omitted MACs |
| Reported MACs differ from documented FLOPs | Different convention, graph boundary, or tool coverage | Record whether one MAC equals one or two FLOPs and which stages were counted | Report tool-native MACs first and explain any FLOP conversion |
| CUDA FPS is implausibly high or unstable | Asynchronous kernels, missing synchronization, warmup/clock effects | Validate plan with `profile_shape_check.py`; repeat with synchronization | Synchronize timed regions or use synchronized CUDA events; report median and spread |
| CPU result changes with environment | Threading/backend/affinity changed | Record intra-op, inter-op, BLAS/backend threads and hardware | Fix thread policy and rerun multiple repeats |
| Mobile conversion succeeds but boxes differ | Format conversion omitted preprocessing, tensor ordering, or decoding parity | Compare framework/ONNX/target intermediate tensors | Fix the earliest divergent boundary; route tracker decoding to `inference` |

## Optional Dependency Policy

Install only what the selected check needs:

- base construction/export: compatible PyTorch and configuration dependency;
- ONNX structural validation: `onnx`;
- numerical ONNX parity: a suitable `onnxruntime` provider;
- optional simplification: `onnxsim`/ONNX Simplifier;
- operation/parameter estimates: `thop`.

Historical setup instructions pin old Python, CUDA, PyTorch, Pillow, Ray, and
other packages. Treat those pins as age/compatibility evidence, not as a safe
modern environment recipe. Select versions from the current interpreter,
accelerator, exporter, and deployment-runtime constraints, then run the package
manager's consistency check.

## Device and Resource Safety

A source workflow may mask visible devices or choose CUDA whenever available.
Do not inherit that behavior blindly:

- let the caller select the device;
- inspect free memory before allocating a GPU;
- begin with one bounded forward, not 1100 track calls;
- avoid running performance loops on shared accelerators without approval;
- synchronize CUDA timing and release resources after a failed probe;
- report CPU results as CPU results, not as evidence for CUDA or mobile.

## Unrelated Evaluation Extension Failures

Exporting the backbone/head and checking ONNX do not require the dataset metric
extension used by some evaluation workflows. A prebuilt native extension is
interpreter/ABI-specific; an import failure there does not diagnose ONNX export,
and its presence does not prove evaluation readiness. Route metric-extension
build and dataset evaluation issues to the `evaluation` sub-skill.

## Artifact Recovery

If export or simplification fails:

1. keep the previous validated artifacts untouched;
2. retain the failing candidate only in a caller-approved diagnostic staging
   area;
3. record command arguments, versions, shapes, and the first meaningful error;
4. fix the earliest failed gate and write to a new candidate name;
5. rerun structure and numerical checks before promotion.

Never treat a nonempty `.onnx` file, a successful conversion-site upload, or a
runtime session constructor as sufficient proof of correct tracking behavior.
