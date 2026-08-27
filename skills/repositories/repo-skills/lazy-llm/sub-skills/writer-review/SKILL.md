---
name: writer-review
description: "Guides LazyLLM writer artifact models, writer tools,
  revision/stream workflows, Feishu adapter boundaries, and review CLI
  planning."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# LazyLLM Writer and Review

Use this sub-skill for LazyLLM writer workflows, writer intermediate representation (IR), artifact JSON envelopes, writer tools, revision/stream utilities, Feishu adapter boundaries, `lazyllm review`, `review-local`, and git review examples.

## Start here when

- The task mentions writer data models such as `WriterDocument`, `WriterBlock`, `WriterSpan`, `WritingContext`, or `ResourceProfile`.
- The user wants to run or adapt writer tools, revision tools, stream tools, or a writer pipeline.
- The task involves Feishu document bindings, provider payloads, or local artifact stores.
- The user wants to plan LazyLLM PR review commands or local code-review output without posting remotely.

## Files to read

- [writer-review-workflows.md](references/writer-review-workflows.md) for local writer artifact, tool, and review command workflows.
- [artifact-formats.md](references/artifact-formats.md) for writer IR fields and artifact envelope expectations.
- [troubleshooting.md](references/troubleshooting.md) for artifact, provider adapter, review CLI, and posting failures.
- [scripts/writer_artifact_smoke.py](scripts/writer_artifact_smoke.py) for a no-network artifact round-trip check.

## Safe workflow

1. **Start with local artifacts.** Build a tiny `WriterDocument` and `WritingContext`; round-trip them through JSON before using provider adapters.
2. **Keep provider bindings as metadata.** `provider_binding` and `provider_payload` should be preserved but not dereferenced unless the user supplies provider access.
3. **Validate tool outputs.** Writer tools should return artifact paths, context paths, schema names, counts, and summaries that downstream steps can inspect.
4. **Treat review commands as side-effecting.** `lazyllm review` may post or call providers; `review-local` can inspect git state and write reports. Ask before posting remote comments.
5. **Route LLM/provider configuration** to [model-deployment](../model-deployment/SKILL.md) when a writer pipeline calls an online model.

## Key local facts

LazyLLM writer tests verify:

- nested `WriterDocument`/`WriterBlock`/`WriterSpan` fields survive JSON round trips,
- `iter_blocks()` traverses depth-first and `block_by_id()` finds nested blocks,
- artifact envelopes contain `schema`, `schema_version`, `data`, and `meta`,
- `save_artifact_json` / `load_artifact_json` support models and lists,
- `WriterToolBase._save_artifacts` records primary artifact path, context path, schema names, counts, and metadata,
- writer adapter, revision, stream, and tool tests are mostly local; provider-backed writer pipeline is optional.

## Review CLI boundaries

Use review workflows for planning and local output unless the user explicitly asks to post:

```text
lazyllm review --pr <number> [--repo owner/name] [--model ...] [--post] ...
lazyllm review-local [--repo-path .] [--base main] [--output review.json] ...
```

Do not post comments, call a provider, or inspect private repositories without user approval and credentials.

## Handoff checklist

When you finish a writer/review task, include:

- artifact schema and file paths created or expected,
- whether provider bindings are preserved or used,
- local round-trip/tool smoke result,
- review command plan and side-effect status,
- model/provider/backend status if a writer pipeline uses an LLM.
