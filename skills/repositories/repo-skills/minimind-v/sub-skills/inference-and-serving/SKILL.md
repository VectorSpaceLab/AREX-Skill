---
name: inference-and-serving
description: "Operates MiniMind-V image-question-answering inference and
  optional Gradio WebUI serving with native PyTorch or Transformers-format
  checkpoints."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Inference and Serving

Use this sub-skill when the user wants to run, dry-run, diagnose, or plan MiniMind-V command-line image QA inference or the optional Gradio WebUI.

## Route here

- Image QA with native PyTorch `.pth` checkpoints.
- Image QA with a Transformers-format MiniMind-V checkpoint directory.
- Preflight checks for checkpoint mode, weight filenames, image directories, device choice, and SigLIP2.
- Optional Gradio WebUI model directory scanning, model selection, and safe serving decisions.

## Route elsewhere

- Prerequisites, dependency installation, resource downloads, and dataset acquisition: `data-and-resources`.
- VLM internals or visual projection details: `model-architecture-and-api`.
- Converting native weights to Transformers format: `model-export-and-format-conversion`.
- Pretraining, SFT, resume, DDP, or any training workflow: `training`.

## Guardrails

- Do not launch generation, download resources, train, or start a server as a default inspection step.
- Start WebUI only when the user explicitly asks and accepts listener/device implications.
- Ask before executing untrusted `trust_remote_code=True` loads.

## Fast path

1. Identify checkpoint mode:
   - Native mode uses a `--load_from` value containing `model` and expects `save_dir/weight_hidden_size[_moe].pth`.
   - Transformers mode uses a path that does not contain `model` and loads with `AutoModelForCausalLM.from_pretrained(..., trust_remote_code=True)`.
2. Confirm SigLIP2 at `model/siglip2-base-p32-256-ve` and an image directory.
3. Run [`minimind_vlm_inference_check.py`](scripts/minimind_vlm_inference_check.py) before expensive generation.
4. Run [`scan_transformers_models.py`](scripts/scan_transformers_models.py) before WebUI launch.
5. Read [inference workflows](references/inference-workflows.md), [WebUI serving](references/webui-serving.md), and [troubleshooting](references/troubleshooting.md) for details.

## Key facts

- Native checkpoint path is `save_dir/weight_hidden_size[_moe].pth`, for example `out/sft_vlm_768.pth` or `out/sft_vlm_768_moe.pth`.
- Transformers inference still needs the local SigLIP2 vision encoder for images.
- The WebUI scans immediate child directories for `.bin`, `.safetensors`, or `model.safetensors.index.json`.
