# MiniMind-V Cross-Cutting Troubleshooting

## Purpose

Use this reference when a failure spans multiple MiniMind-V workflows or when the correct sub-skill is not obvious. Prefer the nearest sub-skill troubleshooting file once the owner is clear.

## Quick route table

| Symptom | Likely owner |
| --- | --- |
| Missing `model/tokenizer.json`, SigLIP2 files, parquet columns, unreadable image bytes | `data-and-resources` |
| `processor is None`, placeholder mismatch, `pixel_values` shape errors, MoE key mismatch | `model-architecture-and-api` |
| `eval_vlm.py` cannot find weight file, wrong native/Transformers mode, WebUI scanner finds no models | `inference-and-serving` |
| Missing training parquet/base weights, CUDA OOM, DDP rank issues, resume mismatch, logging failures | `training` |
| Export lacks tokenizer/config/weights, `strict=False` key surprises, Transformers 5 metadata issues | `model-export-and-format-conversion` |

## Missing or misplaced resources

Symptoms:

- A script cannot find `model/siglip2-base-p32-256-ve/`.
- Native inference/training cannot find `out/llm_768.pth`, `out/sft_vlm_768.pth`, or `_moe` variants.
- Training cannot find `dataset/sft_i2t.parquet` or `dataset/pretrain_i2t.parquet`.
- A Transformers export loads text-only but fails for image prompts.

Likely causes:

- Required resources were not downloaded or were placed under a different relative path.
- Dense/MoE filename convention does not match `--use_moe` or `VLMConfig(use_moe=...)`.
- The conversion/export deleted or did not package the frozen SigLIP2 encoder.

Recovery:

1. Use the repo-level environment helper to identify missing relative paths.
2. Route resource acquisition to `data-and-resources` and ask before downloading large model/data artifacts.
3. Route run/serve actions to `inference-and-serving` only after resources are present.
4. Route export packaging questions to `model-export-and-format-conversion` if the issue is an incomplete Transformers directory.

## Torch/backend mismatch

Symptoms:

- `torch.cuda.is_available()` is false on a CUDA machine.
- Importing torch fails after installing requirements.
- CUDA OOM occurs during inference or training.
- CPU inference is extremely slow.

Likely causes:

- `torch`/`torchvision` are not pinned active requirements and were installed with the wrong backend wheel.
- The selected workflow requires GPU memory beyond the available budget.
- Training defaults are GPU-oriented and use CUDA autocast/DDP when CUDA is selected.

Recovery:

- Treat torch backend setup as separate from `requirements.txt`; select CPU/CUDA/ROCm/MPS wheels for the host.
- For inference diagnosis, lower `--max_new_tokens`, use fewer/lower-resolution images, or start with CPU only for file-path checks.
- For training, lower batch size or accumulation settings and ask before launching expensive runs.
- Do not treat CPU import success as full validation of CUDA training or GPU generation.

## Trusting custom code

MiniMind-V Transformers-format checkpoints rely on custom model code. Loading through Transformers commonly uses `trust_remote_code=True`.

Safe handling:

- Use static export inspection before executing custom code.
- Ask the user whether they trust the checkpoint/code source before running `AutoModelForCausalLM.from_pretrained(..., trust_remote_code=True)`.
- Keep local untrusted exports out of long-lived serving workflows until inspected.

## Network and large artifacts

MiniMind-V workflows may need external resources: SigLIP2 vision encoder, native model weights, Transformers exports, and ALLaVA-style parquet datasets. These can be large and may require ModelScope/HuggingFace/git-lfs access.

Rules:

- Do not download as a default diagnostic.
- Ask for approval, network source, target relative path, and storage budget.
- If a task only needs command planning or static validation, use bundled helpers instead of downloading.

## Long-running or stateful actions

Do not start these without explicit user approval:

- Pretrain or SFT loops.
- DDP `torchrun` jobs.
- WebUI/Gradio server launch.
- Full model conversion when it loads large checkpoints.
- Full image generation over many images.

Prefer preflight checks, command builders, and static inspectors first.
