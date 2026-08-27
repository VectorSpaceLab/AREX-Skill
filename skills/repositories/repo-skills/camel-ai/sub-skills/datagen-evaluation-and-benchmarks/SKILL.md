---
name: datagen-evaluation-and-benchmarks
description: "Use CAMEL-AI synthetic data generation, data collectors, datasets,
  verifiers, environments, and benchmark wrappers while separating deterministic
  checks from model-, dataset-, and credential-heavy evaluation runs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# CAMEL Datagen, Evaluation, and Benchmarks

Use this sub-skill when a task involves CAMEL synthetic data generation, dataset wrappers, data collectors, verifier-backed evaluation, environment rollouts, or benchmark wrappers.

## Route By Task

- For API signatures, object contracts, and safe local probes, read [references/api-reference.md](references/api-reference.md) and run [scripts/inspect_eval_components.py](scripts/inspect_eval_components.py).
- For CoT, self-instruct, evol-instruct, Source2Synth, collectors, datasets, and verifier-backed task loops, read [references/workflows.md](references/workflows.md).
- For GAIA, APIBank, APIBench, Nexus, BrowseComp, and RAGBench evaluation planning, read [references/benchmarks.md](references/benchmarks.md).
- For optional dependencies, credentials, schema failures, unsafe code execution, environment contracts, and long-running generation recovery, read [references/troubleshooting.md](references/troubleshooting.md).

## Boundaries

- Covers `camel.datagen`, `camel.data_collectors`, `camel.datasets`, `camel.benchmarks`, `camel.verifiers`, `camel.extractors`, `camel.environments`, and task-generation/evaluation examples.
- Cross-link to sibling model/agent skills for `ChatAgent`, `RolePlaying`, `Workforce`, model backend, and provider configuration details.
- Cross-link to sibling memory/RAG/storage skills for vector stores, retrievers, embeddings, and persistent storage details.
- Treat source repo examples and benchmarks as evidence; do not require the original checkout at runtime.

## Safety Defaults

- Prefer no-network local validation first: import checks, extractor normalization, small schema validation, tiny static datasets, and environment reset/step smoke tests.
- Treat data generation and benchmark `run()` calls as potentially expensive because they usually call models, download datasets, or require API keys.
- Keep generated outputs resumable: write JSON/JSONL checkpoints, include deterministic seeds, track processed input IDs, and rerun only failed records.
