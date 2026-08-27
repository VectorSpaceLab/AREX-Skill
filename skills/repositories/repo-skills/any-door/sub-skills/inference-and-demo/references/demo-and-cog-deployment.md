# Demo and Cog Deployment

This reference covers the two non-interactive ways users commonly expose AnyDoor
as a service: a local Gradio demo and a Cog predictor.

## Local Gradio demo

The source demo script:

- loads the demo checkpoint from `configs/demo.yaml`,
- optionally loads the interactive segmentation model,
- exposes sliders for strength, steps, guidance scale, and seed,
- and lets the user upload or sketch a background and a reference object.

Important behavior to remember:

- The demo is sensitive to coarse masks.
- The source includes a shape-control toggle.
- The interactive mask-refinement toggle is optional.
- The demo launches on `0.0.0.0` in the source script.

## Cog / Replicate predictor

The predictor workflow:

- downloads or uses a cached model archive,
- loads the same core AnyDoor inference stack,
- exposes structured prediction inputs rather than a web UI,
- and writes a single output image.

Important behavior to remember:

- Network access may be required for the first model fetch.
- The predictor’s file-path contract is separate from the local Gradio flow.
- The helper is useful for deployment planning even if the user never runs Cog.

## When to use which

- Use **Gradio** when the user wants to test masks interactively.
- Use **Cog** when the user wants a containerized prediction interface.
- Use **plain inference** when the user only wants a single batch or script run.

## What the future agent should say

- which checkpoint each surface consumes,
- whether mask refinement is on or off,
- whether the service depends on network downloads,
- and whether a failed launch is actually a checkpoint or mask problem.
