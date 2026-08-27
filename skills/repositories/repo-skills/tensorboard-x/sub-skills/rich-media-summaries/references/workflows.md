# Workflows

This reference gives the safest order for common rich-media tasks.

## 1. Log one image or a batch of images

1. Decide whether your data is one image or a batch.
2. Convert it to `CHW` or `NCHW` as appropriate.
3. Call `add_image()` or `add_images()`.
4. If the image is grayscale or batched in a different layout, pass the right `dataformats` string.

Tiny example pattern:

```python
writer.add_image("preview", image_array, global_step=0, dataformats="CHW")
writer.add_images("preview_batch", batch_array, global_step=0, dataformats="NCHW")
```

## 2. Log an image with boxes

1. Prepare the image tensor.
2. Prepare boxes in `xyxy` order.
3. Pass optional labels only if they match the boxes.
4. Keep the image size modest; it is only a summary, not a detection benchmark.

## 3. Log a figure

1. Build a `matplotlib` figure.
2. Call `add_figure()` or `tensorboardX.summary.figure_to_image()` if you need the image array.
3. Close the figure if you are creating many of them.

## 4. Log audio

1. Build a 1-D signal.
2. Keep values in `[-1, 1]`.
3. Pass the correct sample rate.
4. Install `soundfile` if the helper raises a missing dependency error.

## 5. Log video

1. Build a 5-D tensor in `NTCHW` form or pass the matching `dataformats` string.
2. Keep the clip short for smoke tests.
3. Ensure `moviepy` and `imageio` are installed.
4. If 1-channel output looks wrong, check the moviepy/imageio compatibility notes.

## 6. Log histograms and PR curves

- Use histograms for distributions, not for huge training dumps.
- Use `add_pr_curve()` when you have binary labels and scores.
- Use the raw variants only when you already have the bucket counts from another system.

## 7. Log text and mesh summaries

- Use text for short comments, status messages, or Markdown notes.
- Use mesh summaries when the user is inspecting vertices, faces, or a small geometry preview.

## 8. Validate the workflow with the bundled smoke script

Run the bundled helper when you want a quick local sanity check before writing a larger script:

```bash
python scripts/tbx_media_summary_smoke.py
```

The script creates a temporary directory, writes tiny payloads, and reports which optional payloads were exercised.

## Best practices

- Keep arrays tiny and deterministic.
- Prefer a temporary logdir for local experimentation.
- Route scalar-only tasks back to `logging-core`.
- Route graphs and projector payloads to `graph-and-embedding-plugins`.
