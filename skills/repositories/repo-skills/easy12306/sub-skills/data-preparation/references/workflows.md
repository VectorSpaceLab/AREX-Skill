# Data Preparation Workflows

This sub-skill preserves the repo's data-preparation behavior without requiring a future agent to read or run the original scripts.

## 1. Captcha image acquisition

Legacy constants and behavior:

- Image directory constant: `PATH = 'imgs'`.
- Single fetch endpoint: `https://kyfw.12306.cn/passport/captcha/captcha-image64`.
- The response body is JSON containing base64 field `image`.
- The saved filename is `md5(raw_response_content).hexdigest() + '.jpg'` under `PATH`.
- The bulk loop creates `PATH` and calls the single fetch 40,000 times.

Operational guidance:

1. Only acquire images with explicit user approval, network permission, and rate/terms review.
2. Store raw downloaded images separately from generated `.npz` files.
3. Keep the MD5 filename convention if reproducibility with legacy artifacts matters.
4. Do not run the 40,000-image loop as a smoke test; use the bundled diagnostics on existing or synthetic images instead.

## 2. Prompt-text crop extraction

Given a grayscale captcha array, the text prompt crop is:

```python
text = img[3:22, 120 + offset:177 + offset]
```

With default `offset=0`, the expected crop shape is `19x57`. The crop is used by the text prompt model and by OCR-assisted labeling.

Use [../scripts/captcha_preprocess_diagnostic.py](../scripts/captcha_preprocess_diagnostic.py) to validate crop shape on a candidate captcha image.

## 3. Eight image-tile extraction

The tile extractor uses `length = 67`, `interval = 5`, row stepping by `72`, and column stepping by `72`:

```python
for x in range(40, img.shape[0] - 67, 72):
    for y in range(5, img.shape[1] - 67, 72):
        yield img[x:x + 67, y:y + 67]
```

For the canonical `190x293` captcha, this yields eight row-major tiles:

| Tile index | Row start | Column start | Shape |
| --- | ---: | ---: | --- |
| 0 | 40 | 5 | `67x67` |
| 1 | 40 | 77 | `67x67` |
| 2 | 40 | 149 | `67x67` |
| 3 | 40 | 221 | `67x67` |
| 4 | 112 | 5 | `67x67` |
| 5 | 112 | 77 | `67x67` |
| 6 | 112 | 149 | `67x67` |
| 7 | 112 | 221 | `67x67` |

## 4. Tile perceptual hashes

The legacy `get_imgs` workflow applies `phash` to each extracted tile and returns a list of eight packed 8-byte vectors. See [hash-reference.md](hash-reference.md) and [../scripts/hash_image_tiles.py](../scripts/hash_image_tiles.py).

## 5. `load_data` dataset assembly

The default dataset path is `./data/data.npz`. If the file is absent, the legacy workflow:

1. Ensures enough source images exist by calling the bulk acquisition path.
2. Reads each image as grayscale.
3. Appends the `19x57` text crop to `texts`.
4. Appends the eight tile `phash` vectors to `images`.
5. Saves `np.savez(path, texts=texts, images=imgs)`.
6. Returns `f['texts']`, `f['images']` from the `.npz`.

For safe reproduction, separate the acquisition step from local preprocessing. Validate existing datasets with the diagnostic script instead of triggering downloads implicitly.

## 6. Label vocabulary

The source label vocabulary contains 80 rows. Integrated root documentation should provide the complete vocabulary at `../../../references/label-vocabulary.md`. Data-preparation diagnostics only verify that a supplied labels file has exactly 80 non-empty rows.

## 7. Baidu OCR-assisted text labeling

The OCR workflow is reference-only because the original helper requests a Baidu token at import time. It accepted each prompt-text crop, sent it to the OCR API, and logged an index plus returned word for manual labeling. Use [baidu-ocr-labeling.md](baidu-ocr-labeling.md) before designing any credentialed replacement.

## 8. Hash-label aggregation concept

The aggregation workflow groups repeated tile hashes and counts which text-prompt labels co-occurred with each tile:

1. Load `texts, imgs = load_data()`.
2. Predict text labels with the text model and take `argmax(axis=1)`.
3. Reinterpret each tile's packed 8 bytes as one integer image ID.
4. Compute unique image IDs.
5. For each unique image ID, find captchas containing that tile hash.
6. Count the 80-way prompt-label co-occurrences with `np.bincount(..., minlength=80)`.
7. Save `images.npz` with `images=<unique image ids>` and `labels=<80-column count rows>`.

Do not require this aggregation to run during data-preparation verification; it depends on generated data and a text model. Route model availability questions to `text-modeling`.
