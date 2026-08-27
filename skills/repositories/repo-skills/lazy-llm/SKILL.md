---
name: lazy-llm
description: "Guides LazyLLM low-code LLM application workflows including
  modules, flows, RAG, agents, tools, writer review, CLI, and deployment."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# LazyLLM Repo Skill

Use this skill when a task asks how to build, debug, test, or adapt **LazyLLM** applications: low-code LLM modules, composable flows, RAG/document pipelines, agents/tools/MCP, writer/review workflows, model deployment, online providers, or the `lazyllm` CLI.

## First actions for any LazyLLM task

1. Read [Repository provenance](references/repo-provenance.md) if you need to decide whether this skill matches a current checkout or whether a refresh is required.
2. Pick the focused sub-skill from the route map below before opening details.
3. Check dependency class early. Base LazyLLM imports do not include every optional RAG, agent, model-serving, multimodal, tracing, or provider dependency.
4. Prefer the bundled diagnostic scripts over ad hoc probes:
   - [scripts/check_lazyllm_env.py](scripts/check_lazyllm_env.py) verifies importability, optional workflow groups, and safe CLI availability.
   - [scripts/inspect_lazyllm_surface.py](scripts/inspect_lazyllm_surface.py) prints verified signatures for the main public APIs without running models or network calls.
5. Never assume a model, provider key, vector database, parser service, Kubernetes/Slurm cluster, npm MCP server, or GPU backend is available unless the user explicitly provided it.

## Route map

| User task or signal | Read this |
| --- | --- |
| Install LazyLLM, inspect extras, use `lazyllm` CLI, configure `lazyllm.config`, launcher/service basics, components/prompters, package import failures | [core-runtime](sub-skills/core-runtime/SKILL.md) |
| Use `TrainableModule`, `OnlineModule`, `OnlineChatModule`, `ServerModule`, deploy/fine-tune models, choose local vs online vs multimodal backend, diagnose provider/model type behavior | [model-deployment](sub-skills/model-deployment/SKILL.md) |
| Compose `pipeline`, `parallel`, `diverter`, `switch`, `ifs`, `loop`, `bind`, or traceable application graphs | [flow-orchestration](sub-skills/flow-orchestration/SKILL.md) |
| Build RAG/document workflows with `Document`, `DocNode`, readers, transforms, retrievers, rerankers, BM25, vector stores, parser service, Milvus/OpenSearch | [rag-document-processing](sub-skills/rag-document-processing/SKILL.md) |
| Register function-call tools, use `ToolManager`, build React/ReWOO/PlanAndSolve agents, use sandbox flags, SQL/HTTP/search tools, SkillManager, MCP | [agents-tools](sub-skills/agents-tools/SKILL.md) |
| Use writer IR/artifacts, writer tools, revision/stream utilities, Feishu adapter boundaries, `lazyllm review` or local review workflows | [writer-review](sub-skills/writer-review/SKILL.md) |

## Installation and extras quick guide

Read [Installation and optional extras](references/installation-and-extras.md) for the full matrix. Typical choices:

```bash
python -m pip install lazyllm
lazyllm install rag              # document/RAG imports
lazyllm install agent-advanced   # MCP/advanced agent dependencies
lazyllm install standard         # broad app stack; may install heavy model/vector packages
lazyllm install full             # all optional stacks; use only when explicitly needed
```

For a source checkout, use an editable install with a supported Python (`>=3.10,<3.14`) and then install only the extras required by the selected workflow. Do not install `full` just to answer a base CLI/config/flow question.

Minimal no-network smoke check:

```bash
python scripts/check_lazyllm_env.py --require-rag --require-agent --require-writer
```

Run that command from inside this skill directory after copying or locating the script, or pass the script path explicitly from any working directory. It only imports LazyLLM modules and does not call a provider.

## High-signal API surfaces

Read [API surface map](references/api-surface-map.md) when a task names a class/function or when you need exact routing. Verified public entry points include:

- `lazyllm.pipeline`, `parallel`, `diverter`, `switch`, `ifs`, `loop`, `bind`
- `TrainableModule`, `OnlineModule`, `OnlineChatModule`, `ServerModule`, `ActionModule`
- `Document`, `Retriever`, `Reranker`, `DocNode`, BM25 and store/index helpers
- `fc_register`, `ToolManager`, `SkillManager`, `ReactAgent`, `ReWOOAgent`, `PlanAndSolveAgent`
- writer artifact models and `WriterToolBase`
- CLI commands: `install`, `deploy`, `run`, `skills`, `review`, `review-local`

## Backend and safety policy

- **Safe by default**: import checks, config/CLI inspection, flow graphs with Python callables, BM25/local RAG smoke, writer artifact round trips, tool schema registration.
- **Ask or require explicit evidence**: cloud provider calls, model downloads, local GPU serving/fine-tuning, multimodal generation, external vector databases, parser-service workers, MCP servers launched through `npx`/npm, Kubernetes/Slurm/SCO jobs, PR posting.
- **Do not post or mutate remote systems** from review, MCP, Feishu, database, or provider helpers unless the user asks for that side effect and provides credentials.

## Troubleshooting shortcuts

Start with [cross-cutting troubleshooting](references/troubleshooting.md), then the owning sub-skill's troubleshooting file. Common LazyLLM symptoms:

- `ImportError: Missing package(s): ... You can install them by: lazyllm install rag` → read the RAG or install reference; install the exact extra, not `full`, unless the task needs heavy backends.
- `lazyllm --help` exits with a usage error → this CLI prints usage from its dispatcher; use concrete subcommands such as `lazyllm skills list` or inspect the command table in [core-runtime](sub-skills/core-runtime/SKILL.md).
- Provider/API-key errors → route to [model-deployment](sub-skills/model-deployment/SKILL.md) and keep provider tests optional.
- Flow result mismatch → route to [flow-orchestration](sub-skills/flow-orchestration/SKILL.md) and verify `bind`, skip/kept items, and input tuple handling.

## When not to use this skill

Do not use this skill for generic LLM theory, non-LazyLLM frameworks, model architecture research unrelated to LazyLLM modules, or direct production deployment to a user cluster without first checking the model-deployment and core runtime dependency/back-end constraints.
