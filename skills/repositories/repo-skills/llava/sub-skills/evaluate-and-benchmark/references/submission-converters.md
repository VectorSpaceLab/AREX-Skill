# Submission Converters

## When to read

Read this when a benchmark expects a submission file rather than raw model answers.

## Common answer file shape

A typical LLaVA answer JSONL row contains fields such as:

- `question_id`
- `prompt`
- `text`
- `answer_id`
- `model_id`
- `metadata`

Benchmark-specific modules may add `options`, `option_char`, and `round_id`.

## Bundled converter guidance

### VQAv2

Use the VQAv2 submission converter after merging chunked answers.

### MMBench

The repo's MMBench converter writes an Excel upload file. This depends on `pandas` and `openpyxl`.

### SEED and VizWiz

The benchmark shells and converters prepare upload artifacts or result files after inference.

### Q-Bench / Chinese Q-Bench

Use the dataset-specific JSON and image directories, then convert to the expected answer upload file.

## GPT review scripts

The review scripts for LLaVA-Bench and related judging flows require:

- network access
- an OpenAI-compatible Python package
- valid credentials
- tolerance for rate limits and retries

Treat those as optional, external judge workflows. Do not present them as basic local verification.

## Safe sequence

1. Run the benchmark inference.
2. Validate the answer JSONL with the bundled helper.
3. Run the converter.
4. Inspect the generated upload artifact.
5. Only then submit if the user has the necessary external account or server access.
