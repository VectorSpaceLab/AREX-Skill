# Inference troubleshooting

Use the bundled checker first:

```bash
python3 scripts/check_inference_assets.py --captcha-image <img.jpg> --text-model model.h5 --image-model 12306.image.model.h5 --labels-file texts.txt
```

Add `--load-models` only when the user wants TensorFlow/Keras model loading to run.

## Missing model files

Symptoms:

- `No such file or directory: 'model.h5'`.
- `No such file or directory: '12306.image.model.h5'`.
- The preflight checker reports a missing text or image model path.

Fixes:

1. Put `model.h5`, `12306.image.model.h5`, and `texts.txt` in the working directory used by the unmodified public scripts.
2. If adapting the scripts, pass explicit model paths to the adapter and preserve the original artifact roles.
3. Do not substitute a retrained or differently ordered model unless its output class order still matches the 80-row `texts.txt` vocabulary.

## Bad labels file

Symptoms:

- The checker reports that the label file has a count other than 80 non-empty rows.
- Grid output prints the wrong words for plausible image predictions.
- A prediction class id cannot be mapped to a label.

Fixes:

1. Use UTF-8 text.
2. Keep exactly 80 non-empty rows.
3. Preserve row order: row number is the class id for both `model.h5` and `12306.image.model.h5`.
4. Remove accidental blank rows, headers, comments, or duplicate merged vocabularies.

## Invalid image path or unreadable image

Symptoms:

- `cv2.imread` returns `None`.
- Later code fails with errors involving `NoneType`, slicing, or `cv2.cvtColor`.
- The checker reports that the captcha image is not readable.

Fixes:

1. Verify the image path from the current working directory.
2. Confirm the file is a real image format supported by OpenCV.
3. Use a captcha-like full image for `scripts/run_inference.py captcha`; use a single object image/tile only with `scripts/run_inference.py tile`.

## Wrong captcha geometry

Symptoms:

- The checker reports a text crop shape other than `19x57`.
- The checker reports fewer or more than eight tiles.
- The captcha inference adapter prints too many/few grid lines or silently produces misleading positions.

Expected geometry:

- Text crop at `img[3:22, 120 + offset:177 + offset]` should be `19x57` for offsets `0`, `27`, `47`, and `60`.
- Tile loop should produce exactly two rows and four columns of `67x67` BGR tiles.
- Standard captcha-like geometry is around `190x293`; the exact loop admits two tile rows when height is compatible with starts `40` and `112`, and four columns when width is compatible with starts `5`, `77`, `149`, and `221`.

Fixes:

1. Use the full captcha image rather than a cropped prompt or single tile.
2. Avoid resizing the full captcha before inference; resizing changes crop semantics.
3. If adapting to another captcha layout, update both text crop coordinates and tile loop together, then revalidate with synthetic cases.

## Keras 3 import error

Symptoms:

- `ModuleNotFoundError` or `ImportError` involving `keras.preprocessing.image`.
- The unmodified `main.py` fails while importing `mlearn_for_image.py`, before any model prediction occurs.

Cause:

The original image script imports `keras.preprocessing.image.ImageDataGenerator` at module import time. That training utility is not compatible with Keras 3 layouts used by some modern TensorFlow/Keras installations.

Fixes:

1. Prefer the verified baseline family: Python 3.11 with TensorFlow/Keras 2.15.
2. If only inference is needed, adapt the preprocessing function into a small helper that does not import training-only Keras APIs.
3. Use the checker without `--load-models` to separate image/label/geometry problems from TensorFlow/Keras environment problems.

## Model loading failures

Symptoms:

- `--load-models` fails with HDF5, `h5py`, TensorFlow, or Keras deserialization errors.
- CPU/GPU library warnings obscure the real exception.

Fixes:

1. First run the checker without `--load-models`; fix any file, labels, or geometry failures.
2. Confirm `h5py`, TensorFlow, and Keras are installed in the same environment.
3. Use Keras/TensorFlow 2.x compatible with legacy `.h5` artifacts.
4. Treat a model that loads but produces an output dimension other than 80 as incompatible with the documented label vocabulary.

## Interpreting grid output

The end-to-end command prints one or two prompt labels first, then eight tile lines:

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

Rows and columns are zero-based. Match the prompt labels against the tile labels to decide which positions should be clicked. Multiple matching tiles can appear; the legacy text output does not include confidence scores for the eight grid predictions. For confidence on a single object image, use `python3 scripts/run_inference.py tile --image <img.jpg> --image-model 12306.image.model.h5 --labels-file texts.txt`, which prints maximum probability, class id, and label.
