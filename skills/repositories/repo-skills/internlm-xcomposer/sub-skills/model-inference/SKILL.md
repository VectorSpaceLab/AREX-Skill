---
name: model-inference
description: "Guide InternLM-XComposer Transformers, LMDeploy/AWQ, multi-GPU,
  Gradio, and composition inference workflows with safe planners and approved
  runnable entrypoints."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Model Inference Sub-skill

Use this sub-skill when a task asks how to run, adapt, audit, or troubleshoot InternLM-XComposer model inference for the 2.5/2.0/1.0 model family: Transformers image/video/multi-image chat, LMDeploy acceleration, 4-bit/AWQ inference, multi-GPU dispatch, Gradio demos, and the documented composition APIs `chat`, `write_webpage`, `resume_2_webpage`, `screen_2_webpage`, `write_artical`, plus legacy `generate`/`chat` APIs.

This sub-skill is intentionally non-executing. It can render safe example scripts and command plans, but it must not import torch, Transformers, LMDeploy, Gradio, load/download checkpoints, open network services, or run CUDA inference unless the user explicitly switches to an execution-oriented Researcher workflow with the required environment and approval.

## Route First

- Use this sub-skill for current InternLM-XComposer2.5 image chat, video understanding, multi-image/multi-turn dialogue, webpage generation, resume/screenshot-to-webpage, article writing, LMDeploy pipelines, AWQ/4-bit choices, multi-GPU dispatch, and Gradio chat/composition launch planning.
- Route OmniLive audio, long streaming video memory, SRS/FastAPI backends, OmniLive model-root layout checks, and OmniLive-specific benchmarks to sibling `omnilive`.
- Route benchmark/dataset/submission workflows to sibling `evaluation-and-projects` unless the user only needs a model-call snippet for evaluation.
- Route supervised fine-tuning, LoRA training, and adapter merge planning to sibling `finetuning`.
- Route IXC-2.5-Reward scoring, ranking, reward training, and reward benchmark inference to sibling `reward-model`.

## Required Inputs To Collect

Before producing a plan or snippet, identify:

1. Model family and backend: current `internlm/internlm-xcomposer2d5-7b`, current `internlm/internlm-xcomposer2d5-7b-4bit`, legacy 2.0/4KHD/VL, legacy 1.0, local path, ModelScope path, Transformers, or LMDeploy.
2. Intended workflow: chat, video understanding, multi-image dialogue, high-resolution image understanding, webpage generation, resume-to-webpage, screenshot-to-webpage, article writing, Gradio UI, LMDeploy offline pipeline, or LMDeploy API server plan.
3. Runtime constraints: CUDA version, GPU count and VRAM, PyTorch/Transformers/Gradio/LMDeploy versions, `flash-attn` availability, network/model-download permission, and whether CPU-only planning is acceptable.
4. Inputs and outputs: image/video/resume paths, prompt text, number of images/placeholders, desired `hd_num`, output HTML/article file location, service host/port/share policy, and whether external image search is allowed for composition demos.

## Operating Procedure

1. Open `references/api-reference.md` to choose the correct model id, loader shape, method signature, image placeholder convention, and legacy compatibility mode.
2. Open `references/workflows.md` for end-to-end Transformers, multi-GPU, high-resolution, video, composition, 4-bit/AWQ, and safe rendered-example workflows.
3. Open `references/gradio-and-serving.md` for Gradio chat/composition launch flags, exposure choices, LMDeploy API-server planning, and service-risk notes.
4. Open `references/troubleshooting.md` when the request mentions CUDA/VRAM/OOM, `trust_remote_code`, placeholder mismatch, `hd_num`, generated HTML files, LMDeploy CUDA versions, Gradio versions, or legacy API errors.
5. Use the bundled stdlib-only renderers when the user wants a starting script or plan without side effects:

```bash
python scripts/render_transformers_example.py --help
python scripts/render_transformers_example.py --task chat --image /data/dubai.png --query "Analyze the image" --num-gpus 1
python scripts/render_transformers_example.py --task multi-image --image cars1.jpg --image cars2.jpg --query "Image1 <ImageHere>; Image2 <ImageHere>; compare them" --num-gpus 2
python scripts/render_lmdeploy_example.py --help
python scripts/render_lmdeploy_example.py --quantization awq --mode offline --image /data/dubai.png
python scripts/render_lmdeploy_example.py --quantization fp16 --mode server --tp 2 --session-len 32768
```

The helpers only render text or write user-editable example files. They do not import heavy ML packages and do not download or run models.

## Bundled runnable Gradio entrypoints

When the user explicitly approves a real Gradio service launch, use the self-contained source-derived bundle under `entrypoints/gradio/` instead of asking for the original checkout:

- `entrypoints/gradio/gradio_demo/gradio_demo_chat.py` — multimodal chat UI.
- `entrypoints/gradio/gradio_demo/gradio_demo_composition.py` — composition/web/article UI.
- `entrypoints/gradio/demo_asset/` and `entrypoints/gradio/SimHei.ttf` — support files/assets needed by the demos.
- `entrypoints/gradio/run_gradio_chat.sh` and `entrypoints/gradio/run_gradio_composition.sh` — wrappers that launch from the bundle directory.

Read `entrypoints/gradio/README.md` and `references/gradio-and-serving.md` before launch. These entrypoints are real services: they import Gradio/torch/Transformers, load the selected model, allocate CUDA memory, and bind ports. Keep the public/private exposure policy explicit.

## Core Decision Rules

- Prefer Transformers when the user needs the documented Python methods (`chat`, `write_webpage`, `resume_2_webpage`, `screen_2_webpage`, `write_artical`) or direct access to history/image placeholder behavior.
- Prefer LMDeploy when the user asks for inference acceleration, lower KV-cache memory, API-server-style serving, or current 2.5 4-bit/AWQ usage. Confirm CUDA compatibility first; the repo install notes state that default LMDeploy wheels target CUDA 12.x and CUDA 11.x needs the LMDeploy installation guide.
- Prefer current 2.5 snippets for video, multi-image, web, and article workflows unless the user explicitly targets legacy 2.0 or 1.0 checkpoints.
- Use multi-GPU dispatch only for Transformers model placement planning. The source utility maps vision/front modules to GPU 0, transformer layers across GPUs, and output/norm modules to the last GPU; verify module names against the chosen model family before execution.
- For multi-image prompts, count `<ImageHere>` placeholders and image paths. The model code warns instead of hard failing when counts differ; operational plans should treat mismatch as a correctness bug.
- Treat `write_artical` as the exact misspelled API name in source code. Do not silently rename it to `write_article` in runnable snippets.

## Non-Execution Boundaries

- Do not load `AutoModel`, `AutoTokenizer`, LMDeploy `pipeline`, Gradio `Blocks`, or any CUDA object while operating this skill.
- Do not download hosted checkpoints, fonts, images, videos, benchmark data, or Gradio assets.
- Do not start Gradio, LMDeploy API servers, OpenAI-compatible clients, or network listeners.
- Do not write generated HTML/article outputs from model calls; only render scripts that would do so when a user executes them in their own runtime.
- Do not assume the original source repository is available to the Researcher. Use these bundled references and scripts as the self-contained operating graph.

## Output Expectations

A good response from this sub-skill states the chosen backend and model family, the exact API or command shape, image/video/placeholder expectations, GPU/VRAM and dependency assumptions, safe rendered helper commands when useful, expected output files, known blockers, and the sibling sub-skill to use if the request turns into OmniLive, fine-tuning, reward modeling, or benchmark work.
