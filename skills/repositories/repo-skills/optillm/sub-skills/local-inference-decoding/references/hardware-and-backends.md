# Hardware and Backend Reference

Read this before claiming local inference backend support.

## Backend hierarchy

- **CPU:** works for imports and small model tests if dependencies are installed, but may be slow.
- **CUDA:** used when PyTorch sees NVIDIA GPUs and a compatible CUDA wheel/driver stack.
- **MPS:** PyTorch backend for Apple Silicon macOS.
- **MLX:** Apple Silicon MLX runtime used by MLX-specific code paths.

A visible GPU does not guarantee every model or quantization path works. Always probe framework availability before loading a large model.

## Safe backend probe

```bash
python scripts/check_local_backend.py --json
```

This helper imports framework packages and reports CUDA/MPS/MLX availability without downloading models.

## CUDA checks

A meaningful CUDA smoke check includes:

```python
import torch
print(torch.__version__, torch.version.cuda)
print(torch.cuda.is_available(), torch.cuda.device_count())
if torch.cuda.is_available():
    print(torch.cuda.get_device_name(0), torch.cuda.get_device_capability(0))
    torch.empty((1,), device="cuda")
```

If `torch.cuda.is_available()` is false on a GPU host, suspect CPU-only torch, missing driver passthrough, incompatible driver/wheel, or container GPU restrictions.

## MLX/MPS notes

- `thinkdeeper_mlx` and `MLXInferencePipeline` are for Apple Silicon/macOS.
- Linux CUDA hosts should not be used to verify MLX-specific claims.
- PyTorch MPS and MLX are separate backends; importing one does not prove the other.

## Optional dependency surfaces

| Feature | Dependencies/conditions |
| --- | --- |
| LoRA/adapters | `peft`, base model and adapter compatibility |
| Quantization | `bitsandbytes`, compatible CUDA/CPU support |
| Transformers local inference | `torch`, `transformers`, model cache/access |
| Outlines JSON model path | `outlines`, `transformers`, local model download/cache |
| AutoThink | classifier model, steering vector dataset, compatible target layer |
| DeepConf | local logits/probability access |

## Cache and token handling

- Private HuggingFace models need a valid non-empty token.
- Blank HuggingFace token env vars are removed by package import cleanup, so anonymous access is used instead of an illegal empty header.
- Model downloads can be large; ask before triggering them in constrained environments.
- Use `OPTILLM_MAX_TOKENS` or request `max_tokens` to bound small-model smoke tests.

## Readiness language

Use precise backend claims:

- "Import/backend probe passed" means dependencies import and device APIs respond.
- "Model smoke passed" means a specific model loaded and generated.
- "CUDA verified" requires a device operation, not just `import torch`.
- "MLX verified" requires Apple Silicon MLX import/generation evidence.
