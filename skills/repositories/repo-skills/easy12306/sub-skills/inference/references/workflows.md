# Inference workflows

This reference captures the public script-based inference behavior for easy12306. It is intended for future agents that need to run, adapt, or diagnose inference from user-provided artifacts without consulting the original source checkout.

## Environment baseline

Use Python with OpenCV, NumPy, TensorFlow, and Keras compatible with the original script imports. The inspected safe baseline was Python 3.11 with TensorFlow/Keras 2.15. Avoid Keras 3 for the unmodified scripts because `mlearn_for_image.py` imports `keras.preprocessing.image.ImageDataGenerator` at import time.

## Preflight assets without model loading

Run this before attempting inference:

```bash
python3 scripts/check_inference_assets.py \
  --captcha-image <img.jpg> \
  --text-model model.h5 \
  --image-model 12306.image.model.h5 \
  --labels-file texts.txt
```

This checks that:

- the captcha image can be read by OpenCV;
- the text prompt crop has the expected shape;
- the captcha image yields exactly eight `67x67` image tiles;
- `texts.txt` contains exactly 80 non-empty labels;
- both expected model files exist.

Only add model loading when explicitly needed:

```bash
python3 scripts/check_inference_assets.py \
  --captcha-image <img.jpg> \
  --text-model model.h5 \
  --image-model 12306.image.model.h5 \
  --labels-file texts.txt \
  --load-models
```

## End-to-end captcha inference

For self-contained execution, use the bundled adapter with explicit artifact paths:

```bash
python3 scripts/run_inference.py captcha \
  --captcha-image <img.jpg> \
  --text-model model.h5 \
  --image-model 12306.image.model.h5 \
  --labels-file texts.txt
```

This adapts the legacy public command behavior while avoiding hard-coded source-checkout files. Expected behavior:

1. Read the captcha with `cv2.imread`. OpenCV returns BGR channel order. If the path is wrong or unreadable, later crop/color conversion steps fail.
2. Crop the first text prompt with the text crop routine at offset `0`.
3. Convert the text crop to grayscale, normalize it by dividing by `255.0`, and reshape it to `(1, h, w, 1)`.
4. Crop the eight candidate object tiles with the image tile loop and pass them through image preprocessing.
5. Load `model.h5`, run text-model prediction, take `argmax`, and map that class id through `texts.txt`.
6. Print the first prompt label.
7. Determine the second-prompt offset from the first prompt label length:
   - length `1` -> offset `27`;
   - length `2` -> offset `47`;
   - any other length -> offset `60`.
8. Crop the second prompt at that offset. If the normalized crop mean is below `0.95`, classify it with the same text model and print the second prompt label.
9. Load `12306.image.model.h5`, run image-tile prediction on the eight preprocessed tiles, take `argmax(axis=1)`, map each class id through `texts.txt`, and print `row col label` for every tile.

The grid print format uses zero-based row/column coordinates:

```text
<prompt-label-1>
[<prompt-label-2>]
0 0 <tile-label>
0 1 <tile-label>
0 2 <tile-label>
0 3 <tile-label>
1 0 <tile-label>
1 1 <tile-label>
1 2 <tile-label>
1 3 <tile-label>
```

A downstream chooser should select the grid positions whose labels match the printed prompt labels.

## Single image-tile prediction

For self-contained execution, use the bundled adapter:

```bash
python3 scripts/run_inference.py tile \
  --image <tile-or-object-image.jpg> \
  --image-model 12306.image.model.h5 \
  --labels-file texts.txt
```

Expected behavior of the adapted single-tile path:

1. Read the supplied image with `cv2.imread` in BGR order.
2. Resize it to `67x67`.
3. Reshape it to `(-1, 67, 67, 3)`.
4. Convert to `float32` and subtract BGR means `[103.939, 116.779, 123.68]`.
5. Load `12306.image.model.h5`.
6. Print the maximum class probability and the predicted class id.

Output resembles:

```text
[0.8991613]
[0]
```

Map the class id through the same 80-row `texts.txt` vocabulary to recover the human-readable label.

## When adapting the workflow

The legacy scripts used hard-coded relative filenames: `model.h5`, `12306.image.model.h5`, and `texts.txt`. Preserve the crop coordinates, tile loop, BGR mean subtraction, label order, and print semantics described in [API and data contracts](api-reference.md), while allowing explicit paths for user-supplied artifacts as the bundled adapter does.
