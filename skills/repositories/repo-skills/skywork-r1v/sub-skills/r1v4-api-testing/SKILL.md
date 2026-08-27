---
name: r1v4-api-testing
description: "Draft, inspect, parse, and summarize Skywork R1V4 API batch tests
  without leaking API keys."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# R1V4 API Testing

Use this sub-skill when you need to prepare Skywork R1V4 API batch tests, dry-run request payloads, parse tagged tool-use responses, summarize result JSONL, or troubleshoot the batch viewer safely.

## Start here

1. Read `references/api-batch-workflows.md` for the four batch modes and Chinese terminology.
2. Check `references/data-formats.md` for `test_cases.jsonl`, request payload, and result JSONL schemas.
3. Validate input cases with `scripts/validate_cases.py` before any API run.
4. Build a no-network payload preview with `scripts/build_api_payload.py`.
5. Parse a tagged response or a result file with `scripts/parse_r1v4_response.py`.
6. Summarize a result JSONL with `scripts/summarize_results.py`.

## Bundled files

- `references/api-batch-workflows.md` — workflow map for `batch_nonstream.py`, `batch_stream.py`, `batch_planner_nonstream.py`, and `batch_planner_stream.py`.
- `references/data-formats.md` — input/output schemas and tagged response grammar.
- `references/result-analysis.md` — safe headless analysis path and visualizer guidance.
- `references/troubleshooting.md` — API, image, stream, parse, and viewer failure modes.
- `scripts/validate_cases.py` — schema and optional image-path validation.
- `scripts/build_api_payload.py` — OpenAI-compatible payload builder with data URL support.
- `scripts/parse_r1v4_response.py` — tagged response parser and JSONL parser CLI.
- `scripts/summarize_results.py` — batch result counters and response-length summary.

## Routing notes

- Use `skywork/r1v4-lite` for the regular batch modes and `skywork/r1v4-vl-planner-lite` for planner batch modes.
- Keep the message order as image first, then text.
- Bundled helpers do not make live API calls by default.
- Leave API keys to env or caller config; do not hard-code them in payloads or scripts.
- Use the bundled summary helper instead of copying the full Flask viewer into a workflow.
- Route local Transformers/vLLM inference, CUDA setup, and model-weight issues to the sibling `local-inference` sub-skill.
- Route VLMEvalKit, EMMA, MMK12, and benchmark reproduction tasks to the sibling `evaluation-reproduction` sub-skill.
