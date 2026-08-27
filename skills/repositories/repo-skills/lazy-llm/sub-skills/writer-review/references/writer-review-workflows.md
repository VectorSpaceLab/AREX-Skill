# Writer and Review Workflows

## Local writer artifact workflow

1. Create or load `WritingContext` and `WriterDocument`.
2. Represent structure with `WriterBlock` nodes and optional `WriterSpan` inline spans.
3. Preserve provider fields as metadata:
   - `provider_binding` for external IDs such as Feishu document/block IDs,
   - `provider_payload` for raw provider data needed by adapters.
4. Save artifacts using LazyLLM writer utilities or `WriterToolBase`.
5. Validate envelope metadata before handing artifacts to the next tool.

Safe check:

```bash
python scripts/writer_artifact_smoke.py
```

## Writer tool workflow

`WriterToolBase` can save multiple artifacts and produce a `ToolResult` with paths and metadata. A robust tool chain should record:

- primary document artifact path,
- context artifact path,
- schema names for document/context/resource profile lists,
- step name and summary,
- counts for blocks/resources/changes,
- any provider binding preserved from input artifacts.

Do not rely on in-memory writer objects across tool boundaries; use artifact paths or serialized envelopes.

## Revision and stream workflows

Revision and stream tools operate on writer artifacts and may produce incremental changes. Use local fixtures first:

- one short document,
- one context object,
- one revision/stream operation,
- explicit expected block ID/content changes.

Only connect provider adapters after local artifact changes are correct.

## Feishu/provider adapter boundaries

Provider adapters may require credentials and remote document IDs. Keep adapter fields in artifacts but avoid remote calls unless the user supplies access and asks for it. For local planning, verify that provider-binding fields survive round trips.

## Review command planning

The CLI exposes two review command families:

- `lazyllm review ...` for PR-based review workflows; can post to remote systems when `--post` or equivalent options are used.
- `lazyllm review-local ...` for local repository review output; can inspect git state and write output files.

Before running either, classify:

- whether a provider/LLM model is required,
- whether the command posts remotely,
- target repo/PR/base branch/output path,
- credential availability,
- desired output format and retention.

## Combining with agents and flows

Writer tools can be exposed as tools through agents-tools or composed in flows. Validate writer artifact contracts first, then route orchestration to flow-orchestration or tool schema/sandbox concerns to agents-tools.
