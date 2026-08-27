---
name: pipeline-foundations
description: "Build and debug DataFlow operator, pipeline, storage, prompt, and
  wrapper foundations."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# pipeline-foundations

Use this sub-skill when a task needs the DataFlow core mechanics: custom `OperatorABC` classes, `PipelineABC` subclasses, compile-time key validation, storage/cache steps, prompt-template restrictions, `draw_graph`, or offline non-LLM smoke checks.

## Load order

1. Read `references/api-reference.md` for the public classes, constructor parameters, and operator/pipeline contracts.
2. Read `references/storage-and-data-formats.md` before choosing `FileStorage`, `LazyFileStorage`, batched storage, or database-backed storage.
3. Read `references/pipeline-patterns.md` when implementing or debugging a pipeline skeleton.
4. Read `references/troubleshooting.md` when compile errors, missing keys, storage step errors, prompt type errors, graph rendering, wrappers, or non-TTY diagnostics fail.
5. Use `scripts/smoke_pipeline_foundations.py` to prove a tiny offline custom-operator pipeline.
6. Use `scripts/validate_tabular_input.py` before running operators that require specific columns.

## Scope

This sub-skill covers:

- `PipelineABC`, `BatchedPipelineABC`, and `StreamBatchedPipelineABC` compile and forward behavior.
- `OperatorABC.run(storage, input_*, output_*)` conventions and compile-time key matching.
- `FileStorage`, `LazyFileStorage`, `DummyStorage`, `BatchedFileStorage`, `StreamBatchedFileStorage`, and `MyScaleDBStorage` selection.
- `prompt_restrict`, `PromptABC`, and `DIYPromptABC` prompt-template guardrails.
- `BatchWrapper` and non-LLM foundation smoke patterns.
- `draw_graph(port=0, hide_no_changed_keys=True)` usage and dependency caveats.

## Routing boundaries

- Route API keys, local model serving, OpenAI-compatible endpoints, WebUI, and CLI command choices to the `serving-cli` sub-skill.
- Route text-specific, document-specific, vision, RAG, and operator-catalog workflow assembly to the `text-workflows` or `document-vision-rag` sub-skills.
- Route Ray actor wrapping, distributed execution, and GPU resource allocation to the `rayorch-acceleration` sub-skill.
- Stay here for generic pipeline shape, storage semantics, column validation, and offline reproducibility.

## Fast operating rules

- Always call `pipeline.compile()` once before `pipeline.forward()` on a `PipelineABC` subclass.
- In a pipeline `forward`, call `self.some_operator.run(storage=self.storage.step(), input_key="existing_column", output_key="new_column")` or the equivalent positional storage form.
- Treat `storage.step()` as the step boundary: step 0 reads the first input file; operator output is written to the next step cache file.
- Use `input_*` parameters only for columns that already exist in the input data or were produced by earlier operators. Use `output_*` for columns the operator writes.
- Compile failures mentioning `Key Matching Error` are usually schema or `input_*` typos, not model failures.
- Prefer `FileStorage` for deterministic offline smoke tests; avoid `hf:` and `ms:` sources unless the workflow is allowed to use network access.
