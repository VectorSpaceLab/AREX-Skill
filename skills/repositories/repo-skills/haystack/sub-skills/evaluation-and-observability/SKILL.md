---
name: evaluation-and-observability
description: "Evaluate Haystack retrieval, answers, and pipelines, and
  instrument applications with tracing, logging, telemetry control, and
  diagnostic outputs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Evaluation and Observability

Use this sub-skill when the task is about measuring Haystack output quality or diagnosing runtime behavior: retrieval and answer evaluators, evaluation reports, trace spans, logging output, pipeline debug output, and telemetry opt-out.

## Route here

- Score retrieved `Document` lists with recall, MRR, MAP, or NDCG and interpret aggregate versus per-query metrics.
- Score answer strings with exact match, SAS, faithfulness, context relevance, or a custom `LLMEvaluator`.
- Build an evaluation pipeline or wrap evaluator outputs in `EvaluationRunResult` reports.
- Add `LoggingTracer`, OpenTelemetry, Datadog, or a custom tracer to inspect component and pipeline execution.
- Enable local pipeline debug outputs, structured logging, or content tracing while avoiding sensitive-data leakage.
- Disable Haystack telemetry or auto tracing for privacy-sensitive applications.

## Reroute

- Build RAG pipelines, document stores, retrievers, rankers, readers, or prompt-to-answer flow: use `../retrieval-and-rag/SKILL.md`.
- Configure provider generators, model credentials, prompt builders, or chat/message APIs: use `../generation-and-model-components/SKILL.md`.
- Create custom components, connect pipeline sockets, serialize pipelines, or use `Pipeline`/`AsyncPipeline` mechanics: use `../pipelines-and-components/SKILL.md`.
- Run repository tests, Hatch commands, release notes, or contributor workflows: use the repo-development route if it is present in the generated skill.

## Start fast

1. Choose metric family: retrieval metrics compare expected versus retrieved `Document` objects; answer metrics compare expected versus predicted answers; LLM evaluators judge faithfulness, context relevance, or custom rubric outputs.
2. Keep every evaluator input list aligned by sample count; most evaluator failures are length mismatches or nested-list shape mistakes.
3. Use statistical evaluators first for deterministic checks, then add LLM evaluators only when credentials and JSON-mode generator behavior are available.
4. Wrap evaluator outputs with `EvaluationRunResult(run_name=..., inputs=..., results=...)` to produce `aggregated_report()` and `detailed_report()` dictionaries, CSV files, or dataframes.
5. For diagnostics, start with `LoggingTracer` and `logging.getLogger("haystack").setLevel(logging.DEBUG)` before adding network tracing backends.
6. Treat content tracing as sensitive: enable `tracing.tracer.is_content_tracing_enabled = True` only for local debugging or sanitized data.

Run the bundled smoke check from this sub-skill directory to validate deterministic evaluator and logging-tracer behavior without network credentials:

```bash
python scripts/evaluation_smoke_check.py
```

If working in the Haystack repository checkout, follow the repository’s Hatch policy for execution, for example:

```bash
hatch -e test run python skills/disco/haystack/sub-skills/evaluation-and-observability/scripts/evaluation_smoke_check.py
```

## References

- `references/api-reference.md` lists evaluator imports, inputs, outputs, report APIs, tracing APIs, logging controls, and telemetry switches.
- `references/workflows.md` gives copyable workflows for retrieval evaluation, answer evaluation, LLM evaluation, reporting, tracing, pipeline debug output, and privacy-safe observability.
- `references/troubleshooting.md` maps install/import, optional dependency, credential/backend, API misuse, data/config, and workflow failures to checks and fixes.
