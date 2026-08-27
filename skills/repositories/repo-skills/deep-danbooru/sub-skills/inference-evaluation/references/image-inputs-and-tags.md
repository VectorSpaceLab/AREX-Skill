# Image inputs, preprocessing, and tags

## Accepted call inputs

`load_image_for_evaluate(input_, width, height, normalize=True)` accepts a path
or an in-memory `six.BytesIO` value. The path is passed to
`tf.io.read_file`; the bytes object is read with `getvalue()`. The helper does
not open URLs, directories, or arbitrary file-like objects.

The CLI's default folder patterns cover PNG, JPG, JPEG, and GIF spellings. The
project traversal uses the same four pattern families. The decoder implementation
attempts `tf.io.decode_png(..., channels=3)` first and, on an exception, falls
back to TensorFlow-IO WebP decoding followed by RGBA-to-RGB conversion. The
repository test exercises a JPEG fixture and observes a three-channel result.
Because the source has no separate documented GIF conversion path, validate GIF
inputs in the installed TensorFlow-IO environment before relying on them in a
batch; a filename matching a folder pattern is not proof that decoding will
succeed.

## Exact preprocessing

For target dimensions `(width, height)`:

1. Decode to three channels.
2. Resize with `tf.image.resize`, method `AREA`, with
   `preserve_aspect_ratio=True`. TensorFlow chooses dimensions that fit inside
   the target rectangle.
3. Call `deepdanbooru.image.transform_and_pad_image(image, width, height)`.
   The transform uses a centered affine placement, output shape
   `(height, width)`, interpolation order 1, and edge padding (`mode="edge"`).
   This preserves aspect ratio and fills the remaining area from edge pixels;
   it is not a center crop.
4. When `normalize=True` (the default used by both evaluation commands), divide
   the resulting pixels by `255.0`.

The returned array is HWC, normally `(height, width, 3)`, and is reshaped to
`(1, height, width, 3)` immediately before `model.predict`. A model input such
as `(None, 299, 299, 3)` therefore receives `(1, 299, 299, 3)`. The
`evaluate` API derives dimensions from `model.input_shape`; `evaluate-project`
derives them from `project.json`. Keep these sources consistent.

The default normalized range is intended to be 0..1. Do not normalize again in
a caller, and do not pass `normalize=False` unless the model was deliberately
trained for that convention. A preprocessing smoke check is available at
[`scripts/image_preprocess_smoke.py`](../scripts/image_preprocess_smoke.py).

## Tag-file contract

`tags.txt` is a UTF-8, newline-separated list. `deepdanbooru.data.load_tags`
strips surrounding whitespace and ignores blank lines, preserving the remaining
order. Each tag line names one model output unit. There is no header, score, or
comma syntax in the loader.

A model with output vector length `N` must be paired with exactly `N` intended
tag lines. The implementation does not enforce equality:

- more tags than output scores can cause an indexing error in `evaluate_image`
  or the command;
- fewer tags leave output units unnamed and silently ignore those units;
- duplicate tag strings collapse in the temporary score dictionary, although
  the final iteration still follows the original list and can print duplicate
  names.

Check alignment before inference. If the model was retrained after changing
`tags.txt`, use the tags generated for that exact model rather than a current
or downloaded vocabulary.

## Threshold and text semantics

Scores are compared with `>= threshold`. The source does not sort by score or
apply a top-k rule. A lower threshold is a useful diagnostic for seeing whether
prediction is happening; `--threshold 0.0` should expose nonnegative outputs,
while a threshold above the observed range intentionally produces no tags.

The console score is formatted to three decimal places, followed by the tag in
the input tag order. `--save-txt` writes only selected tag names, joined by
`, `, to a sibling path formed by replacing the input extension with `.txt`.
Scores and a trailing newline are not written. Existing sidecars are opened
with `w` and replaced. The native 1.0.0 helper can fail when the selected list
is empty. The skill-layer `scripts/save_txt_guard.py` makes a safer local
policy available: it rejects empty selections before touching the sidecar,
refuses a directory at the sibling `.txt` path even with overwrite enabled, and
refuses existing regular sidecars unless `--allow-overwrite` is explicit. This
helper does not modify native source or change the native CLI's overwrite
behavior.
