---
name: local-inference
description: "Guides LTX-Video local CLI and Python inference workflows,
  conditioning media, prompt handling, and safe command construction."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# LTX-Video local inference

Use this sub-skill when a task asks to run or reason about LTX-Video generation through the repository CLI `inference.py` or the Python API `infer(InferenceConfig)`.

## Route here for

- Building an `inference.py` command for text-to-video, image-to-video, video extension, video-to-video, or multiple conditioning items.
- Translating a user request into `InferenceConfig` fields for `infer(config)`.
- Diagnosing `conditioning_media_paths`, `conditioning_start_frames`, `conditioning_strengths`, `input_media_path`, `offload_to_cpu`, output-path, padding, or prompt-enhancement behavior.
- Checking whether a proposed command is safe before a heavy run that may download checkpoints or prompt-enhancer models.

## Before running generation

1. Choose or inspect the YAML pipeline config with [model-configs](../model-configs/SKILL.md). This sub-skill can pass a config path, but it does not own model-family or YAML-field selection.
2. Confirm runtime readiness: Python package imports, `[inference]` extras for media I/O, a practical CUDA/MPS/CPU backend, and Hugging Face cache/network expectations.
3. Use the bundled command builder before shelling out:

   ```bash
   python scripts/build_inference_command.py \
     --prompt "A precise cinematic prompt" \
     --pipeline-config PATH/TO/ltxv-13b-0.9.8-distilled.yaml \
     --height 704 --width 1216 --num-frames 121 \
     --output-path outputs/ltx-run
   ```

   The script validates static argument rules and prints a shell-safe `python inference.py ...` command. It never imports LTX-Video, runs inference, or downloads models.
4. Treat full generation as expensive: checkpoint, text-encoder, spatial-upscaler, and prompt-enhancer downloads may occur when paths in the config are not local.

## Main workflows

- For CLI and Python recipes, see [references/workflows.md](references/workflows.md).
- For verified `InferenceConfig` fields and key function behavior, see [references/api-reference.md](references/api-reference.md).
- For failure modes and repairs, see [references/troubleshooting.md](references/troubleshooting.md).

## Boundary routing

- YAML/model selection, FP8-vs-bfloat16 config choice, base-vs-multi-scale config details, and config editing route to [model-configs](../model-configs/SKILL.md).
- Direct `LTXVideoPipeline`, `LTXMultiScalePipeline`, scheduler, VAE, transformer, latent, or prompt-enhancer internals route to [pipeline-components](../pipeline-components/SKILL.md).
- Training, ComfyUI workflow editing, Diffusers documentation, LTX-2, and external control/trainer repositories are non-goals for this local CLI/API workflow.
