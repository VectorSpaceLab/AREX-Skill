# API and data contracts

This reference records the inference contracts that matter for pretrained easy12306 artifacts. It is not a training guide.

## Artifact contracts

| Artifact | Role | Contract |
| --- | --- | --- |
| `model.h5` | Text prompt classifier | Keras/TensorFlow model loaded for cropped prompt images shaped `(1, h, w, 1)` after grayscale normalization. Output classes are indices into `texts.txt`. |
| `12306.image.model.h5` | Image-tile classifier | Keras/TensorFlow model loaded for `67x67` BGR tiles after VGG-style mean subtraction. Output classes are indices into `texts.txt`. |
| `texts.txt` | Label vocabulary | UTF-8 text file with exactly 80 non-empty rows. Row number is the class id used by both models. |
| Captcha image | Inference input | OpenCV-readable BGR image with geometry compatible with the text crop and eight tile crops. Standard captcha-like images are around `190x293`. |

## Text prompt crop contract

The text crop routine uses direct array slicing:

```python
crop = img[3:22, 120 + offset:177 + offset]
```

For standard geometry this yields a crop with height `19` and width `57`. The end-to-end script first calls it with `offset=0`. For a second prompt, it chooses an offset from the length of the first decoded prompt label:

| First prompt label length | Second prompt offset |
| --- | --- |
| `1` | `27` |
| `2` | `47` |
| other | `60` |

The text model input transformation is:

```python
gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
normalized = gray / 255.0
h, w = normalized.shape
normalized.shape = (1, h, w, 1)
```

The second prompt is classified only when `normalized.mean() < 0.95`; otherwise the crop is treated as blank enough to skip.

## Image tile crop contract

The candidate object tiles are generated with these constants:

```python
interval = 5
length = 67
for x in range(40, img.shape[0] - length, interval + length):
    for y in range(interval, img.shape[1] - length, interval + length):
        yield img[x:x + length, y:y + length]
```

For a typical `190x293` captcha image, the starts are:

- rows: `x = 40, 112`;
- columns: `y = 5, 77, 149, 221`.

That produces exactly eight tiles, each with shape `(67, 67, 3)` when the source image was read in color by OpenCV. If the source image is too small or too large, the loop may produce fewer or more than eight tiles; preflight should reject such geometry for end-to-end captcha inference.

## Image preprocessing contract

The image classifier preprocessing converts BGR pixels to `float32` and subtracts fixed BGR means:

```python
x = x.astype("float32")
x -= [103.939, 116.779, 123.68]
```

The single-image prediction command resizes the supplied image to `67x67`, reshapes it to `(-1, 67, 67, 3)`, applies the same preprocessing, then loads `12306.image.model.h5`.

## Prediction and print contracts

### Text prompts

- Load `model.h5`.
- Call `model.predict(text_tensor)`.
- Use `argmax()` to obtain a class id.
- Convert the class id to a label with `texts[class_id]` from the 80-row label file.
- Print the decoded prompt label.

### Captcha image grid

- Load `12306.image.model.h5`.
- Call `model.predict(preprocessed_tiles)`.
- Use `argmax(axis=1)` to obtain one class id per tile.
- Print each tile as:

```text
row col label
```

Rows are `pos // 4`; columns are `pos % 4`; both are zero-based. The eight positions are ordered row-major from top-left to bottom-right.

### Single image-tile prediction

The single-tile helper prints two NumPy-style arrays:

```text
[max_probability]
[class_id]
```

The class id must be mapped through the same `texts.txt` file to obtain a human-readable label.

## Import-time hazards

Do not import modules unrelated to inference. In particular, do not import `baidu.py`; it fetches a token at import time using placeholder credentials. Also note that importing the unmodified `mlearn_for_image.py` imports training utilities such as `keras.preprocessing.image.ImageDataGenerator`, so Keras 3 can break even simple inference unless the preprocessing helper is separated or the environment uses compatible Keras/TensorFlow 2.x.
