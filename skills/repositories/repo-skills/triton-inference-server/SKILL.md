---
name: triton-inference-server
description: "Route NVIDIA Triton Inference Server tasks across server runtime,
  model repository configuration, KServe protocols, Python in-process frontends,
  and OpenAI-compatible LLM serving."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Triton Inference Server

Use this repo skill when a task involves NVIDIA Triton Inference Server: launching or deploying `tritonserver`, authoring model repositories and `config.pbtxt`, sending KServe HTTP/gRPC requests, using Triton Python in-process frontends, or serving LLMs through Triton's OpenAI-compatible frontend.

## First Routing Decision

- **Run, build, deploy, observe, or debug the server/container**: use [`sub-skills/server-runtime-and-deployment/SKILL.md`](sub-skills/server-runtime-and-deployment/SKILL.md).
- **Create, validate, or troubleshoot a model repository or `config.pbtxt`**: use [`sub-skills/model-repository-and-config/SKILL.md`](sub-skills/model-repository-and-config/SKILL.md).
- **Call Triton over KServe HTTP/gRPC or build request payloads**: use [`sub-skills/client-protocols/SKILL.md`](sub-skills/client-protocols/SKILL.md).
- **Embed Triton in Python with `tritonserver` and `tritonfrontend` KServe/Metrics services**: use [`sub-skills/in-process-frontends/SKILL.md`](sub-skills/in-process-frontends/SKILL.md).
- **Launch or call Triton's OpenAI-compatible LLM frontend**: use [`sub-skills/openai-llm-frontend/SKILL.md`](sub-skills/openai-llm-frontend/SKILL.md).

If a user asks for a complete deployment, follow the chain: runtime/deployment -> model repository/config -> protocol or OpenAI request -> observability/troubleshooting.

## Quick Operating Workflow

1. Identify whether the user is operating an external `tritonserver` binary/container, an embedded Python server, or the OpenAI-compatible frontend.
2. Confirm the model repository location, container or package version, backend family, CPU/GPU requirement, ports, and whether live commands are safe to run.
3. Use [`references/package-and-installation.md`](references/package-and-installation.md) to choose the public runtime/package surface and run read-only environment checks.
4. Use the appropriate sub-skill helper scripts to plan commands, validate model repository layout, or build request JSON before running live services.
5. Use [`references/troubleshooting.md`](references/troubleshooting.md) for cross-cutting triage and then route to the nearest focused sub-skill for detailed fixes.
6. Use [`references/repo-provenance.md`](references/repo-provenance.md) before relying on the skill for a different checkout or release; refresh if the source baseline changed.

## Minimal Read-only Checks

From this skill directory, these helpers are safe and do not start services:

```bash
python3 scripts/check_triton_environment.py --json
python3 sub-skills/server-runtime-and-deployment/scripts/plan_triton_launch.py --context cpu --model-repository /models --gpu none
python3 sub-skills/model-repository-and-config/scripts/validate_model_repository.py --model-repository /models
python3 sub-skills/client-protocols/scripts/build_kserve_request.py health --kind ready
python3 sub-skills/openai-llm-frontend/scripts/build_openai_request.py models
```

Replace `/models` and URLs with the user's target runtime values. A dry-run helper can catch wrong paths, missing packages, invalid flags, or malformed payloads, but only live Triton model load/infer checks prove runtime behavior.

## Runtime Surface Notes

- Standard server containers use tags such as `nvcr.io/nvidia/tritonserver:YY.MM-py3`; LLM-focused serving uses variant tags such as `YY.MM-vllm-python-py3` or `YY.MM-trtllm-python-py3`.
- `tritonclient` is a client library; it does not provide the server binary.
- Python `tritonserver` and `tritonfrontend` wheels are native packages that must match the Triton runtime libraries.
- CPU-only import or payload generation does not prove GPU inference, TensorRT-LLM, vLLM, CUDA shared memory, or GPU metrics. Verify those in a compatible runtime.
- Treat model repositories, backend libraries, Python backend models, repository agents, and cache plugins as executable trust boundaries.

## Capability Map

| User intent | Start here | Useful helper |
| --- | --- | --- |
| Plan a Docker or in-container `tritonserver` command | `server-runtime-and-deployment` | `sub-skills/server-runtime-and-deployment/scripts/plan_triton_launch.py` |
| Plan `compose.py` or `build.py` command templates | `server-runtime-and-deployment` | `sub-skills/server-runtime-and-deployment/scripts/plan_triton_build.py` |
| Validate model repository structure and common config fields | `model-repository-and-config` | `sub-skills/model-repository-and-config/scripts/validate_model_repository.py` |
| Emit KServe v2 health/metadata/infer/repository-control request specs | `client-protocols` | `sub-skills/client-protocols/scripts/build_kserve_request.py` |
| Inspect `tritonfrontend` option defaults | `in-process-frontends` | `sub-skills/in-process-frontends/scripts/inspect_frontend_options.py` |
| Plan OpenAI-compatible frontend CLI | `openai-llm-frontend` | `sub-skills/openai-llm-frontend/scripts/build_openai_frontend_command.py` |
| Emit OpenAI-compatible `/v1/*` JSON request specs | `openai-llm-frontend` | `sub-skills/openai-llm-frontend/scripts/build_openai_request.py` |

## Safety And Escalation

- Ask before pulling large containers, downloading model weights, running long benchmarks, building Triton, mutating production model repositories, or using cloud credentials.
- Prefer read-only model repository mounts until dynamic updates are explicitly required.
- For production, keep readiness strict, restrict model repository/control APIs, and place Triton behind an authentication/TLS gateway or service mesh when clients are untrusted.
- If a live command fails, record the exact runtime layer: container/GPU, model repository/config, protocol/payload, Python in-process import/lifecycle, or OpenAI frontend/backend/tokenizer.
