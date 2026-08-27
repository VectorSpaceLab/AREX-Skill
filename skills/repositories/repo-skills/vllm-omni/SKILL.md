---
name: vllm-omni
description: "Use vLLM-Omni for omni-modality model inference and serving: local
  Omni APIs, OpenAI-compatible --omni servers, stage deploy configs, model
  recipes, and model integration workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# vLLM-Omni

Use this repo skill when a task involves vLLM-Omni: omni-modality inference or serving for text, image, audio, video, action, diffusion, TTS, OpenAI-compatible APIs, stage-based deployment, supported model recipes, or source-level model integration.

## Quick start route

1. For install/import/backend checks, read [install-and-backends.md](references/install-and-backends.md) and run the safe checker when needed:

   ```bash
   python scripts/check_environment.py --require-vllm 0.26
   ```

   Add `--require-cuda` only when live GPU generation or serving must be verified.
2. Choose the closest sub-skill:

   | Task | Read |
   | --- | --- |
   | Local Python scripts using `Omni`, `AsyncOmni`, prompt dictionaries, sampling params, or multimodal outputs | [offline-inference](sub-skills/offline-inference/SKILL.md) |
   | `vllm serve ... --omni`, OpenAI-compatible HTTP payloads, curl/OpenAI SDK clients, realtime/streaming, stage head/headless launch | [online-serving](sub-skills/online-serving/SKILL.md) |
   | Deploy YAML overlays, `stages`, connectors, memory placement, `--stage-overrides`, multi-node/stage planning | [stage-configuration](sub-skills/stage-configuration/SKILL.md) |
   | Choosing supported model families, endpoints, hardware backends, diffusion controls, quantization/offload/cache, benchmark metrics | [model-recipes](sub-skills/model-recipes/SKILL.md) |
   | Adding custom pipelines, model registrations, TTS adapters, or selecting focused maintainer tests | [model-integration](sub-skills/model-integration/SKILL.md) |
3. If a failure crosses workflows, read [troubleshooting.md](references/troubleshooting.md) before running full model examples.
4. To check whether this skill matches the source checkout, read [repo-provenance.md](references/repo-provenance.md).

## What vLLM-Omni adds

vLLM-Omni extends vLLM's text-oriented autoregressive runtime with stage-based and diffusion/generation paths for omni-modality workloads:

- multimodal chat and reasoning with text, image, audio, video, and action inputs;
- heterogeneous outputs including text tokens, images, audio, video, latents, trajectories, and custom payloads;
- OpenAI-compatible serving with Omni-specific request fields and endpoints;
- stage-based deploy configs, connectors, head/headless worker launches, and async chunking;
- diffusion image/video/audio pipelines with attention, parallelism, offload, cache, quantization, and LoRA controls;
- TTS and realtime/duplex audio routes;
- model integration surfaces for custom pipelines and supported model families.

## Install/backend guardrails

- Use a fresh environment. vLLM, PyTorch, CUDA/ROCm/vendor libraries, media packages, and attention kernels are easy to mix incorrectly.
- Align upstream `vllm` with the vLLM-Omni release line. For this checkout's docs, `vllm==0.26.x` is the expected upstream line.
- Set `VLLM_OMNI_TARGET_DEVICE` during source installs when automation must choose CUDA, ROCm, NPU, XPU, MUSA, or CPU requirements deterministically.
- CPU parser/config checks do not prove live model serving. Full generation usually requires GPU/accelerator hardware, model weights, license/cache access, and runtime budget.
- Do not run broad native examples or benchmarks by default; use bundled no-network helpers first.

## Common entry points

- Package import: `import vllm_omni` for registration side effects and `from vllm_omni.entrypoints.omni import Omni` for local generation.
- Local API: `Omni(model=..., **kwargs).generate(...)` and `AsyncOmni(model=...).generate(...)`.
- CLI serving: `vllm serve MODEL --omni ...` or `vllm-omni serve MODEL --omni ...`.
- Deploy config concepts: `DeployConfig`, `StageDeployConfig`, `PipelineConfig`, `stage_id`, `devices`, connectors, `gpu_memory_utilization`, `async_chunk`, platform overrides.
- Model/recipe concepts: Qwen3-Omni, Qwen2.5-Omni, Qwen-Image/Z-Image/GLM/Hunyuan/Wan/LTX/Cosmos3/MiniMax-H3, Qwen3-TTS/VoxCPM2/MOSS/Higgs/IndexTTS, DreamZero/GR00T/InternVLA.

## Bundled helpers

| Helper | Use |
| --- | --- |
| `scripts/check_environment.py` | Verify package metadata, imports, optional CUDA, and Omni CLI help without model downloads. |
| `sub-skills/offline-inference/scripts/build_offline_request.py` | Generate safe local Python request snippets without importing vLLM-Omni or loading a model. |
| `sub-skills/online-serving/scripts/build_openai_payload.py` | Generate curl/OpenAI SDK payload scaffolds without sending HTTP requests. |
| `sub-skills/stage-configuration/scripts/validate_deploy_yaml.py` | Sanity-check deploy YAML shape and connector references without model loading. |
| `sub-skills/stage-configuration/scripts/plan_stage_memory.py` | Estimate stage placement and memory utilization from user-provided GPU/stage counts. |
| `sub-skills/model-recipes/scripts/query_model_catalog.py` | Query the bundled representative model catalog by task/backend. |
| `sub-skills/model-integration/scripts/check_tts_adapter_contract.py` | Statically review TTS adapter source shape without imports or model execution. |

## When to refresh this skill

Refresh when vLLM-Omni changes public CLI flags, OpenAI protocol fields, deploy schemas, supported model tables, diffusion controls, TTS adapters, model registry behavior, or aligned upstream vLLM version.
