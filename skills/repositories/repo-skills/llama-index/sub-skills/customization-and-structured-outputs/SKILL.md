---
name: customization-and-structured-outputs
description: "Customize LlamaIndex Settings, prompts, callbacks,
  instrumentation, evaluation signals, and Pydantic structured outputs without
  relying on external APIs during local checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Customization and Structured Outputs

## Use This Sub-Skill When

- You need to configure `Settings.llm`, `Settings.embed_model`, `Settings.node_parser`, `Settings.transformations`, `Settings.callback_manager`, tokenizer, chunk sizes, or prompt helpers.
- You need custom `PromptTemplate` or `ChatPromptTemplate` behavior, prompt inspection, prompt updates, or output-parser formatting instructions.
- You need Pydantic structured output through `PydanticOutputParser`, `LLMTextCompletionProgram`, `llm.as_structured_llm(...)`, or `get_response_synthesizer(output_cls=...)`.
- You need callbacks, instrumentation, token counting, or evaluator result shapes to debug query behavior.
- You need deterministic tests using `MockLLM` and `MockEmbedding` while avoiding external provider calls.

## Route Elsewhere

- Use `../indexing-and-querying/` for index construction, retrievers, query engines, node parsing as part of ingestion, and response modes in normal RAG flows.
- Use `../integrations-and-storage/` for provider packages, credentials, vector stores, readers, and external backend setup.
- Use `../agents-and-workflows/` for `AgentWorkflow`, `FunctionAgent`, `ReActAgent`, handoffs, tools, and agent orchestration; return here for schemas, parsers, prompts, and structured-output validation.

## Core Workflow

1. Decide scope: prefer per-object constructor arguments (`llm=`, `embed_model=`, `callback_manager=`, prompt templates) when isolation matters; use global `Settings` only for app-wide defaults.
2. For tests, set `Settings.llm = MockLLM(...)` and `Settings.embed_model = MockEmbedding(embed_dim=...)`, then restore prior `Settings` fields after the test.
3. Customize prompts with `PromptTemplate`, `ChatPromptTemplate`, `partial_format`, `template_var_mappings`, `function_mappings`, or component prompt APIs such as `get_prompts()` / `update_prompts()`.
4. Add structured outputs with a Pydantic model, then choose the surface: parser-attached prompt, `LLMTextCompletionProgram.from_defaults`, structured LLM wrapper, or response synthesizer `output_cls`.
5. Add callbacks or instrumentation before constructing the component that should emit events, then verify events with a local query or explicit callback-manager context.
6. Evaluate with evaluator classes that return `EvaluationResult` fields (`query`, `contexts`, `response`, `passing`, `score`, `feedback`, invalid metadata), making sure input shapes match the evaluator.

## Bundled References

- `references/customization-recipes.md` contains copy-adapt recipes for Settings isolation, prompts, structured outputs, callbacks, instrumentation, and evaluation.
- `references/api-reference.md` summarizes verified import paths, signatures, and object responsibilities for this sub-skill.
- `references/troubleshooting.md` maps common customization and structured-output failures to targeted fixes.
- `scripts/inspect_settings_and_prompts.py` prints Settings, prompt, parser, callback, evaluator, and mock-model checks without requiring external APIs.

## Safety Notes

- Avoid deprecated `ServiceContext`; current code uses `Settings` and explicit constructor arguments.
- Never let global `Settings` mutations leak between tests; snapshot and restore modified attributes.
- Do not hard-code provider API keys in skill examples; provider installation and credentials are integration concerns.
- Treat Pydantic validation errors as schema/prompt/model-contract feedback, not as retriever failures.
