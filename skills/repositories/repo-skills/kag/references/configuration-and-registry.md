# Configuration and Registry Guide

## Purpose

Read this when a KAG task depends on `kag_config.yaml`, dynamic component registration, or understanding which `type` names are valid in a workflow config.

## Configuration discovery

KAG looks for a nearby `kag_config.yaml` by walking up from the current working directory. That means:

- running from the project directory is the safest default
- if a config is missing, an `import kag` can fail because the package initializes config on import
- the bundled install check creates a temporary minimal config so the import can still be tested from any directory

The config loader also supports YAML `!ENV` tags and environment-variable substitution through the normal package loader.

### Cross-cutting environment variables

Common environment variables used by the package include:

- `KAG_PROJECT_ID`
- `KAG_PROJECT_HOST_ADDR`
- `KAG_DEBUG_DUMP_CONFIG`
- `KAG_PROJECT_NAMESPACE`

## Common top-level config areas

The exact shape varies by example, but the most common top-level keys are:

- `project`
- `llm` or `openie_llm` / `chat_llm`
- `vectorize_model` or `vectorizer`
- `kag_builder_pipeline`
- `kag_solver_pipeline`
- `chat`
- `kb`
- `mcp_executor`
- `log`

## Registry rules

KAG uses registry-driven configuration. Most runtime objects are selected by a `type` key and created through `from_config(...)`.

Common registry families include:

- `KAGBuilderChain`
- `ScannerABC`
- `ReaderABC`
- `SplitterABC`
- `ExtractorABC`
- `MappingABC`
- `VectorizerABC`
- `PostProcessorABC`
- `SinkWriterABC`
- `IndexABC`
- `KAGIndexManager`
- `PlannerABC`
- `ExecutorABC`
- `GeneratorABC`
- `SolverPipelineABC`
- `RetrieverABC`

### Component import gotcha

If you add custom components in a project directory, import those modules before calling `from_config(...)`. The examples use `import_modules_from_path(".")` or `import_modules_from_path("./prompt")` for that reason.

## Verified builder and pipeline type names

### Builder chains

- `structured_builder_chain`
- `unstructured_builder_chain`
- `domain_kg_inject_chain`

### Index managers

- `chunk_index`
- `atomic_query_index`
- `table_index`
- `summary_index`
- `outline_index`
- `kag_hybrid_index`

### Solver pipelines

- `index_pipeline`
- `kag_static_pipeline`
- `kag_iterative_pipeline`
- `naive_generation_pipeline`
- `naive_rag_pipeline`
- `self_cognition_pipeline`
- `mcp_pipeline`

## Useful inspection paths

- Use `kag interface --list` to list registered interfaces.
- Use `kag interface --cls <ClassName>` to inspect a single registry family and see valid subclass names.
- Use `scripts/inspect_kag_config.py` to summarize a config file without leaking secrets.
