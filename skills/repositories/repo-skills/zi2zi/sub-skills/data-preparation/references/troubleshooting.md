# Data-preparation troubleshooting

## `font2img.py` creates no JPGs

Likely causes:

- `--sample_dir` does not exist. Create it before running the original script.
- The source or target font path is wrong or unreadable.
- The charset contains characters unsupported by the target font.
- `--filter=1` filtered every sampled glyph as recurring or blank.
- `--sample_count=0` or a tiny charset ended before enough examples were drawn.

Recovery: rerun with a tiny custom charset and `--filter=0` to prove the font
path and rendering stack work. Then re-enable filtering for large CJK runs.

## Many characters look blank or identical

The target font may not contain those glyphs. Use `--filter=1` for production
renders, reduce the charset to supported characters, or choose a different
target font. The filter hashes target glyph images and skips recurring outputs
that usually indicate missing-glyph fallback.

## Unicode charset errors

The original script reads custom charset files with Python 2 UTF-8 decoding.
Keep custom charset files as a single UTF-8 line. Avoid BOMs, comments, or extra
lines. If Python 3-created files fail in Python 2, recreate them with a simple
UTF-8 writer and no metadata.

## `package.py` fails with label parsing errors

`package.py` expects every JPG basename to start with an integer followed by
`_`. Examples that work: `0_0000.jpg`, `12_0042.jpg`. Examples that fail:
`style_a_0000.jpg`, `0000.jpg`, `label-0.jpg`.

Rename files or rerun `font2img.py` with a numeric `--label`.

## `train.obj` or `val.obj` is empty

Possible causes:

- The samples directory had no `*.jpg` files.
- The split ratio and tiny sample count randomly placed all examples in one
  file.
- All input JPGs failed before packaging.

For a smoke test, inspect both files and accept that one may be empty with very
few examples. For real training, generate enough examples per label and use a
reasonable validation split such as `0.1`.

## Python 3 cannot unpickle `.obj` files

The original packager uses Python 2 pickle strings. Use a Python 3 loader that
passes `encoding="latin1"` to `pickle.load` when needed. The bundled
[inspect_zi2zi_obj.py](../scripts/inspect_zi2zi_obj.py) does this.

## Image dimensions are wrong

The model expects paired images with width exactly twice the half-image width.
With default rendering, images should be `512x256`. If custom rendering tools
were used, verify that the split point divides the image into two equal square
halves and that both halves are RGB-like image data.
