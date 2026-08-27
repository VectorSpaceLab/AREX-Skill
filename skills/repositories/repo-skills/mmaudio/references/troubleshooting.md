# Cross-Cutting Troubleshooting

Read this when an MMAudio task fails before it reaches a specific workflow, or
when install/backend/model/download/media issues affect several routes.

## Install and import failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: mmaudio` | Package not installed in the active environment. | Install from a checkout with `python -m pip install -e <MMAudio checkout>`, then run `scripts/check_mmaudio_env.py`. |
| `ModuleNotFoundError` for `hydra`, `open_clip`, `av`, `tensordict`, `torchdiffeq`, `gradio`, or `nitrous_ema` | Editable install skipped dependencies or the wrong environment is active. | Reinstall the package with dependencies, not `--no-deps`, or install the missing package explicitly. |
| `ModuleNotFoundError: av_bench` | Training/evaluation metric support depends on the separate av-benchmark project; it is not in the package metadata. | Install av-benchmark when training final sampling or project metrics are in scope, or avoid those routes and use inference-only workflows. |
| `File "setup.py" not found` during install | Older pip expected legacy setup metadata. | Upgrade pip inside the target environment, then install from `pyproject.toml` with `python -m pip install -e <checkout>`. |

## CUDA and backend failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| CUDA workflows fail but `import torch` works | CPU-only or incompatible PyTorch wheel, missing driver access, or wrong environment. | Run `scripts/check_mmaudio_env.py --require-cuda`; reinstall PyTorch/torchaudio/torchvision for a CUDA version supported by the driver. |
| NCCL/distributed errors at startup | Training/evaluation/extraction launched without `torchrun`, bad rendezvous env, or too many ranks for visible GPUs. | Use `torchrun --standalone --nproc_per_node=<gpu_count>` for one-node jobs; reduce process count while debugging. |
| OOM during inference/evaluation | Model too large, high batch size, `compile=True`, too many workers, long duration, or expensive video preprocessing. | Reduce batch size, use a smaller variant, disable compile for debugging, keep duration near 8 seconds, and use audio-only output when possible. |
| CPU fallback is extremely slow | Demo CLI can fall back to CPU, but MMAudio models are large. | Treat CPU as import/parser-only unless the user explicitly accepts slow generation. Prefer CUDA or MPS. |

## Model and download failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ValueError: No link found for ...` | Unknown or renamed checkpoint filename passed to the downloader. | Use the exact filenames in `references/model-assets.md`. |
| Repeated checkpoint downloads | File missing or MD5 mismatch. | Check disk space, partial downloads, permissions, and whether the path points to the intended `weights/` or `ext_weights/` directory. |
| Hugging Face rate-limit or unauthenticated warning | Downloading CLIP/model assets without a token or with limited network. | Authenticate or pre-stage weights when allowed; otherwise stop before triggering downloads. |
| 16 kHz model decodes incorrectly or vocoder missing | `best_netG.pt` is absent for the 16 kHz path. | Populate `ext_weights/best_netG.pt` or switch to a 44.1 kHz model if appropriate. |

## Media and data failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Video is reported too short or wrong length | The requested duration needs more CLIP/Synchformer frames than the source provides. | Lower duration or use a longer input; remember CLIP uses 8 FPS and Synchformer uses 25 FPS. |
| Video decode fails or is very slow | PyAV/torchaudio backend issue, unsupported codec, or high-resolution input causing decode/encode overhead. | Re-encode to a common H.264/AAC MP4, keep practical resolution, and skip video compositing when only audio is needed. |
| Training data shape assertion fails | Memmap sequence lengths or feature dimensions do not match the selected model mode. | Read the data-preparation sub-skill and regenerate features for the selected 16k/44k mode. |
| Empty batch/evaluation output | Dataset metadata paths, filename stems, split labels, or JSONL prompts do not match media files. | Use the evaluation data-format reference and command builder `--check-paths` mode before launching CUDA work. |

## Route-specific next steps

- Inference CLI/API failures: [`../sub-skills/inference/references/troubleshooting.md`](../sub-skills/inference/references/troubleshooting.md).
- Feature extraction and memmap failures: [`../sub-skills/data-preparation/references/troubleshooting.md`](../sub-skills/data-preparation/references/troubleshooting.md).
- Training/DDP/checkpoint failures: [`../sub-skills/training/references/troubleshooting.md`](../sub-skills/training/references/troubleshooting.md).
- Batch evaluation/onset failures: [`../sub-skills/evaluation/references/troubleshooting.md`](../sub-skills/evaluation/references/troubleshooting.md).
