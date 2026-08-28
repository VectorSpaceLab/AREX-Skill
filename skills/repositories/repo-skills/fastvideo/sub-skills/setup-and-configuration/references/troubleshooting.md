# Setup troubleshooting

| Symptom | Likely cause | Recovery |
|---|---|---|
| `ModuleNotFoundError` during import | Partial install or optional package absent | Recreate an isolated environment, install the base package, then add only the extra required by the selected route; rerun the diagnostic. |
| CUDA reports unavailable | CPU torch, incompatible driver, container without GPU passthrough, or wrong wheel | Check `torch.version.cuda`, `torch.cuda.is_available()`, `nvidia-smi`, architecture, and driver. Install the documented CUDA wheel; do not call CPU import a CUDA pass. |
| CUDA extension import/ABI error | Extension built for a different torch/CUDA/Python/architecture | Remove the incompatible optional extension only if it is optional, or rebuild/install the matching variant after torch is fixed. Use SDPA as a documented fallback where supported. |
| Config says top-level `generator` is missing | Flat or wrong-shaped JSON/YAML | Add `generator.model_path`; put generation fields under `request`, and use dotted overrides only under allowed prefixes. |
| `unknown field` or invalid literal | Typo, stale config, or unsupported enum | Follow the reported nested path; compare with the typed configuration reference and remove unsupported keys. |
| Model has no preset | ID is not registered, renamed, private, or wrong workload | Verify the exact model ID and family; supply an explicit pipeline/preset only when the model's component layout is known. |
| Out of memory at startup | Model too large, too many GPUs not configured, or offload disabled | Reduce model/resolution, enable supported offload/FSDP, choose a smaller/distilled model, or use more GPUs. |
| Remote download hangs or asks for auth | Network, gated model, or missing Hugging Face credentials | Confirm access and credentials explicitly, retry with a bounded timeout, and preserve the error. Never embed tokens in configs or skill files. |
