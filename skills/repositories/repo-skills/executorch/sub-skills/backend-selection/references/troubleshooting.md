# Backend Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Backend Python import fails | Optional dependency or source-layout module missing | Run `scripts/check_backend_imports.py`; install only the dependency for the selected backend. |
| Export succeeds but no nodes delegate | Unsupported ops/dtypes/layout or wrong partitioner | Start from a tiny supported model; enable verbose partitioner logs if available; compare with backend support matrix. |
| Delegated model fails on device | Runtime built without matching backend library or SDK mismatch | Verify CMake flags, linked libraries, SDK version, and target device ABI. |
| CPU fallback hides performance issue | Unsupported delegate partitions fall back silently | Inspect partition results and profile runtime; make fallback intentional. |
| Backend quantized model inaccurate | Calibration or quantizer config mismatch | Evaluate quantized PyTorch before lowering; use backend-specific quantization recipe. |
| SDK/toolchain path missing | Vendor runtime not installed or not licensed | Stop and ask for SDK/device path or user approval; do not download/accept SDKs silently. |

