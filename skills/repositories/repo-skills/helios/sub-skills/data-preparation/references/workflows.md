# Data-preparation workflows

## Workflow sequence

1. Start from a metadata file that describes each video clip.
2. Confirm that the paths, frame counts, and resolutions match the intended
   training bucket.
3. Produce the latent or embedding artifacts that the training stage consumes.
4. Re-check the file layout before the training launcher sees the dataset.

## What the metadata step must express

- The clip path.
- The number of frames.
- The crop or cut range.
- The frame rate.
- The output resolution.
- The caption or prompt text.

## What the downstream artifacts look like

- Short-latent artifacts are chunked video features keyed by clip ID, frame
  count, height, and width.
- Prompt-embedding artifacts are saved one prompt per `.pt` file.
- ODE-style or GAN-style preparation jobs derive their own dataset variants
  from the same underlying metadata family.

## When to use the bundled script

Use `scripts/validate_toy_filter.py` before a distributed preprocessing run to
catch malformed JSON or missing video files early.
