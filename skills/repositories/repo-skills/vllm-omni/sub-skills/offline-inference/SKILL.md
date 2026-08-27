---
name: offline-inference
description: "Use vLLM-Omni local Python APIs for offline Omni and AsyncOmni
  inference, prompt dictionaries, diffusion sampling parameters,
  batched/generator flows, and multimodal output access."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Offline inference

Use this sub-skill when a user needs local Python inference with vLLM-Omni rather than an HTTP server. It covers the synchronous `Omni` entrypoint, the asynchronous `AsyncOmni` entrypoint, prompt dictionaries, `OmniDiffusionSamplingParams`, batched or generator-style request flows, and safe access to text, image, audio, video, latent, and trajectory outputs.

## Route here for

- Building a local Python script with `Omni(model=..., **kwargs)` or `AsyncOmni(model=..., **kwargs)`.
- Creating prompt dictionaries for text-to-image, image-to-image/edit, image/video/audio chat, Qwen3-Omni-style text/audio responses, or TTS-style `additional_information` payloads.
- Supplying diffusion sampling controls such as `height`, `width`, `num_frames`, `num_inference_steps`, `guidance_scale`, `seed`, `output_type`, `lora_request`, `lora_scale`, `extra_args`, and trajectory-return flags.
- Iterating over synchronous `py_generator=True` outputs or `async for` outputs from `AsyncOmni.generate(...)`.
- Debugging where generated content lives on `OmniRequestOutput` objects.

## Route elsewhere

- OpenAI-compatible HTTP serving, curl payloads, OpenAI SDK calls, realtime clients, or `vllm serve ... --omni`: use the sibling online-serving sub-skill.
- Deploy YAML topology, connector choice, stage placement, memory overlays, or distributed launch planning: use the sibling stage-configuration sub-skill.
- Model family selection, recipe adaptation, offload/parallel/quantization tradeoffs, cache backends, or hardware-specific model choices: use the sibling model-recipes sub-skill.
- Adding new model implementations, custom pipeline internals, adapter contracts, or maintainer tests: use the sibling model-integration sub-skill.

## Always read first

1. [API reference](references/api-reference.md) for verified signatures, prompt keys, sampling parameters, and output fields.
2. [Workflows](references/workflows.md) for copyable local-script patterns.
3. [Troubleshooting](references/troubleshooting.md) before running large models or debugging missing modalities/OOM/version warnings.

## Safety and execution checklist

- Confirm the environment can import compatible `vllm` and `vllm_omni` packages before loading a model.
- Treat model execution as GPU/accelerator- and model-cache-dependent. Do not assume network access, checkpoint availability, or gated-repo permission.
- Prefer local model paths when the user has already cached weights.
- For generated examples, start from the safe bundled helper: `python scripts/build_offline_request.py --help`. The helper only prints code; it does not import vLLM-Omni, contact a server, download weights, or instantiate a model.
- Keep original full-model examples as evidence only. Do not tell a future agent to run repository examples as a prerequisite for using this skill.
