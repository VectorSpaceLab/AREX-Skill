---
name: vllm
description: "Route vLLM tasks across offline inference, OpenAI-compatible
  serving, structured/tool/reasoning, multimodal/LoRA/pooling, and
  deployment/performance workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# vLLM

Use this skill when the user asks how to install, use, serve, configure, troubleshoot, or optimize vLLM, the high-throughput inference and serving engine for LLMs. This root skill is a router; open the focused sub-skill before writing substantial commands or code.

## First Checks

- Confirm whether the user wants **in-process Python inference** or an **OpenAI-compatible HTTP server**.
- Ask for the model identifier/path, hardware target, and whether model downloads, remote code, local media, or credentials are allowed before running live model commands.
- Treat GPU execution, model downloads, multi-node launches, and benchmark runs as environment-gated; prefer help/static checks until the user confirms resources.
- Use `references/repo-provenance.md` to check whether this skill is aligned with the current vLLM checkout.
- Use `references/troubleshooting.md` for cross-cutting install/import/backend triage before routing to workflow-specific troubleshooting.

## Route by Workflow

| User asks for | Open |
| --- | --- |
| Python `LLM`, `SamplingParams`, `generate`, `chat`, `encode`, `embed`, `classify`, `score`, output extraction, or offline smoke scripts | `sub-skills/offline-inference/SKILL.md` |
| `vllm serve`, OpenAI clients, `/v1` endpoints, `chat`, `complete`, `run-batch`, model discovery, server/client errors | `sub-skills/openai-serving/SKILL.md` |
| Structured outputs, JSON schema, regex/grammar constraints, tool calling, reasoning parsers, chat templates, streaming tool-call deltas | `sub-skills/structured-tool-reasoning/SKILL.md` |
| Multimodal image/audio/video payloads, media allowlists, LoRA/adapters, embeddings, rerank, score, pooling outputs | `sub-skills/modalities-adapters-pooling/SKILL.md` |
| Memory planning, parallelism, quantization, KV cache/offload, disaggregated serving, Ray/torchrun, metrics, profiling, benchmarks | `sub-skills/deployment-performance/SKILL.md` |

## Common Starting Points

- **Install/import sanity**: vLLM supports Python 3.10 through 3.14 in package metadata; runtime builds are backend-specific. For source installs, follow the project’s current documented environment workflow instead of mixing package managers.
- **Minimal import check**: `python -c "import vllm; print(vllm.__version__)"` verifies importability, but it does not prove a model/backend can run.
- **CLI discovery**: `vllm --help`, `vllm serve --help`, and `vllm serve --help=all` expose current command groups and flags.
- **Server default**: `vllm serve [model_tag] [options]` launches an OpenAI-compatible server; if omitted, current CLI help documents a default small Qwen model, but production commands should pass an explicit model.
- **Offline default**: `LLM(model=...)` plus `SamplingParams(max_tokens=...)` is the main in-process path; chat models usually need `LLM.chat` or an explicit chat template rather than raw `generate` prompts.

## Bundled Root Helpers

- `scripts/vllm_skill_doctor.py`: checks Python import, distribution metadata, CLI availability, and selected backend facts without downloading models or starting a server.

Sub-skills also include focused helpers for offline smoke planning, serve command construction, OpenAI client smoke checks, structured request validation, multimodal payload validation, environment summaries, and memory command planning.

## Safety Defaults

- Do not start a server, download a model, enable `trust_remote_code`, read arbitrary local media, execute tool calls, or run distributed/benchmark commands unless the user explicitly approves the required resources and side effects.
- For local media in OpenAI-compatible multimodal requests, require a narrow `--allowed-local-media-path`; for remote media, use explicit `--allowed-media-domain` entries.
- For API keys, tokens, Hugging Face credentials, and server auth, describe required environment variables or headers without echoing secret values.
- For performance problems, collect environment and configuration facts first, then propose bounded experiments; avoid broad benchmark suites unless requested.

## Verification Scope

This skill was generated from vLLM source, docs, examples, tests, package metadata, and a CPU/precompiled package-inspection environment. Live GPU model serving, model downloads, multi-node runs, and native benchmark execution remain user-environment gated and should be verified with the user’s actual hardware and model.
