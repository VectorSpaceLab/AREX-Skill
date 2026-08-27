# Tuning and Fine-Tuning Troubleshooting

## Tuning issues

| Symptom | Cause | Recovery |
| --- | --- | --- |
| Tuning was configured but nothing changed | No tuning action was enabled | Set the relevant tuning flag or use the tuning helpers explicitly. |
| Metric or fold configuration looks odd | `auto` tuning values resolved unexpectedly | Inspect the resolved config before running the workflow. |
| Tune-threshold logic seems wrong | The task is classification and thresholds were not requested | Enable the threshold-tuning branch explicitly. |

## Fine-tuning issues

| Symptom | Cause | Recovery |
| --- | --- | --- |
| Fine-tuning stops too early | Validation split is too small or patience is too low | Increase validation data or patience. |
| Validation never runs | Validation split is disabled | Provide validation data or raise `validation_split_ratio`. |
| Checkpoints are missing | `output_dir` was omitted | Provide a checkpoint directory. |
| Model seems worse after training | Early stopping did not restore the best checkpoint | Check the validation metric and restore logic. |

## Differentiable-input issues

- Categorical columns are not supported.
- Manual `n_classes_` setup may be required for classifier gradients.
- `fit_mode` may switch automatically when differentiable input is enabled.

## When to move on

- If the issue is about ordinary outputs or logits, go back to tabular-prediction.
- If the issue is about data cleaning or feature detection, go to preprocessing-config.
- If the issue is about model weights or checkpoint files, go to model-management.
