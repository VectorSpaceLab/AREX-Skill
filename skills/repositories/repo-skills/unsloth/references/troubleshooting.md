# Cross-Cutting Troubleshooting

Use this reference for failures that can affect more than one Unsloth interface. For workflow-specific details, read the nearest sub-skill troubleshooting reference.

## Import And Dependency Failures

| Symptom | Likely cause | Next action |
| --- | --- | --- |
| `No module named 'torch'` during `import unsloth` | Core GPU path needs PyTorch | Install a backend-compatible torch build for the user's OS/GPU/Python, then rerun a safe import check. |
| `Please install unsloth_zoo` | Required companion package missing or too old | Install/upgrade `unsloth_zoo` in the same environment as `unsloth`. |
| `No module named 'bitsandbytes'` or 4-bit load fails | QLoRA/4-bit workflow without bitsandbytes | Install a compatible `bitsandbytes` wheel or switch to 16-bit/full-finetuning workflow. |
| Import-order warning for `trl`, `transformers`, `peft` | Those libraries were imported before Unsloth | Move `import unsloth` before those imports in training scripts. |
| `pip check` reports dependency conflicts | Mixed package manager or partial optional-extra install | Fix the package set before trusting signatures, CLI help, or training behavior. |

## Backend And Hardware Failures

- CUDA `ldconfig` warnings mean Unsloth detected CUDA library linking problems. Verify the PyTorch CUDA smoke test, driver/library paths, and `bitsandbytes` / `xformers` info before training.
- If `torch.cuda.is_available()` is false on a GPU host, check container GPU passthrough, CPU-only torch wheels, driver compatibility, and `CUDA_VISIBLE_DEVICES`.
- Do not install CUDA extras on AMD/ROCm, Intel/XPU, Apple MLX, or CPU-only hosts unless the user is intentionally changing hardware/backend.
- Studio and Core do not have identical backend requirements. A Studio GGUF chat path may work where Core training does not, and a Core training environment may not include Studio's launcher/runtime state.

## Network, Cache, And Credentials

- Model downloads, gated repos, Hub uploads, provider calls, and Cloudflare tunnels may need network access and credentials. Ask before running them.
- Use environment variables or secure stores for `HF_TOKEN`, `WANDB_API_KEY`, Studio API keys, and provider keys. Do not write secrets into config templates, shell history snippets, or generated artifacts.
- If Hugging Face cache paths are read-only or stale, verify cache permissions and fallback behavior before retrying downloads.
- For Hub upload/export failures, confirm repo id, token scope, private/public decision, and whether the artifact is complete locally.

## Routing Mistakes

- Python loader/trainer/data errors belong in `sub-skills/core-training/references/troubleshooting.md`.
- `unsloth train`, `unsloth run`, `unsloth connect`, config, aliases, and parser errors belong in `sub-skills/cli-workflows/references/troubleshooting.md`.
- Checkpoint, tokenizer, GGUF, Ollama, path, and Hub export errors belong in `sub-skills/model-export/references/troubleshooting.md`.
- Studio setup, server startup, secure tunnel, API key, provider, RAG, llama.cpp, and tool policy errors belong in `sub-skills/studio-runtime/references/troubleshooting.md`.

## Safe Escalation Order

1. Read the relevant sub-skill route and troubleshooting reference.
2. Run a bundled preflight/helper script when available.
3. Check package metadata, `pip check`, CLI help, and non-mutating config validation.
4. Only then run downloads, training, conversion, Studio setup/update, server launch, Hub upload, or provider calls with explicit user approval.
