# Text Modeling Workflows

This reference covers the easy12306 cropped prompt-text classifier. It is responsible for 80-way classification of the small Chinese instruction-text crop, not the eight image tiles.

## Compatibility baseline

- Use a Python 3.11 environment with Keras/TensorFlow 2.15-compatible APIs when reproducing the legacy model workflows.
- Keras 3 is a known risk for the broader script collection because legacy `keras.preprocessing` imports used by sibling inference/image-training code are unavailable. If a task requires both text and image workflows, keep the whole run on the Keras 2.15/TensorFlow 2.15 stack.
- Full training is not a smoke test: the base recipe uses 100 epochs and the fine-tuning recipes may perform an additional 100 epochs. Validate assets first.

## Workflow 1: inspect text training assets safely

Use the bundled inspector before training, fine-tuning, or loading a user's artifacts:

```bash
python sub-skills/text-modeling/scripts/inspect_text_training_assets.py \
  --texts-npz texts.npz \
  --texts-v2-npz texts.v2.npz \
  --labels-file labels.txt \
  --model model.h5
```

Notes:

- `--labels-file` should point to an 80-row vocabulary file in softmax-index order. A raw one-label-per-line file is safest; a simple Markdown table with indexed rows is also accepted.
- `--model` only checks that the file exists. Add `--load-model` only when you intentionally want Keras imported and the model loaded with `compile=False`.
- If only `texts.npz` is available, omit `--texts-v2-npz`. If only checking a deployed model, omit both dataset arguments and provide `--model` plus the labels file.

## Workflow 2: base `model.v1.0.h5` training recipe

The base training data is `texts.npz` with two arrays:

| Key | Expected shape | Meaning |
| --- | --- | --- |
| `texts` | `(n, h, w)` | Grayscale prompt-text crops as numeric pixel values, usually uint8 in `[0, 255]`. |
| `labels` | `(n,)` | Sparse integer class ids in `[0, 79]`, aligned with the 80-row label vocabulary. |

The distilled `load_data(fn='texts.npz', to=False)` behavior is:

1. Load arrays `texts` and `labels` from the `.npz` file.
2. Normalize with `texts = texts / 255.0`.
3. Reshape in-place to `(-1, h, w, 1)` after reading the original `(n, h, w)` dimensions.
4. If `to=True`, convert sparse labels with `to_categorical(labels)`.
5. Return a deterministic 90/10 split: `(texts[:n90], labels[:n90])`, `(texts[n90:], labels[n90:])`, where `n90 = int(total * 0.9)`.

The base `main()` model is a small fully-convolutional classifier:

1. `Conv2D(64, 3x3, padding='same', activation='relu', input_shape=(None, None, 1))`
2. `MaxPooling2D()`
3. `Conv2D(64, 3x3, padding='same', activation='relu')`
4. `MaxPooling2D()`
5. `Conv2D(64, 3x3, padding='same', activation='relu')`
6. `MaxPooling2D()`
7. `GlobalAveragePooling2D()`
8. `Dropout(0.25)`
9. `Dense(64, activation='relu')`
10. `Dense(80, activation='softmax')`

Compile and training contract:

- Optimizer: `rmsprop`.
- Loss: `sparse_categorical_crossentropy`.
- Metric: `accuracy`.
- Callback: `ReduceLROnPlateau(verbose=1)`.
- Epochs: `100`.
- Validation: the 10% split returned by `load_data()`.
- Loss plot: saved from the training history, with the first 9 epochs skipped in the base recipe.
- Output model artifact: `model.v1.0.h5`, saved without the optimizer.

## Workflow 3: `load_data_v2` statistical-data merge

`load_data_v2()` combines the hand-labeled base data with a second statistical dataset:

1. Load `texts.npz` with `to=True`, so base sparse labels become one-hot labels shaped `(n, 80)`.
2. Load `texts.v2.npz` with the default `to=False` behavior.
3. Concatenate base and v2 `texts` arrays for training and validation.
4. Concatenate base and v2 `labels` arrays for training and validation.

Practical consequence: for the unmodified merge to work, `texts.v2.npz` labels should already be compatible with the base one-hot/vote shape `(n, 80)`. Sparse v2 labels can be useful as an intermediate format, but convert them to an 80-column one-hot or vote matrix before using the legacy `load_data_v2()` recipe, otherwise NumPy concatenation will fail.

## Workflow 4: `model.v1.9.h5` fine-tuning

The v1.9 route fine-tunes the base model on `load_data_v2()` output:

1. Validate `texts.npz`, `texts.v2.npz`, and the 80-label vocabulary.
2. Ensure `model.v1.0.h5` exists and was produced by the base text classifier.
3. Load the base model.
4. Compile with optimizer `RMSprop`, loss `categorical_hinge`, and custom metric `acc`.
5. Train for `100` epochs with `ReduceLROnPlateau(verbose=1)` and the v2 validation split.
6. Save `model.v1.9.h5` without the optimizer.

The custom `acc(y_true, y_pred)` metric computes:

```text
argmax(y_true + y_pred) == argmax(y_pred)
```

Then it casts the boolean result to the Keras float type. This metric assumes `y_true` is an 80-column one-hot, vote, or soft-target matrix; it is not appropriate for sparse integer labels.

## Workflow 5: `model.v2.0.h5` fresh-plus-v2 training

The v2.0 route starts from a deeper text model, warms it up on sparse labels, then fine-tunes on v2 statistical targets:

1. Build the same general Conv/Pool/GAP/Dropout/Dense classifier, but with two extra `Conv2D(64, 3x3, padding='same', activation='relu')` layers before the final pooling stage.
2. Compile with `rmsprop`, `sparse_categorical_crossentropy`, and `accuracy`.
3. Train on `load_data()` output for `10` epochs.
4. Reload combined data through `load_data_v2()`.
5. Recompile with `rmsprop`, `categorical_hinge`, and the custom `acc` metric.
6. Train for `100` epochs with `ReduceLROnPlateau(verbose=1)`.
7. Save `model.v2.0.h5` without the optimizer.

Use this route only when the user explicitly wants the v2 training strategy and can supply both datasets. It is more expensive than an asset smoke check and may still need manual tuning if `texts.v2.npz` labels are sparse rather than one-hot/vote targets.

## Workflow 6: deployed text prediction with `model.h5`

The deployed prediction routine is intentionally simple:

1. Load deployed text model artifact `model.h5`.
2. Accept a NumPy array of text crops shaped `(n, h, w)`.
3. Normalize with `texts / 255.0`.
4. Reshape to `(-1, h, w, 1)`.
5. Run `model.predict(texts)`.
6. Return `labels`, an `(n, 80)` probability matrix.

Interpretation:

- `argmax(probabilities[i])` is the predicted label index for crop `i`.
- Map indices to Chinese labels with the root vocabulary reference once it exists: [`../../../references/label-vocabulary.md`](../../../references/label-vocabulary.md).
- If a fine-tuned model was saved with a custom metric and manual loading fails, load with `compile=False` for inference-only checks or provide a matching `acc` custom object.

## Workflow 7: batch prediction and classified image dump

The `_predict`/`show` workflow uses intermediate arrays:

| Artifact | Producer | Consumer | Meaning |
| --- | --- | --- | --- |
| `data.npy` | Data-preparation or a user pipeline | `_predict` and `show` | Text crops shaped `(n, h, w)`. |
| `labels.npy` | `_predict` | `show` | Predicted probability matrix shaped `(n, 80)`. |
| `classify/<label>.<idx>.jpg` | `show` | Human review | One image per text crop, named by predicted integer label and original row index. |

Important details:

- `show` uses `labels.argmax(axis=1)`, so filenames contain integer class ids, not Chinese vocabulary names.
- `classify/` is created if missing. Clear or move an old directory before rerunning if stale review images would confuse the user.
- `cv2.imwrite` writes the raw text crop image; ensure `data.npy` contains image-like arrays, not already normalized float arrays unless that is intentional.

## Hand-offs to sibling routes

- If the user needs to create `data.npy`, `texts.npz`, or `texts.v2.npz` from captcha images, route to data preparation first.
- If the user wants to classify the eight candidate tiles or train `12306.image.model.h5`, route to image modeling.
- If the user wants to answer a full captcha using deployed text and image artifacts together, route to inference.
