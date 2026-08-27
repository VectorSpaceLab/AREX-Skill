---
name: image-processing
description: "Choose and debug img2dataset resizing, encoding, filtering, and
  bounding-box blurring."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Image Processing

Use this sub-skill when the task is about how img2dataset changes image geometry or pixels, especially `Resizer` and `BoundingBoxBlurrer`.

## Route here for

- Choosing a resize mode and predicting the output dimensions: `no`, `border`, `keep_ratio`, `keep_ratio_largest`, `center_crop`.
- Picking interpolation strings, codec settings, and blur behavior.
- Explaining `skip_reencode`, `disable_all_reencoding`, alpha matting, and validation filters.
- Debugging bbox blur input from `bbox_col` or direct `BoundingBoxBlurrer` usage.

## Do not handle here

- Input tables, column mapping, metadata layout, or writer/file format choices: route to [input-output-formats](../input-output-formats/).
- URL downloading, retries, hashing, SSL, incremental runs, and command orchestration: route to [core-download](../core-download/).
- Multiprocessing, PySpark, Ray, W&B, shard sizing, or throughput tuning: route to [distributed-execution](../distributed-execution/).

## Operating workflow

1. Check [image options](references/image-options.md) for the exact mode, codec, and filter semantics.
2. Use [troubleshooting](references/troubleshooting.md) to map errors to the relevant resize, encode, or bbox cause.
3. If you need a quick repro, run [`scripts/probe_resize_options.py`](scripts/probe_resize_options.py) on a tiny synthetic image.
4. For bbox blur cases, confirm the coordinates are normalized `[x_min, y_min, x_max, y_max]` values in `[0, 1]` and that the final dimensions still come from the chosen resize mode.

## Bundled helper

- [`scripts/probe_resize_options.py`](scripts/probe_resize_options.py): synthetic resize/encode/filter/bbox probe with optional JSON output.

Start with [image options](references/image-options.md) and [troubleshooting](references/troubleshooting.md) when the user asks why a sample changed shape, codec, or blur coverage.
