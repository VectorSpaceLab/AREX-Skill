# Batched Inference Troubleshooting

## Common failures

| Symptom | Cause | Recovery |
| --- | --- | --- |
| `ragged batches are not supported` | Train or test arrays do not share one shape | Group datasets by shape or score them individually. |
| `same set of classes` error | Class sets differ across datasets | Rebuild the batch so every dataset has the same label set. |
| `float64` `NotImplementedError` | Fused batched forward only supports lower precision | Use per-dataset prediction or lower the inference precision. |
| `balance_probabilities` or `tuning_config` rejected in batched mode | Those fitted states are dataset-specific | Score datasets individually. |
| OOM during batched cached prediction | Chunking or cache placement is too aggressive | Reduce `TABPFN_MAX_BATCHED_TEST_ROWS` or switch to a lower-memory fit mode. |

## What to check first

- Are all datasets truly the same shape family?
- Are you trying to batched-score a classifier with different class sets?
- Is the user forcing `float64` or an unsupported post-processing option?
- Is the task really a single dataset that should use ordinary prediction instead?

## When to move on

- If the issue is about input cleaning, route to preprocessing-config.
- If the issue is about one-dataset logits or quantiles, route to tabular-prediction.
- If the issue is about fine-tuning or calibration, route to tuning-and-advanced.
