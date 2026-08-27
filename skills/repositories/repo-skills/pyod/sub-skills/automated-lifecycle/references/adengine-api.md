# ADEngine API Reference

This reference captures the PyOD automated-lifecycle API surface needed by an
agent that has PyOD installed and needs self-contained operating guidance.

## Constructor and determinism

```python
from pyod.utils.ad_engine import ADEngine
engine = ADEngine(knowledge_dir=None, random_state=42)
```

- `knowledge_dir`: optional path to an alternate PyOD knowledge base. Omit it for
  the bundled detector catalog and routing rules.
- `random_state`: forwarded to detectors that declare a `random_state`
  constructor parameter when ADEngine builds them from a plan. Set it to a fixed
  integer for reproducible shallow-detector runs on identical inputs. Detectors
  without a `random_state` parameter are deterministic by construction. Deep
  detector stacks may also need framework-level seeding such as torch seeding.
- An explicit `random_state` already present in `plan["params"]` wins over the
  engine default. Building a detector does not mutate the caller's plan dict.

## Data profiling

```python
profile = engine.profile_data(X, data_type=None)
```

Accepted `data_type` override values: `tabular`, `text`, `image`, `audio`,
`time_series`, `multimodal`, `graph`.

Autodetection is conservative:

| Input form | Detected type | Key profile fields |
|---|---|---|
| NumPy-like array or numeric list | `tabular` | `n_samples`, `n_features`, `has_nan`, `dtype`, `dimensionality_class` |
| Same numeric input with `data_type="time_series"` | `time_series` | tabular fields plus `n_timestamps`, `channels` |
| `list[str]` with image extensions | `image` | `n_samples` |
| `list[str]` with audio extensions | `audio` | `n_samples` |
| other `list[str]` | `text` | `n_samples` |
| `dict` of modalities | `multimodal` | `n_samples`, `modalities` |
| PyTorch Geometric `Data` object, when PyG is installed | `graph` | `n_nodes`, `n_edges`, `n_features`, `has_features`, `n_samples` |

Numeric data is coerced to `float64`; one-dimensional arrays are reshaped to
`(n_samples, 1)`. `dimensionality_class` is `low` for `<=10` features, `medium`
for `11..100`, and `high` for `>100`.

## Planning

```python
plan = engine.plan_detection(
    profile,
    priority="balanced",          # "speed", "accuracy", or "balanced"
    constraints={"exclude_detectors": ["IForest"]},
    top_k=3,
)
```

Plan shape (`DetectionPlan`) is a closed-schema dict:

```python
{
    "detector_name": "IForest",       # class name, case-sensitive
    "params": {"contamination": 0.1}, # constructor kwargs
    "reason": "...",                  # routing explanation
    "evidence": ["..."],              # benchmark/rule evidence strings
    "confidence": 0.7,                 # numeric confidence
    "alternatives": [                  # more DetectionPlan dicts
        {"detector_name": "ECOD", "params": {"contamination": 0.1}, ...}
    ],
    # optional:
    "preset": "for_text",             # used for EmbeddingOD presets
    "note": "..."
}
```

Important behavior:

- `top_k` is clamped to at least `1`; default `3` yields one primary plan plus
  up to two alternatives.
- `constraints["exclude_detectors"]` is a hard exclusion by detector name.
- When all normal routes are excluded, the planner tries a fallback order:
  `IForest`, `ECOD`, `KNN`, `HBOS`, `LOF`, `COPOD`, `PCA`. If every fallback is
  excluded or unavailable, it returns a no-plan dict with `detector_name=""`,
  `confidence=0.0`, and `note="no_valid_plan"`.
- For detectors whose PyOD knowledge entry has a default contamination value,
  planning backfills `params["contamination"]` so JSON-only clients can see the
  effective thresholding value.
- Optional LLM routing is available through `llm_client`. If the LLM call or
  parse fails, ADEngine falls back to rule routing unless `llm_strict=True` or
  environment variable `PYOD3_LLM_STRICT=1` is set.

## Detector construction

```python
clf = engine.build_detector(plan)
```

- Returns an unfitted PyOD detector instance.
- Unknown detector names or planned-but-unshipped detectors raise `ValueError`.
- `EmbeddingOD` presets support `preset="for_text"` and `preset="for_image"`.
- Use `engine.list_detectors()` or `engine.explain_detector(name)` when a name is
  uncertain; names are case-sensitive.

## One-shot detection helpers

### `detect`

```python
result = engine.detect(X_train, X_test=None, data_type=None, priority="balanced")
```

Runs `profile_data -> plan_detection -> run_detection -> analyze_results` and
returns the `run_detection` result enriched with an `analysis` key. Its output is
compatible with `analyze_results`, `explain_findings`, `suggest_next_step`, and
`generate_report`.

### `run_detection`

```python
result = engine.run_detection(X_train, plan, X_test=None)
```

Result keys:

| Key | Type / meaning |
|---|---|
| `plan` | The DetectionPlan used. |
| `scores_train` | NumPy anomaly scores for training rows. Higher means more anomalous. |
| `labels_train` | NumPy binary labels for training rows (`1` anomaly, `0` inlier). |
| `threshold` | Numeric detector threshold. |
| `n_anomalies` | Count of training rows labeled anomaly. |
| `anomaly_ratio` | `n_anomalies / n_train`, a fraction in `[0, 1]`. |
| `detector` | Fitted detector object. Not JSON-serializable. |
| `runtime_seconds` | Fit/runtime duration. |
| `score_summary` | `mean`, `std`, `min`, `max`, `q25`, `q75`. |
| `scores_test`, `labels_test` | Present when `X_test` is supplied and detector supports scoring/prediction for it; set to `None` when not implemented. |

### `analyze_results`

```python
analysis = engine.analyze_results(result, X=X_train, top_k=10)
```

Returns:

- `n_anomalies`, `anomaly_ratio`.
- `score_distribution`: `mean`, `std`, `min`, `max`, `median`, `q25`, `q75`.
- `top_anomalies`: list of `{"index": int, "score": float}` sorted by score
  descending. Negative `top_k` is clamped to `0`.
- `summary`: human-readable one-sentence summary.
- Optional `feature_importance` when the supplied `X` supports it.

### `explain_findings`

```python
explanations = engine.explain_findings(
    result,
    indices=None,        # list[int] or None
    top_k=5,
    X=X_train,
    feature_names=None,
)
```

If `indices` is `None`, ADEngine explains the top-`k` rows by score. Invalid
indices (booleans, non-integers, out of range) are skipped. Each explanation has:

- `index`, `score`, `percentile`, `label`, `narrative`.
- Optional `contributing_features` when `X` is provided. Each contribution has
  `feature`, `name`, `value`, `mean`, `z_score`, and `direction` (`high` or
  `low`). Provide `feature_names` to replace default `feature_<index>` labels.

### `suggest_next_step`

```python
suggestion = engine.suggest_next_step(result, analysis, feedback=None)
```

Returns a dict with at least `action` and `reason`:

| Feedback or condition | Typical action | Notes |
|---|---|---|
| `"too many false positives"`, `"raise threshold"`, `"reduce contamination"` | `adjust_threshold` | Suggests lower contamination; includes `threshold_adjustment.direction="decrease"`. |
| `"missed anomalies"`, `"lower threshold"`, `"increase contamination"` | `adjust_threshold` | Suggests higher contamination; includes `direction="increase"`. |
| `"different"`, `"another"`, `"switch"`, `"ensemble"` | `try_alternative` | Includes `new_plan` when available. |
| No feedback and anomaly ratio > 30% | `adjust_threshold` | Suggests reducing contamination. |
| No feedback and no anomalies | `try_alternative` | Suggests a different detector. |
| Otherwise | `done` | Results look reasonable enough to review. |

### `generate_report`

```python
markdown = engine.generate_report(result, analysis, format="text")
json_text = engine.generate_report(result, analysis, format="json")
```

- `format="text"` returns a Markdown string with configuration, results, score
  summary, and a top-anomalies table.
- `format="json"` returns a JSON string containing detector, reason, sample and
  anomaly counts, threshold, runtime, score distribution, and top anomalies.
- Unknown formats raise `ValueError`.

## Knowledge-query helpers

Use these when an agent needs detector context but not low-level detector usage:

```python
engine.list_detectors(data_type=None, status="shipped")
engine.explain_detector("ECOD")
engine.compare_detectors(names=None, data_type="tabular", top_k=3)
engine.get_benchmarks(benchmark="all")
```

Also useful for caller-driven planning:

```python
kb_context = engine.get_kb_for_routing(profile, top_k=3)
plan = engine.make_plan(
    detector_choices=["ECOD", "IForest", "KNN"],
    justifications=["fast strong baseline", "tree ensemble", "local density"],
)
```

`get_kb_for_routing` is pure and returns a JSON-safe catalog snapshot filtered by
data type and exclusions. `make_plan` validates case-sensitive names against the
knowledge base and packages a plan with alternatives.
