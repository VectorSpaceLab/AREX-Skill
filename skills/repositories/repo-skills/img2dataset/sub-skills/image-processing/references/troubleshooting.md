# Troubleshooting

Use the exact error string first. Most image-processing problems come from one of four places: a bad mode string, a codec mismatch, a filter gate, or a bbox schema issue.

## Quick diagnostic order

1. Confirm the mode and interpolation strings are exact.
2. Check whether `resize_only_if_bigger` blocked the resize branch.
3. Check whether a filter rejected the original decoded image before resize.
4. Check whether blur is enabled and whether the bbox values are normalized.
5. If needed, run [`scripts/probe_resize_options.py`](../scripts/probe_resize_options.py) with `--json`.

## Error / symptom matrix

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `Invalid option for resize_mode: ...` | The mode string is misspelled or not one of `no`, `border`, `keep_ratio`, `keep_ratio_largest`, `center_crop`. | Use the exact enum name. |
| `Invalid option for interpolation: ...` | The interpolation string is not one of the accepted aliases. | Use `nearest`, `linear` / `bilinear`, `cubic` / `bicubic`, `area`, or `lanczos` / `lanczos4`. |
| `Invalid encode format ...` | The codec is not `jpg`, `png`, or `webp`. | Pick one of the supported formats. |
| PNG quality error mentioning compression and `0` to `9` | PNG uses compression level, not JPEG-style quality. | Keep PNG compression inside `0-9`. |
| `Image decoding error` | The input stream is corrupt, truncated, or uses an unsupported image codec. | Open the image with a standalone viewer or inspect the source bytes before passing them in. |
| `image too small` | `min_image_size` rejected the original decoded image before any resize happened. | Lower the threshold or filter upstream. |
| `image area too large` | `max_image_area` rejected the original decoded image before any resize happened. | Raise the limit or prefilter upstream. |
| `aspect ratio too large` | `max_aspect_ratio` rejected the original decoded image before any resize happened. | Raise the limit or normalize the source set before download. |
| `blurrer not defined` | A bbox list was provided but `Resizer` was built without a blur helper. | Use the downloader path with `bbox_col` or pass `BoundingBoxBlurrer()` directly when constructing `Resizer`. |
| Blur lands in the wrong place or covers almost the whole image | The bbox column is not normalized, the box order is wrong, or the values are pixel coordinates instead of fractions. | Pass `[x_min, y_min, x_max, y_max]` floats in `[0, 1]` relative to the original image size. |
| Output dimensions stay unchanged when you expected a resize | The chosen mode was `no`, or `resize_only_if_bigger=True` blocked the relevant resize gate. | Check the gate side for the mode: smaller side for `keep_ratio` / `center_crop`, larger side for `border` / `keep_ratio_largest`. |
| `skip_reencode` seems ignored | The image changed shape, got alpha-matted, got blurred, or the input format did not already match the target format. | Remember that `skip_reencode` only preserves the original bytes when nothing changed and the source format already matches the requested one. |
| `disable_all_reencoding` returns `None` dimensions | That is expected: the raw byte stream is returned before decoding or validation. | Use this flag only when you want passthrough behavior and do not need size checks. |
| Blur appears clipped after `center_crop` | Blur runs before the final crop in that mode. | Keep the subject away from the crop edge or choose a mode without a final crop. |

## Common gotchas

- Filter checks happen on the original decoded image, not the resized image.
- `resize_only_if_bigger=True` does not mean “only resize if any side is bigger.” The relevant side depends on the mode.
- `skip_reencode` is not the same as `disable_all_reencoding`.
- The bbox blur path expects one list of boxes per row, not a single flat bbox array.
- A 4-channel alpha image is white-matted before encoding, so it will not round-trip bit-for-bit.

## When you need a repro

Use the probe helper with the same mode and codec settings, then compare:

- `original_width` / `original_height`
- output `width` / `height`
- `err`
- whether the output bytes are identical to the synthetic input bytes

That usually isolates whether the issue is a resize gate, a codec mismatch, or a bbox schema problem.
