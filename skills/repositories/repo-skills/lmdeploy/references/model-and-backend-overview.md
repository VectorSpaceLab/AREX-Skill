# Model and Backend Overview

Read this when choosing which LMDeploy route should own a task.

## Project Positioning

LMDeploy is a Python toolkit for compressing, deploying, and serving LLMs and VLMs. Its public workflows cluster around five areas:

- Offline inference with `lmdeploy.pipeline` and `lmdeploy chat`.
- OpenAI-compatible, Responses-compatible, and Anthropic-compatible serving.
- Vision-language and multimodal media input handling.
- Lite quantization and quantized-artifact handoff.
- PyTorch/TurboMind backend tuning and model-extension work.

## Engines

| Engine | Best fit | Typical config | Watch for |
| --- | --- | --- | --- |
| TurboMind | Optimized GPU deployment, quantized model loading, high-throughput serving | `TurbomindEngineConfig(tp=..., session_len=..., cache_max_entry_count=...)` | `_turbomind` extension availability, CUDA/NCCL/runtime compatibility, cache memory pressure |
| PyTorch | Python-first feature development, new-model support, LoRA/adapters, some advanced parser/return features | `PytorchEngineConfig(device_type="cuda", session_len=..., adapters=...)` | `torch`/`triton`/`transformers` version ranges, multiprocessing main guard for tensor parallel scripts |

When a user does not specify an engine, LMDeploy can infer one from model/task metadata. For repeatable guidance, set `backend_config` in Python or `--backend` in CLI examples.

## Primary Entry Points

- Python: `from lmdeploy import pipeline, GenerationConfig, PytorchEngineConfig, TurbomindEngineConfig, ChatTemplateConfig`.
- VLM helpers: `from lmdeploy.vl import load_image, encode_image_base64` and related media helpers.
- CLI: `lmdeploy chat`, `lmdeploy serve api_server`, `lmdeploy serve proxy`, `lmdeploy lite auto_awq`, `lmdeploy lite smooth_quant`.
- Serving client: `lmdeploy.serve.openai.api_client.APIClient` for simple OpenAI-compatible calls; OpenAI SDK, Codex, and Claude Code use HTTP-compatible endpoints.

## Route Selection

| Need | Route |
| --- | --- |
| Prompt batching, streaming, chat sessions, generation parameters, logits/PPL | `sub-skills/pipeline-inference/SKILL.md` |
| Network service, API payloads, auth, proxy, Responses/Anthropic compatibility, client setup | `sub-skills/serving-apis/SKILL.md` |
| Images/video/audio/time-series content blocks, `VisionConfig`, media URL/base64 validation | `sub-skills/vision-language/SKILL.md` |
| Weight quantization, KV-cache quantization, calibration, quantized model-format handoff | `sub-skills/quantization/SKILL.md` |
| Backend internals, cache config, source builds, `_turbomind`, adding PyTorch model support | `sub-skills/backend-extension/SKILL.md` |

## Validation Without Model Downloads

Prefer no-download checks before model execution:

```bash
python scripts/check_lmdeploy_environment.py --include-cli
python sub-skills/pipeline-inference/scripts/inspect_pipeline_config.py --include-cli
python sub-skills/vision-language/scripts/check_vl_media_inputs.py
python sub-skills/quantization/scripts/plan_quantization_command.py --help
python sub-skills/backend-extension/scripts/inspect_backend_config.py --json
```

These checks prove package/CLI/config/media syntax only. They do not prove model weights, GPU memory, optional model packages, live server behavior, or quantization quality.
