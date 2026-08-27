# Evaluation and Benchmarking Troubleshooting

| Symptom | Likely cause | Action |
| --- | --- | --- |
| Unrealistically good scores | Temporal leakage or random split | Use temporal splitters and fit transforms inside each fold. |
| Metric column missing | Scorer name mismatch | Inspect `metric.name` and result columns starting with `test_`. |
| `evaluate` hides failures | `error_score` not set to `raise` | Use `error_score="raise"` during debugging. |
| Benchmark takes too long | Too many estimators/tasks/folds or optional models | Start with one tiny task and small splitters. |
| Parallel/backend failure | Backend dependencies or serialization issue | Run single-process first, then enable backend intentionally. |
| Detection metric mismatch | Point events and segments use different representations | Inspect detector output, then choose point or segment metric accordingly. |
