# Training, Evaluation, and Fine-Tuning Workflows

This reference is self-contained operating guidance for Segmentation Models 1.0.1 with Keras or TensorFlow Keras. In modern environments, prefer TensorFlow Keras and set `SM_FRAMEWORK=tf.keras` before importing `segmentation_models`.

## Minimal array training flow

```python
import os
os.environ.setdefault("SM_FRAMEWORK", "tf.keras")  # must be set before importing segmentation_models

import segmentation_models as sm
from tensorflow import keras

BACKBONE = "resnet34"
preprocess_input = sm.get_preprocessing(BACKBONE)

# User-provided arrays:
# x_train, x_val: float/uint8 arrays shaped (N, H, W, C)
# y_train, y_val: float/binary or one-hot arrays shaped (N, H, W, classes)
x_train = preprocess_input(x_train)
x_val = preprocess_input(x_val)

model = sm.Unet(
    BACKBONE,
    encoder_weights="imagenet",
    classes=1,
    activation="sigmoid",
)
model.compile(
    optimizer=keras.optimizers.Adam(1e-4),
    loss=sm.losses.bce_jaccard_loss,
    metrics=[sm.metrics.iou_score],
)

history = model.fit(
    x=x_train,
    y=y_train,
    batch_size=16,
    epochs=100,
    validation_data=(x_val, y_val),
)

scores = model.evaluate(x_val, y_val, batch_size=16)
predictions = model.predict(x_val[:4])
```

Use the same high-level flow for `sm.Linknet`, `sm.FPN`, and `sm.PSPNet` after checking their constructor and input-size constraints in the model-construction sub-skill.

## Sequence/generator training flow

Modern Keras `model.fit(...)`, `model.evaluate(...)`, and `model.predict(...)` accept `keras.utils.Sequence` instances and Python generators directly. For new code, prefer:

```python
model.fit(
    train_sequence,
    epochs=EPOCHS,
    validation_data=valid_sequence,
    callbacks=callbacks,
)

scores = model.evaluate(test_sequence)
predictions = model.predict(test_sequence)
```

Older examples may call `fit_generator`, `evaluate_generator`, or `predict_generator`. Those are legacy aliases in many Keras versions; replace them with `fit`, `evaluate`, and `predict` unless you are maintaining pinned legacy code.

## Choosing a binary or multiclass compile recipe

For one foreground class:

```python
CLASSES = ["car"]
n_classes = 1
activation = "sigmoid"
loss = sm.losses.bce_jaccard_loss
metrics = [sm.metrics.IOUScore(threshold=0.5), sm.metrics.FScore(threshold=0.5)]
model = sm.Unet(BACKBONE, classes=n_classes, activation=activation)
model.compile(keras.optimizers.Adam(1e-4), loss, metrics)
```

For mutually exclusive foreground classes plus a background channel:

```python
CLASSES = ["car", "pedestrian"]
n_classes = len(CLASSES) + 1  # foreground classes plus background
activation = "softmax"
loss = sm.losses.cce_jaccard_loss
metrics = [sm.metrics.IOUScore(threshold=None), sm.metrics.FScore(threshold=None)]
model = sm.Unet(BACKBONE, classes=n_classes, activation=activation)
model.compile(keras.optimizers.Adam(1e-4), loss, metrics)
```

For overlapping multilabel targets, use `classes=len(LABELS)`, `activation="sigmoid"`, independent mask channels, and a binary-style loss/metric configuration. Route detailed loss weighting and metric threshold decisions to the losses-metrics sub-skill.

## Validation, evaluation, prediction, and visualization loop

A robust training notebook or script should include these checks before long training:

```python
assert x_batch.ndim == 4                 # (N, H, W, C)
assert y_batch.ndim == 4                 # (N, H, W, classes)
assert x_batch.shape[:3] == y_batch.shape[:3]
assert y_batch.shape[-1] == n_classes

# Fit one small batch first when debugging.
model.train_on_batch(x_batch, y_batch)

# Evaluate on validation/test data using the same image preprocessing.
scores = model.evaluate(valid_data, verbose=0)

# Predict and inspect channel semantics.
pr = model.predict(x_batch[:1], verbose=0)
assert pr.shape[-1] == n_classes
```

For visualization, denormalize only the image copy you display. Do not denormalize or preprocess masks after they have been converted to binary/one-hot channels. For sigmoid binary output, visualize `pred[..., 0]` or `pred[..., 0] > threshold`. For softmax output, visualize `pred.argmax(axis=-1)` or individual class probability channels.

## Fine-tuning with encoder freeze and unfreeze

Use `encoder_freeze=True` to train the randomly initialized decoder without immediately changing the pretrained encoder:

```python
model = sm.Unet(
    backbone_name="resnet34",
    encoder_weights="imagenet",
    encoder_freeze=True,
    classes=1,
    activation="sigmoid",
)
model.compile(keras.optimizers.Adam(1e-3), "binary_crossentropy", ["binary_accuracy"])

# Decoder warm-up.
model.fit(train_data, epochs=2, validation_data=valid_data)

# Unfreeze every layer. In modern tf.keras, prefer manual recompile.
sm.utils.set_trainable(model, recompile=False)

# Recompile explicitly, usually with a lower learning rate after unfreezing.
model.compile(keras.optimizers.Adam(1e-5), loss="binary_crossentropy", metrics=["binary_accuracy"])
model.fit(train_data, epochs=100, validation_data=valid_data)
```

`set_trainable(model, recompile=True)` attempts to mark all model layers trainable and then recompile using the model's current optimizer, loss, metrics, loss weights, sample-weight mode, and weighted metrics. That path matches older Keras APIs, but modern `tf.keras` model objects may no longer expose attributes such as `loss_weights` or `sample_weight_mode`; in that case it can raise an `AttributeError`. Use `recompile=False` plus an explicit `model.compile(...)` when targeting modern TensorFlow Keras or when you want to change the optimizer/lr after unfreezing.

## Adding regularization

`sm.utils.set_regularization(...)` mutates regularizer fields on compatible layers, then creates a new model from JSON and copies the existing weights:

```python
regularizer = keras.regularizers.l2(1e-4)
model = sm.utils.set_regularization(model, kernel_regularizer=regularizer)
model.compile(keras.optimizers.Adam(1e-4), loss, metrics)
```

Important caveats:

- The returned model is a new Keras model object with copied weights; recompile it before training/evaluation.
- Optimizer state is not a substitute for a fresh compile after model recreation.
- Apply regularization before a long training run where possible, and run a tiny batch check after recreation.
- If you wrapped the model with custom layers or custom objects, confirm they serialize through Keras JSON before relying on this utility.

## Safe smoke testing

Use the bundled `scripts/tiny_training_smoke.py` when you need a quick runtime check without data downloads or pretrained weight downloads:

```bash
python scripts/tiny_training_smoke.py --mode binary --epochs 1 --batch-size 1 --run-predict
python scripts/tiny_training_smoke.py --mode multiclass --epochs 1 --batch-size 1 --run-predict
python scripts/tiny_training_smoke.py --mode non-rgb --epochs 1 --batch-size 1 --height 32 --width 32
```

The smoke script uses synthetic arrays, `encoder_weights=None`, a small Unet decoder, and a single batch by default. Passing the smoke does not prove convergence or dataset quality; it only checks that construction, compile, fit/evaluate, and optional predict work in the local backend.
