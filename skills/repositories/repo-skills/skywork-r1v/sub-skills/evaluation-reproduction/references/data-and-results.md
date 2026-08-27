# Data and result formats

This reference summarizes the main input and output shapes used by the Skywork evaluation flows.

## VLMEvalKit inputs

### Common command inputs

- `--data`: one or more dataset names
- `--model`: one or more model names
- `--config`: an alternate JSON config that supplies both model and data blocks
- `--work-dir`: output root
- `--mode`: `all` or `infer`
- `--api-nproc`: parallel API calls
- `--retry`: retry count for API-backed model calls
- `--judge`: explicit judge model name
- `--reuse` and `--reuse-aux`: reuse prior artifacts
- `--use-vllm`: enable vLLM-backed model classes when supported

### Skywork-specific environment variables

- `LMDEPLOY_API_KEY`
- `LMDEPLOY_API_BASE`
- `USE_COT`

## VLMEvalKit outputs

The stock Skywork flow writes evaluation outputs under `./outputs/Skywork-R1V3/`.

Common patterns include:

- model-specific subdirectories for predictions and summaries
- xlsx files for benchmark outputs
- follow-up rule-based files for benchmarks that need post-processing

## R1V4 inputs and outputs

### Input schema

`r1v4/test_cases.jsonl` is line-delimited JSON. Each record contains:

- `image`: a string path or an empty string
- `question`: a non-empty question string

### Request payload shape

The batch payloads use OpenAI-compatible chat-completions JSON with:

- `messages`: a list with one user message
- `content`: an ordered list where image content comes before text content
- `model`: either `skywork/r1v4-lite` or `skywork/r1v4-vl-planner-lite`
- `stream`: boolean
- `enable_search`: boolean

### Result schema

The batch scripts write JSONL lines with:

- `image`
- `question`
- `response`

The `response` block usually contains:

- `full_response`
- `raw_response`
- or an `error` field if the call failed

The parser helper can also return:

- `rounds`
- `final_round`
- `tag_counts`
- `parse_errors`

## EMMA results

`generate_response.py` writes a JSON object keyed by problem id. Each problem entry usually contains:

- the built prompt fields
- `response`
- or `error`

The evaluation helpers write a cleaned result JSON and an accuracy summary companion.

## MMK12 results

`evaluate.py` writes a JSON object keyed by problem id into the configured output directory.

`calculate_score.py` reads that JSON, adds per-item `score` annotations, and writes:

- an annotated JSON file with `_extract.json` suffix
- a summary file with `_score.json` suffix

## Boxed-answer scoring

The rule-based scorer operates on records that expose:

- `prediction` or `response`
- `answer`
- optionally `id` for val-only filtering
- optionally `hit` for fallback scoring

It uses the last `\boxed{...}` match when present and normalizes simple math wrappers before comparing to the reference answer.
