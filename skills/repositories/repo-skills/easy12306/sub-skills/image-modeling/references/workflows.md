# Image Modeling Workflows

## Purpose

Read this when a task asks for easy12306 image-tile classifier training,
pre-training asset validation, or a model-artifact handoff. The guidance below
is distilled from the source scripts so future agents can use this sub-skill
self-contained.

## Capability boundary

This sub-skill owns the 80-class image-tile classifier. It does **not** own text
prompt recognition, captcha cropping/hash generation, OCR-assisted labeling, or
quick end-to-end inference from pretrained artifacts. Route those requests to
the sibling sub-skills named in `SKILL.md`.

## Required assets

| Asset | Required for | Expected contract |
| --- | --- | --- |
| `captcha.npz` | training | Contains arrays `images` and `labels`; `images` is rank-4 with final channel 3; `labels` length equals image count and is either sparse ids or an 80-column vote/probability matrix. |
| `captcha.test.npz` | manual validation/evaluation | Contains arrays `images` and `labels`; same image contract as training data; labels should represent the same 80-class vocabulary. |
| `texts.txt` | label names | 80 text rows, where row index is the class id printed by image prediction. See root `../../../references/label-vocabulary.md` when integrated. |
| `12306.image.model.h5` | model handoff / prediction | Keras HDF5 artifact for the image-tile softmax-80 classifier. See root `../../../references/model-artifacts.md` when integrated. |

## Workflow: inspect assets before training

1. Resolve the user's candidate data/model files in their working area. Do not
   assume the generated skill includes any model weights or training data.
2. Run the bundled checker:

   ```bash
   python scripts/inspect_image_training_assets.py \
     --captcha-npz captcha.npz \
     --captcha-test-npz captcha.test.npz \
     --labels-file texts.txt \
     --model 12306.image.model.h5
   ```

3. Confirm these observations before any long training job:
   - `images` is `(N, H, W, 3)` and numeric.
   - `labels` has `N` rows.
   - sparse labels are integer-like class ids in `[0, 79]`, or matrix labels are
     `(N, 80)` with non-negative finite values and positive row sums.
   - matrix labels print a sample-weight summary using the legacy formula:
     `labels.max(axis=1) / sqrt(labels.sum(axis=1))`, then normalized by its mean.
   - the labels file has exactly 80 rows.
4. Only pass `--load-model` when the environment is intentionally set up to load
   Keras models. Without that flag, the checker verifies model-file existence
   without importing TensorFlow/Keras.

## Workflow: reproduce the legacy training recipe

Treat the legacy recipe as a reference implementation to recreate in the active
project, not as a quick check. The original no-argument training flow does the
following:

1. Load `captcha.npz`.
2. Convert training images to `float32` and subtract BGR channel means
   `[103.939, 116.779, 123.68]`. The mean order is BGR because OpenCV reads
   images as BGR.
3. Convert vote/probability-matrix labels to sparse class ids with
   `labels.argmax(axis=1)`.
4. Compute sample weights for statistical vote labels:

   ```python
   sample_weight = labels.max(axis=1) / np.sqrt(labels.sum(axis=1))
   sample_weight /= sample_weight.mean()
   ```

5. Load `captcha.test.npz`, preprocess validation images the same way, and keep
   its labels for validation/evaluation.
6. Create `ImageDataGenerator(horizontal_flip=True, vertical_flip=True)` and
   call `.flow(train_x, train_y, sample_weight=sample_weight)`.
7. Build `VGG16(weights="imagenet", include_top=False, input_shape=(None, None, 3))`.
   This may need a network/cache hit for ImageNet weights unless already cached.
8. Freeze all but the last four VGG16 layers.
9. Add this classifier head: `BatchNormalization`, `Conv2D(64, (3, 3), relu,
   same)`, `GlobalAveragePooling2D`, `BatchNormalization`, `Dense(64, relu)`,
   `BatchNormalization`, `Dropout(0.20)`, `Dense(80, softmax)`.
10. Compile with RMSprop learning rate `1e-5`, sparse categorical cross-entropy,
    and accuracy.
11. Train with a generator for `epochs=400`, `steps_per_epoch=100`, validation
    on the first 800 manual validation examples, and `ReduceLROnPlateau`.
12. Evaluate on the full test set and save `12306.image.model.h5` without the
    optimizer.

## Expense and network warning

The training flow is intentionally not a runtime smoke test:

- `epochs=400` and `steps_per_epoch=100` can be long even on CPU-capable hosts.
- VGG16 with `weights="imagenet"` may download weights unless the cache already
  contains them.
- Full training requires external `.npz` datasets not bundled with this skill.
- A GPU may accelerate the workflow, but no GPU-specific dependency is part of
  the verified public contract; CPU inspection is enough for schema and script
  verification.

For verification, prefer the bundled checker and synthetic usability cases. Run
full training only when the user supplies data, compute budget, and permission
for possible downloads.

## Workflow: prediction contract for trained image models

The legacy prediction helper for image tiles works as follows:

1. `predict(imgs)` preprocesses a batch with the same BGR mean subtraction.
2. It loads `12306.image.model.h5`.
3. It returns model probabilities from `model.predict(imgs)`.
4. The single-file diagnostic branch reads an image with OpenCV, resizes it to
   `67x67`, reshapes it to `(1, 67, 67, 3)`, predicts, and prints:
   - maximum confidence per image,
   - argmax class id per image.

For user-facing quick prediction and output interpretation, route to the
`inference` sub-skill. Keep this sub-skill focused on model construction,
inspection, and artifact compatibility.

## Model artifact handoff checklist

Before handing a trained image model to an inference workflow, record:

- the training dataset source and whether labels were sparse ids or vote matrix;
- the exact 80-row label vocabulary used at training time;
- preprocessing order: OpenCV BGR tiles, then subtract BGR means;
- model file name or user-chosen equivalent, with `12306.image.model.h5` as the
  legacy default;
- Keras/TensorFlow major versions used to save/load the model;
- whether ImageNet VGG16 weights came from cache or a network download;
- validation observations from `captcha.test.npz`, if available.
