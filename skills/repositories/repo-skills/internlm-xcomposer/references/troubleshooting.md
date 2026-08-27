# Cross-cutting Troubleshooting

## When to read

Read this when a workflow fails before it reaches a sub-skill-specific issue. For deeper workflow fixes, open the owning sub-skill troubleshooting file.

## Install and import failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: transformers`, `timm`, `sentencepiece`, `einops` | Base inference dependencies not installed in the selected environment | Install only the profile from `references/installation.md` that matches the selected workflow, then rerun `scripts/check_environment.py --modules torch,transformers`. |
| `trust_remote_code` warning or refusal | XComposer model APIs are implemented in trusted remote/local model code | Use only trusted InternLM/HF/ModelScope IDs or local checkpoints. Keep `trust_remote_code=True` in examples that call XComposer-specific methods. |
| `torch.cuda.is_available() == False` while a GPU is expected | CPU-only torch wheel, driver/runtime mismatch, container lacks GPU passthrough, or wrong environment | Check `nvidia-smi`, install a CUDA torch wheel compatible with the driver, then run a tiny CUDA allocation before loading the model. |
| `flash_attn` build/import errors | ABI mismatch with torch/CUDA/Python or missing `nvcc` for source builds | Treat `flash-attn` as workflow-specific; install after torch and use `--no-build-isolation` only with matching toolchain evidence. |
| `lmdeploy` import/runtime error | LMDeploy wheel does not match CUDA/runtime; docs default to CUDA 12.x | Reinstall LMDeploy for the actual CUDA version or use Transformers inference instead. |

## Model and checkpoint failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| 404 or authorization error for model download | Wrong model ID, private/gated model, missing license acceptance, or offline environment | Verify the exact model family in `references/overview.md`; use a local checkpoint path if downloads are not allowed. |
| `AttributeError: chat`, `write_webpage`, or reward `rank` missing | Loaded a generic model class or wrong checkpoint | Use the documented InternLM-XComposer model ID with `trust_remote_code=True`; verify that the checkpoint belongs to the requested sub-skill. |
| Out of memory during inference | 7B/4K/high-context workload exceeds VRAM or `hd_num`/context too high | Use LMDeploy/AWQ, multi-GPU dispatch, reduce `hd_num`, reduce `max_new_tokens`/context, or select a smaller/quantized checkpoint. |
| Bad multi-image response or warning about image count | Prompt `<ImageHere>` placeholders do not match the image list | For multiple images, put one placeholder per image and keep list order explicit; for single image, some models auto-prepend the placeholder if absent. |

## Data and benchmark blockers

- Fine-tuning data must be JSON lists and `data.txt` manifests must have one path plus sample amount per line. Run the finetuning or reward validators before `torchrun`.
- Reward data uses `conversations_a` and `conversations_b` for chosen/rejected responses; ordinary SFT `conversations` data is not enough.
- Benchmark workflows often need licensed datasets, official eval tools, leaderboard accounts, or GPT/OpenAI judge keys. The skill can plan these workflows but should not download or submit without explicit approval.
- Notebooks and scripts in old evaluation directories are evidence for command shape and output expectations; treat them as heavyweight unless the dataset/model/cache and GPU budget are already available.

## Service and deployment blockers

- Gradio/OmniLive ports may conflict with existing services; choose ports and bind addresses deliberately.
- OmniLive SRS setup needs a LAN-reachable `CANDIDATE` IP, not `127.0.0.1`.
- A remote OmniLive backend needs frontend-visible URLs, firewall access, and consistent HTTP/WebSocket/SRS hostnames.
- Node/npm frontend installs can download many packages; do not run `npm install` in a restricted environment without approval.

## When to stop

Stop and ask for explicit execution approval when a command would download model weights or benchmark data, call an external judge/submission server, start a public listener, mutate a shared environment, launch long training/evaluation, or require credentials.
