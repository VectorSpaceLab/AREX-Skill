# Visualization

## Purpose

Read this when the user wants to inspect lane predictions as a video rather than as a metric.

## Demo behavior

- `demo.py` loads a checkpoint and creates lane overlays on the selected split frames.
- The source script uses OpenCV to write AVI files.
- TuSimple visualizations are not recommended for final qualitative judgments because the split order is not naturally video-like.

## Practical guidance

- Prefer the evaluation workflow first when the user needs a metric.
- Use the demo workflow when the user wants to inspect whether the model is tracking lanes on representative frames.
- Keep the checkpoint and dataset family aligned with the config used to launch the demo.

## Common pitfalls

- Running the demo without a checkpoint path.
- Forgetting that the source script writes to the current working directory.
- Expecting the demo to create a benchmark score.
