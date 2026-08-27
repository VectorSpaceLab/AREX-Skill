# Data Formats

## Captcha image

- Canonical full captcha geometry: `190x293` pixels.
- The crop and tile logic should operate on grayscale arrays. If a color image is supplied, convert it to grayscale before validation or hashing.
- Pixel dtype is normally `uint8`.

## Prompt-text crop

- Slice: `img[3:22, 120 + offset:177 + offset]`.
- Default offset: `0`.
- Expected shape: `(19, 57)`.
- Consumer: text prompt model and OCR-assisted text labeling.

## Image tiles

- Extracted from the full captcha after converting to grayscale.
- Tile size: `(67, 67)`.
- Tile count: `8` for a `190x293` captcha.
- Tile order: row-major over row starts `40,112` and column starts `5,77,149,221`.

## Packed hash vector

- Each supported hash returns a boolean `8x8` decision matrix packed with `numpy.packbits`.
- Stored form: 8 `uint8` bytes per tile.
- Portable display form: 16 lowercase hex characters per tile.
- Legacy aggregation may reinterpret each 8-byte vector as one integer ID. Preserve the original byte vector or hex string when exchanging data across machines to avoid endian ambiguity.

## `data.npz`

Default path in the legacy loader: `./data/data.npz`.

Required keys:

| Key | Expected shape | Meaning |
| --- | --- | --- |
| `texts` | `(N, 19, 57)` | One prompt-text crop per captcha. |
| `images` | `(N, 8, 8)` | Eight packed tile-hash byte vectors per captcha. |

Recommended checks:

- `texts.shape[0] == images.shape[0]`.
- `texts.shape[1:] == (19, 57)`.
- `images.shape[1:] == (8, 8)`.
- `images` is byte-like, preferably `uint8`.

Use [../scripts/captcha_preprocess_diagnostic.py](../scripts/captcha_preprocess_diagnostic.py) for these checks.

## Label vocabulary

The label file contains exactly 80 non-empty rows, one class name per row. The row index is the class id used by text and image models. The integrated root skill should provide the complete copy at `../../../references/label-vocabulary.md`.

## `images.npz` aggregation output

The hash-label aggregation concept saves:

| Key | Expected meaning |
| --- | --- |
| `images` | Unique tile-hash image IDs, derived from packed 8-byte tile hashes. |
| `labels` | One 80-count row per unique tile hash, counting prompt labels from captchas where that tile appeared. |

This artifact is a data-preparation bridge into image modeling. Training and model interpretation are owned by `image-modeling`.
