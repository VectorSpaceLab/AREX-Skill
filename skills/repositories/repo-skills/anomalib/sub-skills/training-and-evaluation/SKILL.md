---
name: training-and-evaluation
description: "Use for Anomalib's Engine fit/train/test/validate flow, metrics,
  callbacks, preprocessing, postprocessing, loggers, visualization, and
  training-mode guidance while keeping CLI and deployment internals out of
  scope."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Training and Evaluation

Use this sub-skill when the user needs to configure, explain, or debug Anomalib's training/evaluation loop, metric collection, callback order, preprocessing/postprocessing, experiment logging, or visualization.

## Read first

- `references/engine-and-metrics.md`
- `references/callbacks-and-logging.md`
- `references/troubleshooting.md`
- `scripts/training-modes.py`
- `scripts/evaluation-smoke.py`

## Safe operating boundary

Owns the core training/evaluation surface under:

- `src/anomalib/engine`
- `src/anomalib/callbacks`
- `src/anomalib/metrics`
- `src/anomalib/pre_processing`
- `src/anomalib/post_processing`
- `src/anomalib/loggers`
- `src/anomalib/visualization`

Covers:

- `Engine.fit`, `Engine.train`, `Engine.validate`, `Engine.test`, `Engine.predict`, `Engine.from_config`
- `AnomalibModule.configure_callbacks`
- `get_callbacks`
- `Evaluator`, `AnomalibMetric`, `PostProcessor`, `PreProcessor`, `ImageVisualizer`
- training-mode guidance such as `barebones`, checkpointing, and validation-first zero/few-shot behavior

Excludes:

- CLI parsing details
- export/deployment internals
- pipeline orchestration

Treat optional logger packages and GPU-only device checks as non-blocking.

## Quick routing

| User need | Do this |
| --- | --- |
| "How do I wire training, validation, and test?" | Read `references/engine-and-metrics.md`. |
| "Why do my callbacks or loggers behave strangely?" | Read `references/callbacks-and-logging.md`. |
| "Why are metrics missing, duplicated, or empty?" | Read `references/troubleshooting.md`. |
| "Can I run a CPU-only smoke for barebones mode?" | Run `scripts/training-modes.py`. |
| "Can I sanity-check metrics, preprocessing, postprocessing, and visualization?" | Run `scripts/evaluation-smoke.py`. |

## Operating notes

- Model components are usually chained as `pre_processor -> model -> post_processor`, with `evaluator` and `visualizer` attached as callbacks.
- Validation populates normalization and threshold state for `PostProcessor` and related metrics.
- The default evaluator uses prefixed image/pixel metrics so image-level and pixel-level results do not collide.
- Barebones mode removes Lightning logging overhead; use Anomalib's evaluator if you still need returned metrics.
