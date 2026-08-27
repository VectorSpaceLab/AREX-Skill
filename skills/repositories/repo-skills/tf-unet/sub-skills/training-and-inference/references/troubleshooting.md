# Troubleshooting

## Shape and checkpoint problems

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Prediction tensors are smaller than the labels | `VALID` convolutions shrink the graph output | Crop labels to `prediction.shape` before loss or evaluation. |
| Restore fails after editing the graph | The checkpoint no longer matches `layers`, `features_root`, or `n_class` | Rebuild the checkpoint with the same graph shape or start a fresh run. |
| The trainer recreates directories unexpectedly | `restore=False` tells the trainer to recreate `output_path` and `prediction_path` | Use a fresh temp directory for inspection or set `restore=True` when resuming. |
| The loss name is rejected | `cost` is not one of the supported names | Use `cross_entropy` or `dice_coefficient`. |
| Optimizer behavior is confusing | Only the legacy `momentum` and `adam` branches are implemented | Choose one of those two or extend the package. |

## Debugging tips

- Keep `summaries=False` for tiny smokes when TensorBoard output is not required.
- Use `verification_batch_size=1` for minimal inspection runs.
- When inspecting a failure, print `net.offset` and `prediction.shape` before debugging the label path.
- If a checkpoint looks correct but restore still fails, verify that the run path points to the checkpoint base name, not just the directory.
- The tiny smoke helper is the fastest way to confirm the graph, checkpoint, and predictor before you investigate a larger training job.
