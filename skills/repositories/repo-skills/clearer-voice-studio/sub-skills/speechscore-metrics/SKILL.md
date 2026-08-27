---
name: speechscore-metrics
description: "Choose, validate, and run SpeechScore objective metrics for
  intrusive and non-intrusive speech quality assessment."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# SpeechScore Metrics

Use this sub-skill when a task asks for objective speech quality assessment with SpeechScore: selecting metrics, scoring one enhanced/degraded file against a clean reference, scoring matched test/reference directories, scoring reference-free MOS-style metrics, tuning `window`/`score_rate`/`return_mean`, or interpreting nested result dictionaries.

Start here:

- Read [references/api-reference.md](references/api-reference.md) for the `SpeechScore` factory, import-layout rules, call parameters, result shapes, and important `window`/`score_rate` caveats.
- Read [references/metric-catalog.md](references/metric-catalog.md) before choosing metrics or deciding whether `reference_path` is required.
- Read [references/workflows.md](references/workflows.md) for copyable dry-run, single-file, matched-directory, reference-free, and nested-result interpretation recipes.
- Read [references/troubleshooting.md](references/troubleshooting.md) when imports, metric dependencies, model-backed metrics, references, directory basenames, or windowed scoring fail.
- Use [scripts/speechscore_metric_recipe.py](scripts/speechscore_metric_recipe.py) to validate requested metric names/reference behavior or to run scoring without assuming bundled sample paths.

Operating rules:

1. Use this sub-skill only for SpeechScore objective metric selection and scoring.
2. Route audio enhancement, separation, super-resolution, or target-speaker extraction generation to `../clearvoice-inference/` before scoring.
3. Route benchmark list creation, dataset manifests, training launchers, or training/evaluation data preparation to `../training-and-data-prep/`.
4. Decide `reference_path` from the metric catalog, not from each source class's `intrusive` attribute; that attribute is inconsistent in this snapshot.
5. For dry runs, validate metric names, whether any selected metric requires a reference, and matching directory basenames before reading audio.
6. For real source-layout runs from outside the SpeechScore component directory, pass `--speechscore-dir <speechscore_component_dir>` so the helper can import `speechscore.py` and resolve metric assets.
7. Prefer `window=None` for direct source API calls. Use the bundled helper when windowed scoring or explicit non-fixed metric resampling is required, because the inspected source window branch has a `maxlen` bug and the direct `score_rate` argument is not reliably honored for non-fixed metrics.
