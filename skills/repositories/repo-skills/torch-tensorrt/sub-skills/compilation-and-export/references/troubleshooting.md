# Compilation Troubleshooting

## Fast failure classification

| Failure point | Likely owner | What to do |
| --- | --- | --- |
| Import fails | Environment/package | Use root install and feature-gate guidance. |
| PyTorch export fails | Model/export constraints | Simplify model, adjust `torch.export` dynamic shapes, or use `torch_tensorrt.dynamo.trace`. |
| Partitioning finds little/no TRT coverage | Unsupported ops or too-large `min_block_size` | Use dryrun, lower `min_block_size` cautiously, allow fallback, or route to custom converter guidance. |
| TensorRT engine build fails | TensorRT unsupported layer/dtype/shape or memory | Try FP32, narrower shapes, smaller model segment, `pass_through_build_failures=False` for diagnosis, or inspect engine logs. |
| Output mismatch | Precision, fallback, dynamic shape, or model state | Compare eager/compiled under `eval()` and `inference_mode()`, check dtype/tolerance, and reduce to a smaller repro. |
| Compile succeeds but save/load fails | Artifact/runtime mismatch | Read serialization reference and deployment matrix. |

## Graph breaks in `torch.compile`

If first-call compilation repeatedly recompiles or falls back:

1. Reproduce with `torch._dynamo.explain` or a smaller model block when appropriate.
2. Prefer explicit `torch.export.export` if dynamic shape or graph-break behavior needs to be controlled.
3. Keep `dynamic=False` unless the user knows PyTorch dynamic-shape behavior is required for the `torch.compile` route.
4. If the problem is unsupported TensorRT conversion rather than graph capture, switch to dryrun/debugger.

## Unsupported operators

Symptoms include messages like "no converter", "unsupported op", "requires full compilation", or an unexpectedly tiny TensorRT partition.

Decision tree:

1. If fallback is acceptable, keep the op in PyTorch with `torch_executed_ops` or allow partition fallback.
2. If fallback overhead is too high, try a model rewrite or decomposition that expresses the op with supported ATen ops.
3. If full TensorRT coverage is mandatory, use `require_full_compilation=True` to make failures explicit.
4. If this is a recurring production op, route to the extensibility/debugging sub-skill for converter/plugin/QDP choices.

## Dynamic shape failures

Check:

- Every dynamic dimension has `min <= opt <= max`.
- The PyTorch export dynamic shape constraints include the same dimensions the TensorRT `Input` objects claim are dynamic.
- Multiple inputs sharing batch/sequence dimensions use consistent names and ranges.
- The failing runtime shape is inside every profile.
- The `opt_shape` is not outside expected production shape ranges.

## Precision and dtype failures

- Start with FP32 for debugging; move to FP16 or lower precision only after a passing baseline.
- INT8/FP8/FP4 workflows require ModelOpt/calibration or model-specific quantization steps; missing ModelOpt warnings are expected when the extra is absent.
- DLA supports only FP16/INT8 and is only meaningful on hardware with DLA.
- Do not pass integer token inputs as FP tensors just to make compilation succeed; preserve model input semantics.

## Memory and timeout failures during compile

- Reduce max dynamic shapes, workspace, batch size, or model segment size.
- Compile on an idle GPU; engine build can be memory-intensive.
- Avoid running broad test suites or benchmarks as a compile smoke.
- Use timing caches and engine caches once correctness is established.

## When to escalate

Escalate to another sub-skill when:

  - The requested fix is a custom converter, plugin, QDP kernel, dryrun report interpretation, or issue repro: `../../extensibility-and-debugging/SKILL.md`.
  - The problem happens only after compile during runtime performance, caches, CUDA Graphs, output allocation, or refit: `../../runtime-optimization/SKILL.md`.
  - The problem is artifact loading in Triton, C++, AOTI, ExecuTorch, Windows, Jetson/DLA, or distributed inference: `../../deployment-and-distributed/SKILL.md`.
  - The problem is building the package from source or running repository tests: `../../build-and-maintenance/SKILL.md`.
