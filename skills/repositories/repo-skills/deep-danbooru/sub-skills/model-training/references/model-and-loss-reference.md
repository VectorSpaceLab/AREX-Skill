# Model, optimizer, loss, and project reference

## Exact dispatch values

### Models

| `model` | Constructor behavior |
|---|---|
| `resnet_152` | ResNet-152-style bottleneck stack, final average pool, flatten, dense outputs, float32 sigmoid. |
| `resnet_custom_v1` | Short/wide custom bottleneck stack, convolution plus global average pooling, float32 sigmoid. |
| `resnet_custom_v2` | Default; deep/narrow custom stack, convolution plus global average pooling, float32 sigmoid. |
| `resnet_custom_v3` | Custom six-stage bottleneck stack, convolution plus global average pooling, float32 sigmoid. |
| `resnet_custom_v4` | Custom six-stage bottleneck stack with shorter repeated stages, convolution plus global average pooling, float32 sigmoid. |

No aliases or case variants are accepted. Every model returns one sigmoid score
per nonblank line in `tags.txt`. The input is NHWC with shape
`(image_height, image_width, 3)`; the default is `(299, 299, 3)` from
`image_width: 299` and `image_height: 299`.

The building blocks use bias-free convolutions with He-normal initialization,
batch normalization, ReLU activations, residual additions, and either a dense
or convolution/global-average-pooling output head. Final sigmoid activation is
explicitly float32, including under mixed-precision construction.

### Optimizers

| `optimizer` | Construction |
|---|---|
| `adam` | `Adam(learning_rate)` |
| `sgd` | `SGD(learning_rate, momentum=0.9, nesterov=True)` |
| `rmsprop` | `RMSprop(learning_rate)` |

When `mixed_precision` is true, the selected optimizer is wrapped in
`LossScaleOptimizer`. Checkpoint resume restores optimizer state. Do not assume
that loading an optimizer-free `.keras` export is equivalent to restoring a
training checkpoint.

### Losses

| `loss` | Behavior |
|---|---|
| `binary_crossentropy` | Keras `BinaryCrossentropy`; default. |
| `focal_loss` | DeepDanbooru focal loss with defaults `alpha=0.25`, `gamma=2.0`, `epsilon=1e-7`, mean reduction. |

Both are multi-label losses over independent sigmoid outputs. The focal loss
down-weights easy examples; selecting it does not repair label imbalance,
missing positives, or a mismatched tag vocabulary. Training also reports Keras
precision and recall and computes a console F1 value from those step metrics.

## Project fields

| Field | Default | Training contract |
|---|---:|---|
| `image_width` | `299` | Positive integer; model/input target width. |
| `image_height` | `299` | Positive integer; model/input target height. |
| `database_path` | `null` | Must be replaced with a usable SQLite path before training. Relative paths follow process CWD. |
| `minimum_tag_count` | `20` | Non-negative integer used in the SQLite eligibility predicate. |
| `model` | `resnet_custom_v2` | One exact supported model value above. |
| `minibatch_size` | `32` | Positive integer passed to dataset batching. |
| `epoch_count` | `10` | Positive integer for an intended training run. |
| `export_model_per_epoch` | `10` | Non-negative integer; `0` exports every epoch. |
| `checkpoint_frequency_mb` | `200` | Positive integer; slice size is this value times minibatch size. |
| `console_logging_frequency_mb` | `10` | Positive integer; zero causes modulo-by-zero. |
| `loss` | `binary_crossentropy` | One exact supported loss value above. |
| `optimizer` | `adam` | One exact supported optimizer value above. |
| `learning_rate` | `0.001` | Positive finite number; source fallback is `0.001` if absent. |
| `learning_rates` | absent/`null` | Optional list of `{used_epoch, learning_rate}` schedule entries. |
| `rotation_range` | `[0.0, 360.0]` | Ordered two-number range, or null/empty to disable. |
| `scale_range` | `[0.9, 1.1]` | Ordered positive two-number range, or null/empty to disable. |
| `shift_range` | `[-0.1, 0.1]` | Ordered two-number range, or null/empty to disable. |
| `mixed_precision` | `false` | Boolean; enables mixed-float16 construction and loss scaling. |

The training source has fallbacks only for `learning_rate`, `learning_rates`,
`export_model_per_epoch`, `mixed_precision`, and `loss`. Other missing fields
raise a key error. Keep all default fields explicit so a saved project remains
self-describing.

Schedule entries are applied in list order at the start of each epoch. Every
entry with `used_epoch <= current_epoch` overwrites the rate, so use ascending,
unique non-negative epoch thresholds.

## Checkpoint and export contract

Checkpoints live under `PROJECT/checkpoints/`; the manager retains three. They
store model and optimizer variables plus epoch, minibatch, sample, offset, and
shuffle-seed counters. The command always checks for a latest checkpoint and
restores it automatically.

Periodic exports use `model-MODEL.eEPOCH.keras`; final export uses
`model-MODEL.keras`. They are saved with `include_optimizer=False`. An export
is suitable for inference or deliberate source-model initialization, not an
exact optimizer/counter resume.

Mixed precision changes the global policy only while constructing the training
model, then reconstructs a float32 model and restores model variables from the
latest checkpoint for `.float32.keras` export. Validate both the regular and
float32 artifacts with a real inference case. The resulting float32 filename is
formed by appending `.float32.keras` to the regular export path, so it contains
two `.keras` suffix segments.

The `--source-model` branch loads a saved model instead of constructing either
project model. In 1.0.0, `mixed_precision: true` on that branch still attempts
to export an uninitialized `model_float32` local, so reject that combination
rather than waiting for an end-of-run failure.
