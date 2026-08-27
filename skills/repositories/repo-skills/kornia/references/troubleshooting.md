# Cross-cutting troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `import kornia` fails | Base dependencies are missing or the active Python is not the intended environment. | Run the root import check, then `scripts/kornia_environment_probe.py --check-optional`. Install `kornia` in the environment that will run the task. |
| Import emits warnings under `-W error` | A dependency or Kornia path emits import-time warnings. | Run the repository import-warning tests when maintaining Kornia; for user code, isolate the import after importing torch and optional runtime dependencies. |
| Tensor results are clipped or numerically wrong | Float image tensors are in `[0,255]` or layout is HWC/BHWC. | Convert to BCHW/CHW and scale floats to `[0,1]` before Kornia image/augmentation APIs. |
| CPU works but CUDA/MPS fails | Backend kernel, dtype, or optional package support differs. | Retry float32 on the backend, run the nearest smoke script on that device, and classify the failure as backend-specific before changing algorithm code. |
| Half precision corrupts later CUDA tests | A low-precision CUDA kernel caused an async device-side assert. | Run half-precision cases in isolated subprocesses or separate invocations; do not mix them with standard dtype suites. |
| Pretrained model or learned matcher attempts network access | A pretrained option requested weights that are not cached locally. | Use a no-download configuration for smoke checks or explicitly authorize/provide weights before running pretrained workflows. |
| ONNX or transpiler import fails | Optional ONNX/Ivy/TensorFlow/JAX dependencies are absent. | Install only the optional dependency stack required by the selected deployment route, or use a PyTorch-only fallback. |
| Geometry output is shifted/flipped | `(h,w)` versus `(w,h)`, matrix direction, `align_corners`, or coordinate-order mismatch. | Read `sub-skills/geometry-vision/references/coordinate-conventions.md` and test with a non-square image. |
| Loss/metric output shape is unexpected | Target encoding, channel dimension, or reduction was misread. | Read `sub-skills/losses-and-metrics/references/target-shapes-and-reductions.md` and assert logits/target shapes before calling the API. |
| Source maintenance PR fails docs or API gates | Public API symbol was not listed in docs or a removal lacked the deprecation window. | Update the relevant docs reference, API inventory, and release notes according to the maintainer workflow. |

## Escalation order

1. Run the root environment probe.
2. Run the nearest sub-skill smoke script on CPU.
3. Re-run on the target accelerator and dtype only if the CPU contract passes.
4. Use focused native tests for the owning module.
5. For source changes, run lint/typecheck/doc or benchmark gates that match the PR lane.
