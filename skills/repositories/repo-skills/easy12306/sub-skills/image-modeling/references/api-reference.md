# Image Modeling API Reference

## Purpose

Use this as the distilled contract for the easy12306 image-tile modeling helpers.
It preserves the relevant behavior of the legacy image training script without
requiring future agents to open or execute that script.

## Environment compatibility

- Verified inspection target: Python 3.11 with Keras/TensorFlow 2.15-compatible
  APIs.
- Known incompatible target: Keras 3, because the workflow imports
  `keras.preprocessing.image.ImageDataGenerator`, which is removed from that
  legacy import path.
- The repository is not an installable Python distribution; public use is
  script-style. Generated helpers in this skill avoid importing repo modules.

## Label vocabulary

The model is an 80-way classifier. Class ids are positional row indexes in the
80-row labels file. In the integrated root skill, read
`../../../references/label-vocabulary.md` for the row-to-label mapping and
`../../../references/model-artifacts.md` for where model files should be placed.

## Data schema

| File | Arrays | Image contract | Label contract |
| --- | --- | --- | --- |
| `captcha.npz` | `images`, `labels` | Rank-4 numeric array `(N, H, W, 3)` in OpenCV BGR order. | Either sparse class ids with length `N`, or an `(N, 80)` vote/probability matrix. Matrix rows must have positive sums for sample weights. |
| `captcha.test.npz` | `images`, `labels` | Same rank-4 BGR image contract. | Same 80-class vocabulary. Sparse labels are expected by the legacy sparse-categorical evaluation path; matrix labels should be converted or inspected before use. |

Use [../scripts/inspect_image_training_assets.py](../scripts/inspect_image_training_assets.py)
to validate these contracts without loading the training model.

## `preprocess_input(x)`

Behavior:

```python
x = x.astype("float32")
x -= [103.939, 116.779, 123.68]
return x
```

Important details:

- The means are in **BGR** order because the image pipeline reads files with
  OpenCV.
- Do not swap to RGB preprocessing unless the upstream image loader changes and
  all training/inference artifacts are regenerated consistently.
- The function mutates the converted `float32` array, not the original integer
  array when `astype` creates a new array.

## `load_data()`

Behavior:

1. Reads `captcha.npz` and extracts `images` / `labels`.
2. Applies `preprocess_input` to training images.
3. Treats training labels as statistical vote/probability rows and computes:

   ```python
   sample_weight = labels.max(axis=1) / np.sqrt(labels.sum(axis=1))
   sample_weight /= sample_weight.mean()
   train_y = labels.argmax(axis=1)
   ```

4. Reads `captcha.test.npz`, extracts `images` / `labels`, and preprocesses test
   images.
5. Returns `(train_x, train_y, sample_weight), (test_x, test_y)`.

Notes for future agents:

- If the user supplies sparse training labels instead of vote rows, do not apply
  the vote-matrix sample-weight formula. Use unit weights or a user-specified
  class/sample weighting policy.
- A row with all zeros makes the vote formula invalid. The bundled checker flags
  non-positive row sums.
- `train_y` becomes sparse class ids via `argmax`, so the compiled loss is
  sparse categorical cross-entropy.

## `learn()`

The legacy training function composes these pieces:

| Stage | Contract |
| --- | --- |
| Data | Calls `load_data()` for statistical training data and manual validation data. |
| Augmentation | `ImageDataGenerator(horizontal_flip=True, vertical_flip=True)`. |
| Base model | `VGG16(weights="imagenet", include_top=False, input_shape=(None, None, 3))`. |
| Fine-tuning | Freezes all VGG16 layers except the last four. |
| Head | `BatchNormalization` → `Conv2D(64, (3,3), activation="relu", padding="same")` → `GlobalAveragePooling2D` → `BatchNormalization` → `Dense(64, activation="relu")` → `BatchNormalization` → `Dropout(0.20)` → `Dense(80, activation="softmax")`. |
| Optimizer/loss | `RMSprop(lr=1e-5)`, sparse categorical cross-entropy, accuracy. |
| Training | Generator training for 400 epochs, 100 steps per epoch, `validation_data=(test_x[:800], test_y[:800])`, and `ReduceLROnPlateau`. |
| Evaluation | Evaluates on all `test_x`, `test_y`. |
| Save artifact | Writes `12306.image.model.h5` with `include_optimizer=False`. |

Compatibility notes:

- `fit_generator` and `RMSprop(lr=...)` are legacy-style Keras APIs. Prefer a
  Keras/TensorFlow 2.15-compatible runtime when preserving the original recipe.
- VGG16 ImageNet weights can trigger a download. Ask before network access or
  use an explicitly supplied local cache/weights plan.

## `predict(imgs)`

Behavior:

1. Applies `preprocess_input(imgs)`.
2. Loads `12306.image.model.h5` with Keras model loading.
3. Returns `model.predict(imgs)` probabilities.

This contract is useful for checking artifact compatibility. For ordinary
pretrained prediction tasks, route to the `inference` sub-skill because it owns
output interpretation and full captcha context.

## `_predict(fn)` diagnostic behavior

The single-image diagnostic branch:

1. reads the image with OpenCV;
2. resizes it to `67x67`;
3. reshapes to `(1, 67, 67, 3)`;
4. calls `predict`;
5. prints `labels.max(axis=1)` and `labels.argmax(axis=1)`.

The printed argmax id maps through the 80-row label vocabulary. The diagnostic
is model-file dependent and should not be used as a schema-only smoke test.
