# Text Modeling API and Artifact Reference

This file distills the text-classifier contracts into self-contained operating knowledge. Function names mirror the legacy script API so agents can recognize related user code, but runtime guidance should come from this skill and its bundled helper rather than from an external checkout.

## Label vocabulary contract

- Number of classes: `80`.
- Softmax index range: `0..79`.
- Vocabulary order: one row per class in the root vocabulary reference, expected at [`../../../references/label-vocabulary.md`](../../../references/label-vocabulary.md) after integration.
- Both the text prompt classifier and the image-tile classifier use this 80-label vocabulary, but their inputs and model artifact names differ.

## Dataset schemas

### `texts.npz`

Required arrays:

| Key | Required form | Source behavior |
| --- | --- | --- |
| `texts` | Numeric array shaped `(n, h, w)` | Divided by `255.0`, then reshaped to `(-1, h, w, 1)`. |
| `labels` | Sparse integer array shaped `(n,)` | Used directly for sparse loss; optionally converted with `to_categorical(labels)`. |

Validation expectations:

- `texts.shape[0] == labels.shape[0]`.
- Pixel values are normally uint8-like `[0, 255]`; already-normalized `[0, 1]` values will be divided by 255 again by the legacy loader.
- Labels should be integer-like and within `[0, 79]`.
- The legacy loader unpacks `_, h, w = texts.shape`, so exactly three text dimensions are safest even though the bundled inspector can warn on higher-dimensional arrays.

### `texts.v2.npz`

Required arrays are also `texts` and `labels`; text preprocessing is the same. The v2 file is described as statistical data and is merged after base labels are one-hot encoded.

Accepted label forms for inspection:

| Detected form | Shape | Usability note |
| --- | --- | --- |
| Sparse ids | `(n,)` | Valid as a data interchange format, but convert to one-hot/vote matrix before using the unmodified v2 merge recipe. |
| One-hot matrix | `(n, 80)` | Directly compatible with `load_data_v2()` concatenation. |
| Vote/soft-target matrix | `(n, 80)` | Compatible with categorical-hinge fine-tuning and the custom `acc` metric if values are non-negative. |

### `data.npy` and `labels.npy`

| File | Shape | Role |
| --- | --- | --- |
| `data.npy` | `(n, h, w)` | Cropped text images to classify with deployed `model.h5`. |
| `labels.npy` | `(n, 80)` | Probability matrix produced by the text model. |

`show`-style review output writes `classify/<label>.<idx>.jpg`, where `<label>` is the predicted integer id from `argmax(labels[i])`.

## Distilled function behavior

### `load_data(fn='texts.npz', to=False)`

Inputs:

- `fn`: `.npz` file containing `texts` and `labels`.
- `to`: when true, convert sparse integer labels to one-hot labels.

Behavior:

1. Load `texts` and `labels`.
2. Normalize text images by dividing by `255.0`.
3. Reshape from `(n, h, w)` to `(-1, h, w, 1)`.
4. Optionally call `to_categorical(labels)`.
5. Split deterministically at `int(n * 0.9)`.

Outputs:

```text
(train_x, train_y), (test_x, test_y)
```

where `train_x`/`test_x` are 4D grayscale tensors and labels are sparse or one-hot depending on `to`.

### `savefig(history, fn='loss.jpg', start=2)`

Reads `history.history['loss']` and `history.history['val_loss']`, skips epochs before `start`, and saves a training/validation loss plot to `fn`.

### `main()` base trainer

Purpose: train the first text CNN and save `model.v1.0.h5`.

Architecture:

| Stage | Layer |
| --- | --- |
| 1 | `Conv2D(64, (3, 3), padding='same', activation='relu', input_shape=(None, None, 1))` |
| 2 | `MaxPooling2D()` |
| 3 | `Conv2D(64, (3, 3), padding='same', activation='relu')` |
| 4 | `MaxPooling2D()` |
| 5 | `Conv2D(64, (3, 3), padding='same', activation='relu')` |
| 6 | `MaxPooling2D()` |
| 7 | `GlobalAveragePooling2D()` |
| 8 | `Dropout(0.25)` |
| 9 | `Dense(64, activation='relu')` |
| 10 | `Dense(80, activation='softmax')` |

Compile/train/save:

- Optimizer: `rmsprop`.
- Loss: `sparse_categorical_crossentropy`.
- Metrics: `accuracy`.
- Callback: `ReduceLROnPlateau(verbose=1)`.
- Epochs: `100`.
- Save: `model.v1.0.h5` with optimizer omitted.

### `load_data_v2()`

Purpose: merge base one-hot training data with statistical v2 data.

- Calls `load_data(to=True)` for `texts.npz`.
- Calls `load_data('texts.v2.npz')` for v2 data.
- Concatenates train and validation text tensors separately.
- Concatenates train and validation labels separately.

Because base labels are one-hot after `to=True`, v2 labels need the same trailing class dimension for the unmodified concatenation path.

### `acc(y_true, y_pred)`

Custom metric for categorical-hinge fine-tuning:

```text
K.cast(
  K.equal(K.argmax(y_true + y_pred, axis=-1), K.argmax(y_pred, axis=-1)),
  K.floatx()
)
```

Interpretation: the prediction is counted correct if adding the target vector to predicted scores does not change the predicted argmax. It expects one-hot, vote, or soft-target `y_true`, not sparse class ids.

### `main_v19()`

Purpose: fine-tune the base model with v2 statistical data.

- Loads data through `load_data_v2()`.
- Loads `model.v1.0.h5`.
- Compiles with optimizer `RMSprop`, loss `categorical_hinge`, and metric `acc`.
- Trains for `100` epochs with `ReduceLROnPlateau(verbose=1)`.
- Saves `model.v1.9.h5` without optimizer.

### `main_v20()`

Purpose: train a deeper v2 model from scratch plus v2 fine-tuning.

- Builds a deeper Conv2D model with five 64-filter convolution layers in total, max pooling between early blocks and before `GlobalAveragePooling2D`.
- First stage: load sparse `texts.npz`, compile with `rmsprop` + `sparse_categorical_crossentropy` + `accuracy`, and train for `10` epochs.
- Second stage: load merged v2 data, recompile with `rmsprop` + `categorical_hinge` + `acc`, and train for `100` epochs with `ReduceLROnPlateau(verbose=1)`.
- Saves `model.v2.0.h5` without optimizer.

### `predict(texts)`

Purpose: run deployed text-model inference.

- Loads deployed text model file `model.h5`.
- Normalizes input `texts` by `255.0`.
- Reshapes `(n, h, w)` to `(-1, h, w, 1)`.
- Returns `model.predict(texts)`, an `(n, 80)` probability matrix.

### `_predict()` and `show()`

- `_predict()` loads `data.npy`, runs `predict(texts)`, and saves the probability matrix to `labels.npy`.
- `show()` loads `data.npy` and `labels.npy`, computes `argmax(axis=1)`, creates `classify/`, and writes each text crop to `classify/<label>.<idx>.jpg`.

## Model artifact ownership

| Artifact | Owner route | Meaning |
| --- | --- | --- |
| `model.v1.0.h5` | text-modeling | Base text classifier trained with sparse labels. |
| `model.v1.9.h5` | text-modeling | Fine-tuned base model using v2 statistical targets. |
| `model.v2.0.h5` | text-modeling | Deeper model trained with sparse warm-up plus v2 fine-tuning. |
| `model.h5` | inference/text-modeling | Deployed text prompt model used by prediction helpers. |
| `12306.image.model.h5` | image-modeling/inference | Separate image-tile classifier; do not use it for prompt text crops. |

See the root artifact reference after integration for cross-skill model placement: [`../../../references/model-artifacts.md`](../../../references/model-artifacts.md).
