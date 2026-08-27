# Evaluation troubleshooting

## Install and import

- `ModuleNotFoundError: openai`: install the project's declared OpenAI client
  in the prepared environment, then verify its version is compatible with the
  legacy `openai.ChatCompletion.create` interface used by this evaluator.
  Do not put a key in the package or result file.
- `ModuleNotFoundError: nltk`, `rouge`, or `sentence_transformers`: the
  traditional path has optional-but-required runtime packages beyond the core
  model run. Install them in the evaluation environment and verify imports
  before a benchmark-sized run.
- `nltk.download('wordnet')` runs at import time. A restricted network or
  unwritable NLTK cache can stop the traditional evaluator before scoring.
- The inspected reference environment is Python 3.10 with torch 2.0.1+cu117,
  CUDA on an A100 40GB (capability 8.0), transformers 4.28.0.dev0 at commit
  `cae78c46`, tokenizers 0.12.1, and PointLLM 0.1.2. Keep evaluation in that
  compatible environment rather than mixing system Python packages.

## Dependencies and backends

- Generation uses CUDA model inference and is outside this sub-skill's local
  no-model check. A missing GPU, incompatible torch/CUDA build, or checkpoint
  dtype issue must be handled by the inference sibling.
- Traditional scoring downloads `all-mpnet-base-v2` and
  `princeton-nlp/sup-simcse-roberta-large`; a cache miss requires network and
  disk space. Do not call it a pure local smoke test.
- If OpenAI calls fail with authentication, billing, entitlement, quota, or
  deprecated-model errors, stop and fix the credential/account/model choice.
  Retries do not make a bad credential valid.
- Rate limits, service-unavailable, and timeout errors receive exponential
  backoff (up to the evaluator's retry limit). Reduce `--num_workers` before
  spending the remaining budget.

## Data and configuration

- A result with no `prompt`, no `results` array, or missing row fields is an
  inference failure. Re-run generation or repair upstream annotations; do not
  fabricate ground truth in the judge input.
- Objaverse task/prompt mismatch is only warned about by generation. Reject
  classification with prompt 2 and captioning with prompt 0/1 during review.
- ModelNet requires exactly the known 40-category ordering and integer labels.
  Keep shuffle false; otherwise object IDs and labels can silently misalign.
- Duplicate object IDs break resume semantics because processed IDs are removed
  by set-like filtering. Validate before scoring.

## API, parsing, and cost

- The judge expects `T`/`F`, `index#class#reason`, or `score#reason` depending
  on eval type. The parser is permissive about surrounding text but not about
  the final semantic value. Preserve `gpt_reason` for audit.
- Open classification invalids are counted and excluded from that evaluator's
  saved accuracy denominator. Close-set invalids are randomly assigned a class;
  report headline accuracy, clean accuracy, invalid count, and invalid-correct
  count together.
- Caption invalid scores are `-1` and excluded from `average_score`. A zero is
  a valid judge score and must not be treated as invalid.
- `GPT_cost` uses source hard-coded historical per-1K token prices. Treat it as
  an estimate; calculate a fresh budget using current provider pricing before
  running a large set.
- If a final output already exists, the CLI exits instead of overwriting it.
  Choose a new output directory/name after confirming the source artifact.

## Resume and workflow failures

- On interruption or exception, confirm that `_processed_temp.json` exists and
  is valid JSON. Re-run the same evaluator command to resume by `object_id`.
- Do not delete a temp file until the final output is complete and independently
  validated. If it is corrupt, restore from the original inference JSON and
  start a fresh output name; do not merge partial counters by hand.
- Parallel output order is nondeterministic. Compare rows by `object_id`, not
  list position.
- For traditional scoring, an empty generated caption is internally replaced
  by `##`; record that this is source behavior when interpreting zeros.
- If validation fails after scoring, retain the raw output and use the reported
  field path to decide whether the issue is a source/runtime defect or a bad
  upstream result. Full benchmarks and live API recovery are intentionally not
  part of the bundled verification.
