# AIMET backend compatibility and verification

Use this reference to decide whether CPU, CUDA, or ONNX Runtime provider checks are required for a task.

## Baseline requirements

- Python: `>=3.10`.
- OS/platform in docs: x86-compatible Ubuntu 22.04+ or Windows 10/11; source builds also depend on CMake and compiler/toolchain availability.
- PyTorch package: required for `aimet_torch` and also useful for exporting small ONNX smoke models.
- ONNX Runtime: required for `aimet_onnx`; `onnxruntime-gpu` is required only for CUDAExecutionProvider.

## Backend expectation matrix

| Workflow | Backend requirement | CPU substitute | Notes |
| --- | --- | --- | --- |
| Import `aimet_torch`/`aimet_onnx` and inspect API signatures | CPU | full | Use `python -m pip check` plus `scripts/quick_smoke.py`. |
| Torch QuantSim calibration on small models | CPU | full for API behavior | CUDA may be needed for the user's real model size or device-specific tensors. |
| ONNX QuantSim calibration/export on small models | CPU | full for API behavior | CUDA provider behavior must be verified separately with `onnxruntime-gpu`. |
| CUDA-marked native tests or ONNX CPU/GPU encoding comparisons | CUDA | none for GPU semantics | Verify `torch.cuda.is_available()` or ONNX Runtime CUDA provider before running. |
| Source CUDA build | CUDA toolkit and usually `nvcc` | partial | A CPU editable install does not prove CUDA buildability. |
| Analysis/visualization | CPU | full for most static outputs | Visualization dependencies must be version-compatible. |
| Compression examples | CPU for small fixtures, CUDA optional | partial for performance | Real examples can require large datasets and long evaluation loops. |
| On-target inference | external target SDK/device | none | AIMET only produces model/encoding artifacts; target execution must be separately available. |
| GenAILab local LLM/VLM scorecards | model-dependent CUDA/GPU memory, Hugging Face/dataset access, and installed GenAILab deps | partial only for config preflight | Static YAML preflight is CPU-safe, but real model loading/evaluation can download assets and require large GPUs. |
| GenAILab online scorecards | GitHub Actions credentials, pushed branch/ref, CI secrets, and runner capacity | none for online semantics | `--online` uses remote workflow state and ignores uncommitted local changes. |
| Cluster/Pod workflows | Argo/Kubernetes auth, namespace permissions, pod image, remote quota | none for remote-state semantics | Preflight can check tools/auth locally; launch/stop mutate cluster state. |
| Qualcomm AI Hub / QAIRT / QNN deployment | AI Hub credentials or local QAIRT/QNN SDK/device libraries | none for target semantics | Export inspection is local; compile/profile/inference proof comes only from target tooling. |

## Practical checks

Torch CUDA check:

```bash
python - <<'PY'
import torch
print(torch.__version__, torch.version.cuda)
print(torch.cuda.is_available(), torch.cuda.device_count())
if torch.cuda.is_available():
    print(torch.cuda.get_device_name(0), torch.cuda.get_device_capability(0))
    torch.empty((1,), device="cuda")
PY
```

ONNX Runtime provider check:

```bash
python - <<'PY'
import onnxruntime as ort
print(ort.__version__)
print(ort.get_available_providers())
PY
```

GenAILab static config check:

```bash
python scripts/genai_config_preflight.py config.yaml --framework torch --print-command
```

Cluster/Pod preflight:

```bash
scripts/cluster_pod_helper.sh preflight --namespace aihub
```

Qualcomm target dry-runs:

```bash
python scripts/qairt_command_builder.py <export-dir>
python scripts/qai_hub_qnn_job.py --dry-run --qdq-model model_qdq.onnx --device "<device>"
```

If the task is only about package APIs or tiny smoke behavior, CPU checks are sufficient. If the task claims CUDA correctness, provider parity, source CUDA buildability, GenAILab benchmark results, cluster execution, credentialed model access, or device deployment, require backend- or service-specific evidence.
