---
name: adalflow
description: "Use AdalFlow to build, debug, evaluate, optimize, trace, and
  operate LLM task pipelines, RAG systems, agents, tools, and structured-output
  workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# AdalFlow Repo Skill

Use this skill when a task involves the AdalFlow Python package: building model-agnostic LLM task pipelines, structured outputs, RAG, agents, tool calling, evaluation, prompt/few-shot/text-gradient optimization, or tracing.

AdalFlow uses PyTorch-like `Component` building blocks. A typical workflow combines `Prompt`, `ModelClient`, `Generator`, `DataClass`/parser objects, retrievers, tools, agents, metrics, and tracing callbacks.

## First checks

1. Read [repository provenance](references/repo-provenance.md) before assuming this skill is current for a checkout.
2. For a package install/import task, read [package overview](references/package-overview.md) and [root troubleshooting](references/troubleshooting.md).
3. For a quick environment smoke, run [check_adalflow_environment.py](scripts/check_adalflow_environment.py) in the target Python environment.
4. Then route to the most specific sub-skill below.

## Install/import guidance

For AdalFlow 1.1.1, use Python 3.9+ and include the OpenAI SDK for reliable top-level import because the current `Generator` module imports OpenAI response event types:

```bash
python -m pip install "adalflow[openai]"
python - <<'PY'
import adalflow as adal
print(adal.__version__)
from adalflow import Component, DataClass, Generator, Agent, Runner
print("adalflow import ok")
PY
```

Install additional extras only for workflows that need them, such as provider SDKs, FAISS/LanceDB/Postgres/Qdrant retrieval, MCP, torch/transformers, datasets, or SQLAlchemy. Do not treat a missing API key, service, dataset, or accelerator as a base package failure.

## Route map

### Core components and structured I/O

Read [core-components-and-structured-io](sub-skills/core-components-and-structured-io/SKILL.md) for:

- `Component`, `DataComponent`, `Sequential`, `ComponentList`, `Prompt`, `DataClass`, and `required_field`.
- JSON/YAML/list/int/float/bool parsers and `DataClassParser` structured-output prompts.
- Service-free mini-pipeline checks that do not call a model provider.

### Model clients, generators, and embedders

Read [model-client-and-generator-workflows](sub-skills/model-client-and-generator-workflows/SKILL.md) for:

- `ModelClient`, `Generator`, `GeneratorOutput`, `Embedder`, and `BatchEmbedder`.
- `prompt_kwargs`, `model_kwargs`, `ModelType`, output processors, cache behavior, and async/streaming basics.
- Provider extras and no-credential fake-client tests.

### Retrieval, RAG, and data pipelines

Read [retrieval-rag-and-data-pipelines](sub-skills/retrieval-rag-and-data-pipelines/SKILL.md) for:

- `Document`, `TextSplitter`, `LocalDB`, `ToEmbeddings`, and `RetrieverOutputToContextStr`.
- `BM25Retriever`, `FAISSRetriever`, LanceDB, Postgres, Qdrant, and RAG context assembly.
- Optional vector-store, embedding-dimension, stale-index, and service troubleshooting.

### Agents, tools, streaming, HITL, and MCP

Read [agents-tools-and-streaming](sub-skills/agents-tools-and-streaming/SKILL.md) for:

- `FunctionTool`, `ToolManager`, `FunctionDefinition`, `FunctionOutput`, and `ToolOutput`.
- `Agent`, `Runner`, `ReActAgent`, `RunnerResult`, `StepOutput`, and stream events.
- Human approval/permission handlers, safe tool patterns, and optional MCP tools.

### Evaluation and optimization

Read [evaluation-and-optimization](sub-skills/evaluation-and-optimization/SKILL.md) for:

- `AnswerMatchAcc`, `RetrieverEvaluator`, cautious `LLMasJudge`, and dataset loaders.
- `Parameter`, `GradComponent`, `AdalComponent`, `Trainer`, `BootstrapFewShot`, `TGDOptimizer`, `EvalFnToTextLoss`, `LLMAsTextLoss`, and `optimize_anything`.
- Training/benchmark workflows that require provider credentials, data, and runtime budget.

### Tracing, observability, and configuration

Read [tracing-observability-and-configuration](sub-skills/tracing-observability-and-configuration/SKILL.md) for:

- `setup_env`, logging helpers, config loading, and default artifact roots.
- `GeneratorStateLogger`, `GeneratorCallLogger`, callbacks, spans, trace providers, and optional MLflow.
- Debug artifacts, path hygiene, and trace/log troubleshooting.

## Cross-workflow rules

- Start service-free when possible: validate `DataClass`, parser, `TextSplitter`, metrics, fake `ModelClient`, or fake `Runner` behavior before adding providers.
- Choose provider extras only after the required `ModelClient` is known. API credentials and network calls are workflow prerequisites, not skill smoke checks.
- For RAG, separate data preparation, retrieval index construction, context formatting, generator configuration, evaluation metrics, and tracing; each has a different owner sub-skill.
- For agents, verify tools independently with `FunctionTool`/`ToolManager` before letting an LLM planner call them.
- For optimization, define evaluation and loss contracts before running `Trainer.fit`; prefer `Trainer.diagnose` or metric smokes before expensive training.
- For tracing/logging, keep artifacts in explicit writable directories and avoid logging secrets, provider payloads, or machine-specific paths.

## When not to use this skill

- The task is only about editing this repository's release process, CI, or publishing scripts.
- The task needs a different package's APIs and only mentions AdalFlow as background context.
- The user asks Creator to perform downstream research directly; switch to Researcher mode instead of using this operating graph here.
