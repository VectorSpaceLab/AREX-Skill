---
name: data-preparation
description: "Prepare and validate easy12306 captcha crops, tiles, perceptual
  hashes, label vocabulary artifacts, and OCR-assisted labeling workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Artistic 2.0
---

# easy12306 Data Preparation Router

Load this sub-skill when the task is to recreate, inspect, or validate the data artifacts behind easy12306: captcha acquisition, prompt-text crops, 8 image tiles, perceptual hashes, label vocabulary rows, OCR-assisted text labeling, or hash-label aggregation.

Do not use this sub-skill for pretrained model inference, text-model training, or image-model training. Route those tasks to `inference`, `text-modeling`, or `image-modeling` respectively.

## Required references

- [Workflows](references/workflows.md): acquisition, crop/tile extraction, dataset assembly, OCR-assisted labeling, and hash-label aggregation.
- [Data formats](references/data-formats.md): captcha geometry, crop/tile dimensions, `.npz` schemas, and label-vocabulary expectations.
- [Hash reference](references/hash-reference.md): exact packed 64-bit hash algorithms and the excluded wavelet hash caveat.
- [Baidu OCR labeling](references/baidu-ocr-labeling.md): credentialed, network-only reference workflow and import-time hazard.
- [Troubleshooting](references/troubleshooting.md): common geometry, dependency, label, hash, credential, and compatibility failures.
- Root label vocabulary should be read from [../../references/label-vocabulary.md](../../references/label-vocabulary.md) after the integrated root skill creates it.
- Root model/data artifact context should be read from [../../references/model-artifacts.md](../../references/model-artifacts.md) after integration creates it.

## Bundled scripts

- `python scripts/captcha_preprocess_diagnostic.py --help`
- `python scripts/captcha_preprocess_diagnostic.py --self-test`
- `python scripts/captcha_preprocess_diagnostic.py --image CAPTCHA.jpg --labels-file texts.txt --npz data.npz`
- `python scripts/hash_image_tiles.py --help`
- `python scripts/hash_image_tiles.py --self-test`
- `python scripts/hash_image_tiles.py --image CAPTCHA.jpg --method phash`

The scripts are self-contained adaptations of the safe crop, tile, and hash logic. They do not depend on an original source checkout and do not call credentialed OCR or captcha download endpoints.

## Safety and boundary rules

- Treat bulk captcha downloading as an explicitly approved network workflow only. The legacy loop targeted 40,000 images and must not be run as an automatic diagnostic.
- Do not import or run the credentialed OCR helper from the source project. It requests a Baidu token at import time with placeholder credentials.
- Preserve the source geometry exactly: text crop rows `[3:22]`, columns `[120+offset:177+offset]`; eight `67x67` tiles from row starts `40,112` and column starts `5,77,149,221` for a `190x293` captcha.
- Preserve packed hash semantics: the standard hash artifact is 8 bytes per tile, normally represented as a 16-character hex string or an 8-byte `uint8` vector.
