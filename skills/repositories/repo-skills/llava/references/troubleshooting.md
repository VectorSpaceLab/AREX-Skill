# Cross-Cutting Troubleshooting

## Install/import failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: llava` | Package was not installed in the active Python | Install `llava` in the environment you are using, then run `python scripts/check_install.py`. |
| `torch`, `torchvision`, `transformers`, or `tokenizers` version conflicts | Resolver upgraded or downgraded away from package pins | Reinstall the pinned stack from [`install-and-compatibility.md`](install-and-compatibility.md). Avoid unpinned upgrades unless you are refreshing this skill for a newer repo version. |
| Training imports fail inside `peft` or `accelerate` | New PEFT release incompatible with repo-pinned Accelerate/Transformers | Use a PEFT version compatible with `accelerate==0.21.0` and `transformers==4.37.2`, or refresh the entire package stack intentionally. |
| `pkg_resources` missing while importing PyTorch extension utilities | Very new setuptools removed the legacy import surface used by older PyTorch | Install a setuptools release that still provides `pkg_resources`, then re-run `pip check`. |
| `pip check` reports broken `httpx`/`httpcore` or `torch`/`triton` pins | A repair install pulled transitive dependencies from a newer stack | Restore `httpx==0.24.0` with a compatible `httpcore` and `torch==2.1.2` with `triton==2.1.0`. |

## Backend failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `torch.cuda.is_available()` is false on a GPU host | CPU-only Torch, missing driver passthrough, unsupported driver/wheel, or container lacks GPU access | Check `nvidia-smi`, reinstall CUDA-enabled Torch matching the pinned version, and re-run `scripts/check_install.py --require-cuda`. |
| CUDA out-of-memory while loading a checkpoint | Model too large for visible GPU VRAM or too many workers/processes | Use a smaller checkpoint, 4-bit/8-bit quantization on supported Linux/CUDA, reduce worker concurrency, use multiple GPUs when supported, or free GPU memory. |
| `no kernel image is available` or CUDA extension ABI errors | Wheel or compiled extension does not support the GPU architecture or Torch/CUDA ABI | Use a supported wheel/toolkit pair, avoid optional compiled extensions, or rebuild in a compatible environment. |
| MPS or Windows quantization fails | LLaVA docs only support limited 16-bit inference on macOS/Windows | Use Linux/CUDA for quantization or run macOS with `--device mps` and no 4/8-bit flags. |

## Data, model, and network failures

- Hugging Face model downloads can require network access, disk space, auth for gated base models, and acceptance of base-model terms. Do not treat download failure as a skill failure until credentials/network are checked.
- Dataset and benchmark scripts often assume large external downloads. Use validation scripts before launching inference or training.
- OpenAI/GPT review scripts require credentials and can hit rate limits. If credentials are absent, record the judge step as blocked or optional rather than failing the whole LLaVA workflow.

## What not to claim

- A CPU import check does not prove LLaVA generation, model-worker serving, benchmark inference, or training works.
- CLI `--help` success does not prove a full benchmark or training job can finish.
- A Gradio process can run without any registered model worker; an empty model list means no worker is available, not that the UI is broken.
- Optional SGLang, FlashAttention, xFormers, MPS, Intel, and GPT-review surfaces are separate compatibility claims and need their own evidence.
