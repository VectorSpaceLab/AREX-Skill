# Troubleshooting

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| `torch.cuda.is_available()` is false, or you see a CPU-only wheel error | The environment has no CUDA-capable torch build | Install a CUDA-enabled torch wheel such as `torch==2.7.0+cu126` and run on an NVIDIA GPU host. ICEdit inference is GPU-first; a CPU-only wheel is not a supported substitute. |
| `CUDA out of memory` | The edit is too large for the current VRAM budget | Re-run with `--enable-model-cpu-offload`, close other GPU jobs, or use a smaller-height source image. The README notes that a 512×768 edit can need about 35 GB without offload. |
| Model download, auth, or network failures | Default Hub weights are unavailable, or a supplied local checkpoint/LoRA path is missing | Log in to Hugging Face or provide existing `--flux-path` and `--lora-path` filesystem paths. The helper does not bundle or synthesize weights. |
| MoE mode cannot find the vendored package | The checkout root does not contain `icedit/` | Pass `--repo-root /path/to/ICEdit-checkout` or set `ICEDIT_REPO_ROOT`. If you do not have that tree, use `--mode normal` and the normal LoRA path. |
| The helper resized my image | The input width was not 512 | This is expected. The helper always normalizes width automatically, and there is no separate width flag. |
| The edit changed too much or missed the target | Seed sensitivity | Try a different `--seed`. The README explicitly recommends retrying with another seed when the first result is not good enough. |

## Preference note

When MoE is hard to load or you just want the standard editing path, prefer `--mode normal` with `RiverZ/normal-lora`.
