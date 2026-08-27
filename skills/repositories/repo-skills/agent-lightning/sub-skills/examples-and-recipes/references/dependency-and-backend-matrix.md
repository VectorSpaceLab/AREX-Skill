# Dependency and backend matrix

## Purpose

Use this matrix before installing optional dependency groups or running examples.

## Core environment

| Capability | Needs | Verification level |
| --- | --- | --- |
| Import `agentlightning` | Python `>=3.10`, base package dependencies | required and CPU-safe |
| Author/decorate agents | base package | required and CPU-safe |
| In-memory store/runners/tracing | base package | required and CPU-safe |
| CLI help (`agl`, `agl store`) | installed console script | required and CPU-safe |
| Prometheus CLI/service | `prometheus-client` and runtime env var for service start | optional but CPU-safe |

## Optional algorithms and examples

| Workflow | Extras/groups | Backend/service | Notes |
| --- | --- | --- | --- |
| APO prompt optimization | `agentlightning[apo]` or `apo` group plus base | OpenAI-compatible endpoint/API key | `APO` imports `poml`; full optimization calls LLMs. |
| VERL training | `agentlightning[verl]`, torch/vLLM/VERL groups | CUDA recommended/expected | Avoid installing into a minimal CPU environment unless selected. |
| vLLM serving/proxy | vLLM group/version and torch stack | CUDA for practical serving | Use `agl vllm` only when vLLM imports. |
| Mongo store | `agentlightning[mongo]` | MongoDB replica set | In-memory store fully validates core APIs but not persistence. |
| Weave tracing | `agentlightning[weave]` | Weave config/service as needed | Experimental; avoid mixing with other auto-instrumentation without tests. |
| Unsloth SFT | `trl`, torch/vLLM, Unsloth deps | CUDA GPU | Training-heavy; verify tiny import/GPU allocation first. |
| ChartQA / vision | `image`, langchain, vLLM/torch stack | GPU, image/model/data downloads | Do not run by default. |
| Spider SQL | `sql`, `langchain`, agents groups | dataset, LLM endpoint, often GPU for training | CPU can validate schema/tool logic only. |
| RAG | `rag`, agents, VERL stack | FAISS/index data, LLM backend, GPU for training | Historical/optional. |
| Azure fine-tuning | Azure/OpenAI SDK deps | Azure subscription/auth/quota | Costly/deployment workflow; require explicit authorization. |
| Claude Code SWE-bench | `swebench`, Anthropic/OpenAI/vLLM deps | Docker, API key or local model | Potentially expensive and mutating. |
| Tinker | `tinker` group | Tinker credentials/service | Hosted training; use dry-run if available. |
| Dashboard | Node/npm | Node 22/npm | Maintainer workflow, not package runtime. |

## Choosing a validation level

| Level | Use when | Examples |
| --- | --- | --- |
| help-only | command exists but running would start services or need credentials | `agl vllm --help`, endpoint checker help |
| tiny-fixture | CPU-local behavior is enough | rollout smoke, local trace smoke, in-memory store smoke |
| interface smoke | external endpoint/service is supplied | LiteLLM/OpenAI-compatible chat check |
| optional backend smoke | user supplies backend/hardware | Mongo connection, torch CUDA allocation, vLLM startup |
| full example | user explicitly requests and supplies time/resources | APO optimization, VERL training, Azure fine-tune |

## Dependency conflict guidance

- Keep CPU-only package inspection separate from GPU-heavy training environments.
- Do not install broad example groups just to answer an API authoring question.
- If a subcommand or optional algorithm fails on missing dependencies, classify whether the user's task actually requires that optional path.
- For CUDA stacks, follow the repository's torch/vLLM compatibility groups instead of mixing arbitrary latest packages.
- For hosted services, verify account credentials and quotas before launching long or costly workflows.
