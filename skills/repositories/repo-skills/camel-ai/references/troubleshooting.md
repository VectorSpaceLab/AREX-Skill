# CAMEL-AI Cross-Cutting Troubleshooting

## Install And Import

- Use Python supported by the package metadata: `>=3.10,<3.15`; Python 3.10-3.12 is safer for optional compiled/document-processing extras.
- If `import camel` fails after installing only the source tree, install the package with `pip install camel-ai` or `pip install -e .` so base dependencies such as `openai`, `pydantic`, `mcp`, `tiktoken`, and `docstring-parser` are present.
- If optional modules fail with `ModuleNotFoundError`, install only the owning extra for the workflow instead of `camel-ai[all]` unless a full development environment is intentional.
- Python 3.13+ can be incompatible with some optional document/vector dependencies documented by CAMEL; use Python 3.10-3.12 when `unstructured`, `pyobvector`, or NumPy-constrained stacks are required.

## Credentials And Services

- Provider models, web/search tools, loaders, hosted embeddings, vector stores, MCP servers, OpenAPI services, Slack/Discord/GitHub integrations, and benchmarks often need API keys or running services.
- Keep secrets in environment variables or external config; never hard-code them in skill prompts, examples, or generated scripts.
- For local endpoints such as Ollama, vLLM, SGLang, LMStudio, Docker runtimes, browsers, and databases, verify the service is running with a short health check before constructing agents.

## Data And Config Validation

- Validate model provider/type pairs, `model_config_dict`, structured-output schemas, tool schemas, vector dimensions, loader output rows, benchmark dataset splits, and environment reset/step contracts before running model-backed workflows.
- Prefer small fixtures, no-network inspection scripts, and mocked/offline tests in CI.
- Treat benchmark and data-generation runs as potentially expensive; cap subsets, set seeds, write checkpoints, and rerun only failed records.

## Route Workflow-Specific Failures

- Agent loops, role-play state, Workforce timeouts, and task trees: `sub-skills/agents-and-societies/references/troubleshooting.md`.
- Model backend, provider credentials, local endpoint, and structured output failures: `sub-skills/models-and-configuration/references/troubleshooting.md`.
- Tool schema, MCP/OpenAPI, runtime, interpreter, browser, Docker, and service failures: `sub-skills/tools-runtimes-and-services/references/troubleshooting.md`.
- Memory/RAG, embedding, vector store, loader, datahub, and dataset failures: `sub-skills/memory-rag-and-data/references/troubleshooting.md`.
- Datagen, verifier, extractor, environment, and benchmark failures: `sub-skills/datagen-evaluation-and-benchmarks/references/troubleshooting.md`.
