# Web UI Runtime Troubleshooting

## Installer and dependency problems

| Symptom | Likely cause | Recovery |
|---|---|---|
| Installer asks which GPU to use | No `GPU_CHOICE` environment variable and interactive one-click flow. | Ask the user to choose CPU/NVIDIA/AMD/Apple/Intel. Use CPU for minimal checks. |
| Conda base environment warning or refusal | Installer expects a dedicated environment. | Create a clean environment instead of mutating base. |
| `ModuleNotFoundError: markdown` during server import | Web UI docs/render dependency missing. | Install `markdown` as part of the web UI dependency group. |
| `ModuleNotFoundError: numba` from cache utilities | Web UI cache utility dependency missing. | Install `numba==0.59.*` with `numpy==1.26.*` for the checked stack. |
| Torch/NumPy ABI warning | Incompatible NumPy 2.x with older torch. | Use `numpy==1.26.*` for the repo-tested stack or update torch and NumPy together. |

## Backend and hardware problems

| Symptom | Likely cause | Recovery |
|---|---|---|
| GPU is present but the UI uses CPU | `--cpu` flag or CPU torch wheel. | Remove CPU flag only after installing and verifying the correct GPU torch build. |
| AMD/Apple/Intel install fails on unsupported platform | Wrong vendor path for host OS/hardware. | Re-select backend; do not force unrelated wheels. |
| CUDA wheel installs but `torch.cuda.is_available()` is false | Driver/toolkit/wheel mismatch. | Check driver and torch CUDA tag; create a new env with a compatible wheel rather than repeatedly mutating the same env. |

## Model download problems

| Symptom | Likely cause | Recovery |
|---|---|---|
| Invalid branch error | Branch contains unsupported characters. | Use branch names with only letters, digits, dot, underscore, or dash. |
| Download selects too many files | Missing specific file or model has multiple weight formats. | Preview the plan, then pass a specific file or use the helper's safetensors preference. |
| Checksum failure | Partial or corrupt download. | Re-run with clean download after confirming disk/network stability. |
| Authentication required | Gated/private HF repo. | Ask the user for a token or local model files; do not invent credentials. |

## Launch and UI problems

| Symptom | Likely cause | Recovery |
|---|---|---|
| Browser opens but no model loads | `autoload_model` false, no selected model, or missing local model files. | Select/download the model first; use the encrypted-distilbert validator for local classifier assets. |
| Remote Llama response never arrives | Nesa stream endpoint/network unavailable. | Use backend request preview first; then test network only if user requests live remote inference. |
| Public URL or LAN exposure appears unexpectedly | `--share`, `--listen`, or broad server name. | Stop and add authentication or bind only localhost. |
| Prompt output is garbled | Wrong mode or prompt template. | Validate `mode: equivariant-encrypt` and inspect `equivariant-encrypt_command`. |
