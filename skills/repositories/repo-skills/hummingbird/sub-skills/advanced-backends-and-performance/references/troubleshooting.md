# Advanced Backend Troubleshooting

Use this table when Hummingbird advanced-backend requests fail or when the environment is not yet proven. Do not install CUDA, TVM, ONNX, or optional source-model packages blindly; first identify the missing capability and the user's target platform.

## Quick probe

From this sub-skill directory, run:

```bash
python scripts/check_backends.py --json
```

For an explicit CUDA tensor allocation smoke, only when acceptable for the task:

```bash
python scripts/check_backends.py --json --cuda-smoke
```

## Failure and recovery table

| Symptom | Likely cause | Safe response |
| --- | --- | --- |
| `MissingBackend` or backend alias maps to null for `tvm` | TVM is not importable in the active Python environment. | Report that TVM is unavailable. Check Python compatibility before proposing install; Hummingbird's package guidance says TVM only works through Python 3.10. |
| `MissingBackend` for `onnx` | ONNX Runtime support is not importable, even if another ONNX package is present. | Route detailed ONNX dependency and model I/O handling to the ONNX sub-skill. Do not treat `onnx` alone as enough for Hummingbird's ONNX backend. |
| Runtime error says the backend requires test inputs | TorchScript, TVM, and non-ONNX-source ONNX conversion need representative `test_input`; some ONNX-source paths also need explicit input. | Re-run conversion with a small representative array/DataFrame/tuple matching production feature shape and dtype family. |
| TVM prediction fails on a different number of rows | Plain TVM conversion compiled a fixed input shape from `test_input`. | Use `convert_batch(...)` with an appropriate `remainder_size`, recompile for the desired shape, or set `TVM_PAD_INPUT=True` and accept possible performance loss. |
| TVM compilation appears to hang or takes too long | Relay fusion depth or model complexity is too high for the bounded task. | Set `extra_config={constants.TVM_MAX_FUSE_DEPTH: 30}` or a smaller tested value, reduce model size for smoke validation, and avoid benchmark-scale runs without explicit budget. |
| `device="cuda"` fails or `model.to("cuda")` raises a CUDA error | PyTorch is CPU-only, no CUDA device is visible, or the installed CUDA wheel does not match the host. | Use `check_backends.py --json`; if `cuda_available` is false or `torch.version.cuda` is null, explain that a CUDA-capable PyTorch build matching the platform is required. Continue on CPU unless the user authorizes environment changes. |
| User asks for GPU acceleration after only CPU smokes passed | No GPU verification exists. | State the verified limit: CPU only. Offer the CUDA probe or a small CUDA conversion/prediction smoke if hardware and policy allow. |
| TVM requested on Python newer than the supported TVM build | TVM wheels/builds may not support that Python version; Hummingbird documents TVM as working through Python 3.10. | Do not attempt a blind install. Ask whether to create/use a Python 3.10-compatible environment or fall back to TorchScript/ONNX. |
| `Device ... not recognized` for TVM | TVM conversion accepts `cpu`, `cuda`, or LLVM target strings. | Use `device="cpu"`, `device="cuda"` only after CUDA/TVM-GPU checks, or a valid LLVM target string. |
| Thread settings give inconsistent timings | PyTorch thread settings are process-global and Hummingbird sets inter-op threads to 1. | Run measurements in a fresh process, set `N_THREADS` once during conversion, and report the thread count with timing results. |
| User asks to run full benchmarks for quick validation | Hummingbird benchmark suites are paper-scale and can take days. | Decline routine benchmark execution for smoke validation; propose a tiny parity/timing check unless the user budgets benchmark datasets and runtime. |

## CUDA-specific notes

- Hummingbird can move PyTorch-family output to CUDA with `device="cuda"` during conversion or with `hb_model.to("cuda")` afterward.
- A CUDA-capable NVIDIA driver and a CUDA-enabled PyTorch wheel are both required for actual GPU execution.
- `torch.cuda.is_available() == False` is enough to mark GPU execution unverified/unavailable for the current environment.
- Do not infer GPU support from the presence of a GPU in the machine if the active Python environment has CPU-only PyTorch.

## TVM-specific notes

- TVM backend support appears in Hummingbird only when TVM imports successfully.
- `test_input` is part of the TVM compiled shape contract.
- `TVM_PAD_INPUT=True` increases shape flexibility by padding but may hurt performance.
- `TVM_MAX_FUSE_DEPTH` exists to bound compilation; the default is 50, and smaller values such as 30 or 10 are used in package tests.

## Routing reminders

- Basic conversion and fitted-model checks belong to the core conversion sub-skill.
- ONNX export, ONNX Runtime session behavior, and model save/load belong to the ONNX and model I/O sub-skill.
- Optional source model dependencies such as LightGBM, XGBoost, SparkML, and Prophet belong to the optional source models sub-skill.
