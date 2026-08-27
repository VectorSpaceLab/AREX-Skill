---
name: comfyui-ltxvideo
description: "Operate ComfyUI-LTXVideo custom nodes for LTX-2 video, audio,
  IC-LoRA, prompt-conditioning, and advanced ComfyUI workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NOASSERTION
---

# ComfyUI-LTXVideo

Use this repo skill when the user wants to install, inspect, plan, adapt, or debug **ComfyUI-LTXVideo** custom-node workflows for LTX-2 video/audio generation. This repository is a ComfyUI custom-node package, not a standalone Python library; practical use assumes a working ComfyUI runtime plus this custom-node folder loaded by ComfyUI or installed through ComfyUI Manager.

Do not send future agents back to the original source checkout or original example JSON paths. The references below distill the repo evidence and native workflow families into self-contained guidance.

## Before promising native generation

Read [model and backend requirements](references/model-and-backend-requirements.md) when the task involves running ComfyUI, loading models, or diagnosing missing nodes/models. The README requires a CUDA-capable GPU, recommends 32GB+ VRAM and 100GB+ model/cache disk for LTX-2 workflows, and expects user-provided model files in ComfyUI model folders.

For safe static inspection of a checkout, use:

- [`scripts/inspect_custom_node_package.py`](scripts/inspect_custom_node_package.py): load a ComfyUI root plus a ComfyUI-LTXVideo custom-node folder and report node mapping counts.
- [`scripts/summarize_workflow_json.py`](scripts/summarize_workflow_json.py): summarize exported ComfyUI workflow JSON node types without running generation.

## Route map

| User task signal | Read next | Why |
| --- | --- | --- |
| Ordinary LTX-2 text-to-video, image-to-video, video-to-video/detailer, single-stage/two-stage generation, samplers, latents, VAE decode, long/tiled clips, low VRAM loading | [core-generation](sub-skills/core-generation/SKILL.md) | Owns normal graph construction, sampler/decode choices, latent frame math, tiling, looping, and core VRAM troubleshooting. |
| Gemma local text encoder, Gemma API text encoding, prompt enhancement, saved conditioning safetensors, dynamic conditioning, multimodal guider parameters | [prompt-conditioning](sub-skills/prompt-conditioning/SKILL.md) | Owns prompt-to-conditioning surfaces and guider inputs consumed by samplers and specialized workflows. |
| IC-LoRA union control, motion tracks, HDR, DubIt, text-to-audio, audio-only model mode, inpaint/outpaint masks, pixel spatial upscaler, ingredients workflows | [specialized-workflows](sub-skills/specialized-workflows/SKILL.md) | Owns LTX-2 specialty workflow families and media-specific helper nodes. |
| STG/APG, Q8 kernels, VAE/Q8 patching, latent/stat normalization, decoder noise, attention bank/override, flow-edit, PAG/FETA, RF samplers, inverse prediction | [advanced-control](sub-skills/advanced-control/SKILL.md) | Owns expert and optional model-internal control surfaces. |
| Nodes do not appear, `comfy` import fails, CUDA/torch is wrong, model files are missing, optional q8/OpenEXR/Kornia errors appear | [root troubleshooting](references/troubleshooting.md) first | Cross-cutting installation, backend, and compatibility failures affect every workflow family. |

## Operating workflow

1. **Classify the request by workflow family.** If the task names T2V/I2V/V2V, first try [core-generation](sub-skills/core-generation/SKILL.md). If it names IC-LoRA, HDR, T2A, masks, motion, or DubIt, use [specialized-workflows](sub-skills/specialized-workflows/SKILL.md). If it names prompt, Gemma, or conditioning, use [prompt-conditioning](sub-skills/prompt-conditioning/SKILL.md). If it names Q8/STG/tricks, use [advanced-control](sub-skills/advanced-control/SKILL.md).
2. **Check prerequisites before graph details.** Confirm ComfyUI is present, this custom node package is loaded, CUDA and model files match the requested workflow, and optional packages are installed only for the features that need them.
3. **Use node names as routing signals.** The repo exposes 78 custom node class mappings in source inspection. Read [node catalog](references/node-catalog.md) when a user gives a node name and you need to find its owner.
4. **Use workflow families, not original file paths.** Native workflow JSONs showed LTX-2.0, LTX-2.3, and LTX-2.5 recipe families. Use [workflow overview](references/workflow-overview.md) for the distilled family map rather than pointing to source examples.
5. **Avoid unsafe or expensive checks unless requested.** Model downloads, ComfyUI generation, large media processing, API calls, EXR writing, and Q8 kernel installation are not safe static checks. Use bundled preflight/validator scripts first.
6. **Keep prompt, sampler, and specialty responsibilities separate.** A specialized IC-LoRA or HDR task usually still needs prompt conditioning and core sampler/decode choices; route across sub-skills instead of duplicating advice.

## Public references

- [Model and backend requirements](references/model-and-backend-requirements.md): install modes, CUDA/VRAM, model folder layout, optional dependencies, and compatibility notes.
- [Workflow overview](references/workflow-overview.md): self-contained map of T2V/I2V/V2V, IC-LoRA, T2A, HDR, mask, and advanced workflow families.
- [Node catalog](references/node-catalog.md): grouped node taxonomy and owning sub-skill for user-supplied node names.
- [Troubleshooting](references/troubleshooting.md): cross-cutting failure symptoms and recovery steps.
- [Repo provenance](references/repo-provenance.md): source commit, dirty-state baseline, package-version status, and evidence paths.
- [Router metadata](references/repo-routing-metadata.json): structured scenario metadata for repo-skills-router import tooling.

## Runtime boundaries

- This skill does not create, download, or redistribute LTX/Gemma/LoRA/audio/upscaler model weights.
- This skill does not guarantee native generation unless the user's ComfyUI runtime, CUDA stack, model files, and optional packages are available.
- Generated helper scripts are static/preflight tools; they do not start ComfyUI or run model inference.
- If the user asks to modify this repository's source code rather than operate the package, treat that as repository maintenance and use a maintenance workflow instead of this operating skill.
