# Data Preparation Troubleshooting

## Captcha image does not produce eight tiles

Expected full captcha shape is `190x293`. The tile extractor uses row starts `40,112` and column starts `5,77,149,221`, yielding eight `67x67` crops. If the diagnostic reports fewer or more tiles, check that the input is a full captcha, not a single tile, screenshot crop, resized image, or browser-scaled asset.

## Text crop shape is not `(19, 57)`

The crop is `img[3:22, 120+offset:177+offset]`. A wrong shape usually means the full image geometry is wrong or the offset is inappropriate. Do not resize the text crop to make the diagnostic pass unless the downstream text-model workflow explicitly requires a different preprocessing path.

## Labels file is not 80 rows

The repo vocabulary has 80 label rows. Remove blank lines, byte-order marks, and comments from ad-hoc copies before using them. The class id is the line index, so reordering rows changes model semantics.

## `.npz` is missing `texts` or `images`

The data-preparation dataset requires `texts` and `images` keys. Expected shapes are `(N,19,57)` and `(N,8,8)`. If an `.npz` contains model-training arrays such as `labels`, route the task to `text-modeling` or `image-modeling` to identify its schema.

## Hash outputs differ from another implementation

Check these details first:

- Convert color images to grayscale before hashing.
- Use cubic interpolation for resizing.
- Use `numpy.packbits` bit ordering rather than formatting booleans manually.
- For `phash`, apply DCT over axis 0 and then axis 1, keep the top-left `8x8`, and compare with the median.
- Preserve packed bytes or hex strings; integer reinterpretation can be endian-sensitive.

## `whash` raises `NameError` or import errors

The legacy wavelet hash references `pywt` without importing it. The bundled hash script excludes `whash`. Add it only with an explicit `PyWavelets` dependency and tests.

## Baidu OCR import hangs or fails

Do not import the credentialed OCR helper from the source project. It performs a token request at import time with placeholder credentials. Use the safe replacement requirements in [baidu-ocr-labeling.md](baidu-ocr-labeling.md).

## Dependency errors

The bundled scripts need `numpy`, `opencv-python` or `opencv-python-headless`, and `scipy` for DCT-based hashes. The repo's broader model workflows were verified with Python 3.11 plus Keras/TensorFlow 2.15. Keras 3 breaks the legacy `keras.preprocessing.image.ImageDataGenerator` import path used by modeling and inference scripts; route those issues to the modeling or inference sub-skills.

## Bulk download concerns

The legacy acquisition loop targeted 40,000 captchas. Treat that as a historical data-generation recipe, not a default command. Require explicit network permission, rate-limit consideration, and a storage plan before collecting new data.
