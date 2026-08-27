# API Reference

This reference captures the public methods and helpers that matter for rich-media summaries.

## SummaryWriter methods

| Method | Key contract |
| --- | --- |
| `add_image(tag, img_tensor, global_step=None, walltime=None, dataformats='CHW')` | Log one image tensor. `dataformats` describes the input layout. |
| `add_images(tag, img_tensor, global_step=None, walltime=None, dataformats='NCHW')` | Log a batch of images. |
| `add_image_with_boxes(tag, img_tensor, box_tensor, global_step=None, walltime=None, dataformats='CHW', labels=None, **kwargs)` | Log an image with one or more boxes and optional labels. |
| `add_figure(tag, figure, global_step=None, close=True, walltime=None)` | Render a matplotlib figure or list of figures. |
| `add_audio(tag, snd_tensor, global_step=None, sample_rate=44100, walltime=None)` | Encode a 1-D audio signal. |
| `add_video(tag, vid_tensor, global_step=None, fps=4, walltime=None, dataformats='NTCHW')` | Encode a 5-D video tensor. |
| `add_text(tag, text_string, global_step=None, walltime=None)` | Log plain text or Markdown. |
| `add_histogram(tag, values, global_step=None, bins='tensorflow', walltime=None, max_bins=None)` | Log histogram data from numeric values. |
| `add_histogram_raw(tag, min, max, num, sum, sum_squares, bucket_limits, bucket_counts, global_step=None, walltime=None)` | Log a precomputed histogram proto. |
| `add_pr_curve(tag, labels, predictions, global_step=None, num_thresholds=127, weights=None, walltime=None)` | Log precision-recall data. |
| `add_pr_curve_raw(tag, true_positive_counts, false_positive_counts, true_negative_counts, false_negative_counts, precision, recall, global_step=None, num_thresholds=127, weights=None, walltime=None)` | Log precomputed PR curve data. |
| `add_mesh(tag, vertices, colors=None, faces=None, config_dict=None, global_step=None, walltime=None)` | Log a mesh plugin payload. |

## Direct summary builders

Use `tensorboardX.summary.*` when you need a `Summary` proto instead of writing straight through a writer.

| Function | Notes |
| --- | --- |
| `image(tag, tensor, rescale=1, dataformats='CHW')` | Converts image tensors to an image summary. |
| `image_boxes(tag, tensor_image, tensor_boxes, rescale=1, dataformats='CHW', labels=None)` | Same as `image()` but with drawn boxes. |
| `audio(tag, tensor, sample_rate=44100)` | Builds audio summaries from a numeric signal. |
| `video(tag, tensor, fps=4, dataformats='NTCHW')` | Builds a GIF-backed video summary. |
| `histogram(name, values, bins, max_bins=None)` | Builds a histogram summary from values. |
| `histogram_raw(...)` | Builds a histogram summary from precomputed bucket data. |
| `pr_curve(...)` / `pr_curve_raw(...)` | Build PR curve summaries. |
| `text(tag, text)` | Build a text summary. |
| `mesh(tag, vertices, colors, faces, config_dict=None)` | Build a mesh summary. |
| `custom_scalars(layout)` | Build custom scalar layouts. |
| `hparams(hparam_dict=None, metric_dict=None)` | Build hparams plugin summaries. |

## Utility helpers

| Function | Purpose |
| --- | --- |
| `figure_to_image(figures, close=True)` | Convert one figure or a list of figures to image arrays. |
| `make_grid(I, ncols=8)` | Tile a batch of images into a grid. |
| `convert_to_HWC(tensor, input_format)` | Convert image-like arrays to `HWC`. |
| `convert_to_NTCHW(tensor, input_format)` | Convert video-like arrays to `NTCHW`. |
| `_prepare_video(V)` | Normalize/pad video tensors before GIF encoding. |

## Optional dependency notes

- `pillow` is needed for image rendering and box drawing internals.
- `matplotlib` is needed for figure conversion.
- `soundfile` is needed for audio encoding.
- `moviepy` and `imageio` are needed for video encoding.
- `numpy` is required for most shape conversions.

## Read this when

Read this reference when you need exact payload signatures, when a tensor shape or dtype is failing, or when you want to choose between `SummaryWriter` and direct `tensorboardX.summary` construction.
