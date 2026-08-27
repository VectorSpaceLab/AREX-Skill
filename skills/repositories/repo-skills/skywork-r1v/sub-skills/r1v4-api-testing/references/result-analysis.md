# Result Analysis

## Prefer the safe path first

Use the bundled helpers for everyday inspection:

- `scripts/summarize_results.py` for batch-level counts.
- `scripts/parse_r1v4_response.py` for tagged response inspection.

The source repository also includes an interactive Flask viewer. This sub-skill does **not** bundle that full UI because it is browser-driven, path-sensitive, and easy to misuse in automated workflows. Use the non-interactive helper unless you specifically need a local exploratory UI.

## What each helper answers

| Helper | Best for | Output |
| --- | --- | --- |
| `summarize_results.py` | Quick health check on a result JSONL | Total, success, error, with-image, text-only, and average response length. |
| `parse_r1v4_response.py` | Inspect one response, one file, or one JSONL | Parsed tagged content plus per-round statistics. |
| `validate_cases.py` | Confirm the input file is usable before calling the API | Schema errors and optional image-path failures. |
| `build_api_payload.py` | Inspect the exact request body before a live call | OpenAI-compatible request JSON with no network access. |

## Typical headless workflow

```bash
python scripts/validate_cases.py --input test_cases.jsonl --check-images
python scripts/build_api_payload.py --image ./demo_image/demo_1.png --question '问题内容' --model skywork/r1v4-lite --stream false --enable-search false
python scripts/parse_r1v4_response.py --text '<think>...</think><answer>...</answer>'
python scripts/summarize_results.py --input result_nonstream.jsonl
```

## How the summary helper counts results

The summary helper treats a record as successful when the response block has a non-empty `full_response` and no `error` field.

It also counts:

- `with-image`: records with a non-empty `image` field.
- `text-only`: records with an empty or missing `image` field.
- `average response length`: average character count of `full_response` values when present.

That makes the helper useful for quick comparisons between:

- 非流式 vs 流式 runs.
- Regular model vs 规划器 runs.
- Image-heavy and text-only subsets.

## What the parser exposes

The parser keeps the information needed for trace-level review:

- raw tagged strings for each round,
- parsed JSON for tool calls and observations when valid,
- parse errors when JSON is malformed,
- the final answer text,
- per-round tool-name statistics when available.

## Visualizer guidance

If the viewer path or image display is broken in a local environment:

1. Confirm the result file itself is valid JSONL.
2. Confirm the image field points to a file that exists relative to the case file or current directory.
3. Fall back to `summarize_results.py` and `parse_r1v4_response.py` for headless inspection.
4. Only rebuild a local browser UI if you truly need point-and-click browsing of many records.

## Output hygiene

- Do not place API keys in result files.
- Do not rely on browser state for batch analysis.
- Keep the summary helper as the default inspection route for automation.
