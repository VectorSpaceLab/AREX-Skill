---
name: model-recipes
description: "Select vLLM-Omni model families, endpoints, diffusion controls,
  quantization/offload/cache recipes, backend routes, and benchmark targets
  without reopening repository evidence."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# vLLM-Omni model recipes

Use this sub-skill when the task is to choose or adapt a vLLM-Omni model family,
serving endpoint, hardware/backend route, diffusion optimization stack, or
benchmark target. It is a router and decision aid; detailed payload code belongs
to sibling usage sub-skills.

## Fast route

1. Identify the desired output: text/chat, speech/TTS, image, video, audio/video,
action, or robot policy.
2. Query the bundled static catalog when you need a quick shortlist:

   ```bash
   python scripts/query_model_catalog.py --task text-to-video --backend cuda
   python scripts/query_model_catalog.py --task tts --backend cuda --format json
   ```

3. Read [references/model-selection-and-recipes.md](references/model-selection-and-recipes.md)
   for model-family taxonomy, endpoint/API choice, and route-level backend notes.
4. For diffusion image/video/audio or world/action models, read
   [references/diffusion-quantization-and-offload.md](references/diffusion-quantization-and-offload.md)
   before enabling batching, step execution, attention backend overrides, LoRA,
   HSDP, offload, cache, or quantization.
5. Read [references/benchmarking.md](references/benchmarking.md) before selecting
   TTFT, TPOT, TTFP, E2EL, RTF, or throughput targets.
6. Read [references/troubleshooting.md](references/troubleshooting.md) when a
   model is gated, unavailable in cache, rejected by a backend, or fails after a
   quantization/offload/cache change.

## Boundary with sibling sub-skills

- Need executable offline Python using `Omni.generate`, request dictionaries, or
  output accessors -> use `offline-inference`.
- Need `curl`, OpenAI SDK payloads, `/v1/*` request bodies, or server/client
  mechanics -> use `online-serving`.
- Need stage YAML, connectors, head/headless placement, or memory overlays ->
  use `stage-configuration`.
- Need to add or edit a model implementation, register a custom pipeline, or
  check TTS adapter internals -> use `model-integration`.

## Safety and evidence limits

- This sub-skill is self-contained. Do not reopen the original checkout just to
  find model lists, recipes, or examples.
- Do not start downloads, gated-model access, native examples, or long benchmarks
  unless the user explicitly approves the model/cache/backend budget.
- Treat source examples that require GPUs, network downloads, or external model
  licenses as evidence only; reproduce their intent through the distilled
  guidance here.
- Prefer conservative BF16/eager or documented baseline routes when validating a
  new model-family/backend combination, then add one optimization at a time.
