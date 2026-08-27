# Attacks and Scenarios Troubleshooting

## Branching logic is in the wrong component

Symptoms: a target tries to score, a converter changes behavior based on model responses, or a scenario implements turn-by-turn conversation logic.

Recovery: move response judgment into a scorer; move next-turn logic into an attack/executor; keep scenarios as campaign packagers; keep targets as send/receive adapters.

## Missing target, scorer, dataset, or default

Symptoms: constructor requires `objective_target`, scenario lists no techniques, default scorer is missing, or registry lookup fails.

Recovery: initialize PyRIT with the needed initializers; confirm registry names; route target/scorer setup to `targets-scorers`; route datasets/converters to `converters-datasets`.

## Modality mismatch

Symptoms: attack sends image/audio/video but target or scorer rejects it; converter output type does not match target input.

Recovery: inspect target capabilities, converter output data type, message normalizer behavior, and scorer modality support before running the attack.

## Async or event-loop errors

Symptoms: coroutine was never awaited, event loop already running, notebook execution hangs.

Recovery: use PyRIT async APIs with `await` in notebooks or `asyncio.run()` in scripts; do not nest event loops; keep long-running attack execution outside import/smoke helpers.

## Rate limits or runaway cost

Symptoms: many 429s/timeouts, high token usage, duplicate retries, expensive adversarial/scorer calls.

Recovery: reduce scenario concurrency, set max attempts/retries, use smaller datasets, separate objective/adversarial/scorer targets, and add memory labels for traceability.

## Optional GCG/model/benchmark path blocked

Symptoms: missing torch/accelerate/sentencepiece, model download fails, CUDA unavailable, benchmark data missing.

Recovery: treat GCG/model-heavy workflows as optional unless explicitly required. Install the documented extra/backend only after the user approves downloads/compute. Use CPU-only import checks only for base PyRIT readiness, not GPU/model verification.

## Results cannot be found

Symptoms: CLI or output helper cannot locate scenario results or attack rows.

Recovery: confirm memory backend, labels, result IDs, run state, cancellation status, and whether the backend/client point at the same PyRIT home/config.
