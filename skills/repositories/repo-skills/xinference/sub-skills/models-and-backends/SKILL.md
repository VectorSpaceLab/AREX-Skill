---
name: models-and-backends
description: "Select, validate, and troubleshoot Xinference model families,
  custom model specs, virtual environments, LoRA, and runtime backends without
  assuming downloads or accelerator execution."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Models and Backends

Use this sub-skill when the task is about choosing a model family, checking a
custom model JSON file, matching a backend to a model format or quantization, or
diagnosing optional dependency and accelerator problems.

## Use this for

- Built-in and custom model families for LLM, embedding, rerank, image, audio,
  video, and flexible models.
- Custom model JSON validation before CLI or client registration.
- Backend/engine fit for `transformers`, `llama_cpp`, `vllm`, `sglang`, `mlx`,
  embedding/rerank/image/video/audio extras, telemetry, and vendor variants.
- Model format, quantization, size, `model_path`, `model_uri`, `model_id`, and
  local-vs-hub source decisions.
- LoRA attachment, per-model virtual environments, dependency markers, and
  launch-time package overrides.
- Memory-estimation planning and backend caveats before expensive launches.

## Route away when needed

- Starting local services, supervisor/worker processes, or model lifecycle CLI
  commands: `serving-and-cli`.
- Python client calls, HTTP request bodies, OpenAI-compatible base URLs, or
  streaming response handling: `client-and-api`.
- Auth, metrics, logging, persistent state, deployment hardening, and general
  environment-variable policy: `operations-and-security`.

## Working pattern

1. Identify the model type and model ability first.
2. Decide whether the task uses a built-in family, a custom model JSON, or a
   flexible launcher.
3. Validate custom JSON offline before trying to register or launch it.
4. Match the desired model format and quantization to a compatible backend.
5. Confirm platform gates and optional extras before claiming a backend is
   usable.
6. Add LoRA, virtualenv, and memory planning only after the family/backend pair
   is valid.
7. Route to service or client sub-skills for the actual launch or request.

## Required cautions

- LLM launches require an explicit `model_engine`; embedding, rerank, and image
  routes can have default engines when omitted.
- A package import, CLI help check, or JSON validation is not proof that a real
  model download or GPU/MPS backend run succeeded.
- vLLM and SGLang are CUDA/Linux-oriented and model-family constrained.
- MLX is macOS arm64 / Apple-silicon-specific.
- SGLang is not included in the `all` extra; install it deliberately.
- Custom video registration is not supported by the bundled checker; treat video
  custom specs as unsupported unless future package evidence changes.

## References

- [Model overview](references/model-overview.md) for the family/type map and
  selection cues.
- [Custom models](references/custom-models.md) for JSON shapes and registration
  boundaries.
- [Backend compatibility](references/backend-compatibility.md) for extras,
  platform gates, quantization, and memory planning.
- [Virtual envs and LoRA](references/virtual-envs-and-lora.md) for per-model
  dependency isolation and adapter attachment.
- [Troubleshooting](references/troubleshooting.md) for validation failures,
  missing extras, and backend-gate errors.

## Bundled checker

- [check_model_config.py](scripts/check_model_config.py) validates a custom
  model JSON file offline and can print a safe `xinference register` command
  template. It does not download models or start a service.
