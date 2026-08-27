# Extensibility and Debugging Troubleshooting

## Error text to map quickly

| Error or symptom | Most likely meaning | Next action |
| --- | --- | --- |
| `Converter for ... requested, but no such converter was found` | Unsupported-op converter gap | Check schema, decide fallback vs rewrite vs custom converter. |
| `Unable to convert node` | A specific op or lowering path failed | Capture the exact op, shapes, and dtypes; run dryrun/debugger. |
| `Failed to create execution context` after save/load | Runtime/cache/context mismatch or unsupported runtime path | Reproduce with a tiny static-shape artifact and simplify runtime settings. |
| Quantization/import warnings about `modelopt` | Optional quantization dependency missing | Install ModelOpt only if the quantization workflow is required. |
| QDP kernel import/runtime issues | Kernel package or capability gate missing | Verify `torch_tensorrt.kernels` APIs, CUDA Python/core deps, and installed TensorRT flavor. |

## Debugging sequence

1. Record package versions and `ENABLED_FEATURES`.
2. Capture a minimal failing input and the exact op/schema.
3. Run dryrun or a debugger capture.
4. Determine whether the problem is coverage, runtime, or deployment.
5. Escalate to the smallest fix that matches the root cause.

## Missing dependency triage

- **ModelOpt absent**: expected for non-quantization workflows; only install when quantization is explicitly needed.
- **CUDA Python/Core absent**: may block QDP/custom-kernel paths even if normal compilation works.
- **TensorRT-RTX unavailable**: runtime settings and caches from RTX docs do not apply.
- **Standard TensorRT plugin package unavailable**: custom kernel/plugin paths may be disabled.

## Good debugging artifacts

A future agent should be able to use the following without reopening the original source checkout:

- a tiny Python script or notebook cell,
- the op schema and shapes,
- a dryrun/debugger summary,
- the exact compile settings,
- the smallest observed failure message,
- a note about whether fallback was accepted.
