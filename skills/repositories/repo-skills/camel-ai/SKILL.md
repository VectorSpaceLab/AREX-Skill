---
name: camel-ai
description: "Use CAMEL-AI to build, configure, tool, remember, evaluate, and
  troubleshoot multi-agent Python systems with self-contained routing across
  agents, models, tools, RAG, and evaluation workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# CAMEL-AI Repo Skill

Use this repo skill when a task mentions CAMEL-AI, `camel-ai`, the `camel` Python package, `ChatAgent`, `RolePlaying`, `Workforce`, CAMEL toolkits, CAMEL model backends, CAMEL memory/RAG, or CAMEL benchmark/datagen/evaluation workflows.

## First Checks

1. Install the base package with `pip install camel-ai` for core agents, models, messages, tools, and package imports.
2. Install only the optional extras needed for the chosen workflow, such as `camel-ai[model_platforms]`, `camel-ai[rag]`, `camel-ai[storage]`, `camel-ai[document_tools]`, `camel-ai[web_tools]`, or `camel-ai[dev_tools]`.
3. Run [scripts/inspect_camel_install.py](scripts/inspect_camel_install.py) for a no-network import, version, and route check.
4. Read [references/troubleshooting.md](references/troubleshooting.md) before installing broad extras, debugging provider credentials, or running network/Docker/browser/benchmark workflows.

## Route By Task

| Task or signal | Read |
| --- | --- |
| Build a `ChatAgent`, system/user/assistant messages, task tree, role-playing society, or `Workforce` | [sub-skills/agents-and-societies/SKILL.md](sub-skills/agents-and-societies/SKILL.md) |
| Configure model providers, `ModelFactory`, `ModelManager`, provider enums, local/OpenAI-compatible endpoints, structured output, audio, or multimodal models | [sub-skills/models-and-configuration/SKILL.md](sub-skills/models-and-configuration/SKILL.md) |
| Attach `FunctionTool`, built-in toolkits, MCP/OpenAPI tools, code execution, interpreters, runtimes, browser/Docker/terminal tools, or CAMEL services | [sub-skills/tools-runtimes-and-services/SKILL.md](sub-skills/tools-runtimes-and-services/SKILL.md) |
| Add memory, retrieval/RAG, embeddings, vector/key-value/object/graph stores, loaders, datahubs, or datasets | [sub-skills/memory-rag-and-data/SKILL.md](sub-skills/memory-rag-and-data/SKILL.md) |
| Generate synthetic data, use data collectors, run verifiers/environments, or plan CAMEL benchmarks | [sub-skills/datagen-evaluation-and-benchmarks/SKILL.md](sub-skills/datagen-evaluation-and-benchmarks/SKILL.md) |

## Cross-Cutting References

- [references/package-overview.md](references/package-overview.md) summarizes package surfaces, optional extras, and support modules such as prompts, personas, schemas, responses, caches, parsers, configs, and utilities.
- [references/troubleshooting.md](references/troubleshooting.md) covers install/import failures, optional dependencies, credentials, data/config validation, and workflow-specific escalation.
- [references/repo-provenance.md](references/repo-provenance.md) records the source commit, package version, evidence paths, and dirty-state baseline used to create this skill.
- [references/repo-routing-metadata.json](references/repo-routing-metadata.json) is structured metadata for the managed `repo-skills-router` import process.

## Safety And Scope

- Start with credential-free inspection scripts and constructor/signature checks before calling models, services, datasets, browsers, Docker, or remote vector stores.
- Do not install `camel-ai[all]` by default in automated environments; select extras by workflow to avoid heavyweight or unsupported optional dependencies.
- Treat source examples and native tests as evidence; this skill is self-contained and does not require the original repository checkout at runtime.
- Keep API keys, service URLs with secrets, OAuth tokens, model credentials, and local data paths outside generated prompts and skill files.
