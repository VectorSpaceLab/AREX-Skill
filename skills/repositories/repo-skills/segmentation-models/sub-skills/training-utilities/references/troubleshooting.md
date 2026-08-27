# Training Workflow Troubleshooting

Use this guide for workflow-level failures around preprocessing, masks, compile/fit/evaluate/predict, fine-tuning, non-RGB data, and utility functions.

## Import chooses the wrong backend or no backend is installed

Symptom examples:

- `ImportError` for `keras`, `tensorflow`, or `efficientnet` when importing `segmentation_models`.
- Segmentation Models prints that it is using standalone `keras` when the project expects TensorFlow Keras.
- Later compile/fit calls fail because objects came from mixed Keras backends.

Fix:

```python
import os
os.environ["SM_FRAMEWORK"] = "tf.keras"  # set before importing segmentation_models
import segmentation_models as sm
from tensorflow import keras
```

Install guidance should remain generic: `pip install segmentation-models`, install a compatible TensorFlow/Keras backend for the target machine, then set `SM_FRAMEWORK=tf.keras` before import in modern environments.

## `fit_generator` / `evaluate_generator` examples fail or warn

Older Segmentation Models examples used Keras generator-specific methods. In modern Keras, call the standard methods with the same data object:

```python
model.fit(train_sequence, validation_data=valid_sequence, epochs=EPOCHS)
model.evaluate(test_sequence)
model.predict(test_sequence)
```

If maintaining a pinned legacy stack, the old aliases may still work, but new workflows should use `fit`, `evaluate`, and `predict`.

## Output and mask channel mismatch

Symptom examples:

- `ValueError` during loss computation about incompatible shapes.
- Model output shape is `(N, H, W, 1)` but masks are `(N, H, W, 2)` or `(N, H, W, 3)`.
- Softmax model receives a single binary channel.

Fix checklist:

1. Decide the task type:
   - one foreground class: `classes=1`, `activation="sigmoid"`, mask shape `(N, H, W, 1)`;
   - mutually exclusive classes with background: `classes=len(CLASSES)+1`, `activation="softmax"`, one-hot mask shape `(N, H, W, classes)`;
   - overlapping multilabel: `classes=len(LABELS)`, `activation="sigmoid"`, independent binary channels.
2. Assert `model.output_shape[-1] == y_batch.shape[-1]` before training.
3. Confirm loss family matches output semantics. Route detailed loss/metric decisions to `losses-metrics`.
4. Confirm background channel position and class-weight order match the chosen mask channel order.

## Spatial shape mismatch

Symptom examples:

- Model output height/width does not match mask height/width.
- Concatenation or upsampling errors during model construction.

Fix checklist:

- Use input sizes compatible with the selected architecture and backbone. For Unet, Linknet, and FPN, choose image dimensions divisible by the encoder downsampling factor in typical workflows.
- Pad or crop validation/test images with the same spatial convention used for training.
- If using PSPNet or unusual input sizes, route constructor-specific checks to `model-construction`.

## Preprocessing was omitted, applied to masks, or applied twice

Symptom examples:

- Training is unstable with ImageNet encoder weights.
- Masks contain non-binary values after augmentation/preprocessing.
- Evaluation data performs much worse than training data due to inconsistent preprocessing.

Fix checklist:

```python
preprocess_input = sm.get_preprocessing(BACKBONE)
x_train = preprocess_input(x_train)
x_val = preprocess_input(x_val)
```

- Apply backbone preprocessing to images only.
- Do not normalize masks with image mean/std transformations.
- Re-binarize masks after mask-affecting augmentation: `mask.astype("float32").round().clip(0, 1)` when appropriate.
- Keep training, validation, evaluation, and prediction preprocessing identical.
- Keep RGB/BGR conversion explicit before preprocessing.

## Non-RGB input fails with pretrained weights

Symptom examples:

- A constructor fails when `input_shape=(..., N)` and `encoder_weights="imagenet"` with `N != 3`.
- A pretrained model expects 3 channels but the dataset has grayscale, multispectral, medical, or remote-sensing channels.

Fix options:

1. Train from scratch:

   ```python
   model = sm.Unet(BACKBONE, input_shape=(None, None, N), encoder_weights=None)
   ```

2. Keep a 3-channel pretrained base and add a trainable adapter:

   ```python
   base_model = sm.Unet(BACKBONE, encoder_weights="imagenet")
   inp = keras.layers.Input(shape=(None, None, N))
   x = keras.layers.Conv2D(3, (1, 1))(inp)
   out = base_model(x)
   model = keras.models.Model(inp, out)
   ```

Do not claim ImageNet preprocessing is automatically meaningful for arbitrary non-RGB channels. Validate domain-specific scaling.

## Pretrained weight download is slow or blocked

Symptom examples:

- Model construction hangs or fails while trying to fetch ImageNet weights.
- Offline/air-gapped runtime cannot construct `encoder_weights="imagenet"` models.

Fix:

- For smoke tests and offline checks, set `encoder_weights=None`.
- Use cached/preinstalled weights only when the deployment environment explicitly provides them.
- Keep long training and weight-download expectations separate from tiny functional checks.

## Training is slow or appears to require a GPU

Segmentation Models can run tiny correctness checks on CPU, but real notebook-scale segmentation training is compute-heavy. A CPU smoke passing only proves the API path works.

Practical reductions:

- Use a small input crop and batch size for debugging.
- Use `encoder_weights=None` to avoid network downloads during plumbing checks.
- Try a smaller backbone or fewer decoder filters for synthetic smokes.
- Run one batch with `train_on_batch` before starting a long `fit`.
- Treat GPU/CUDA as acceleration for real training, not as a requirement for the safe synthetic smoke script.

## `set_trainable` fails or does not use the intended optimizer/lr

`sm.utils.set_trainable(model, recompile=True)` was written for older Keras compile attributes. In modern TensorFlow Keras, it may raise an error like `AttributeError: 'Functional' object has no attribute 'loss_weights'` or `sample_weight_mode`, because those attributes are no longer exposed the same way.

Safer modern pattern:

```python
sm.utils.set_trainable(model, recompile=False)
model.compile(keras.optimizers.Adam(1e-5), loss="binary_crossentropy", metrics=["binary_accuracy"])
```

Use `recompile=True` only when you have verified that the pinned Keras version exposes the compile attributes Segmentation Models expects. If you call `set_trainable(model, recompile=False)`, you must compile manually before continuing training so the optimizer sees the changed trainable state.

## `set_regularization` returns a model that behaves unexpectedly

`sm.utils.set_regularization(...)` sets regularizer attributes on compatible layers, recreates a model from JSON, and copies weights. Common pitfalls:

- The returned model is a new object; use `model = sm.utils.set_regularization(...)`.
- Recompile the returned model before fit/evaluate.
- Optimizer state is not preserved as a substitute for recompilation.
- Custom wrappers/layers must be serializable through Keras JSON.
- Run a tiny `train_on_batch` or the bundled smoke script after regularization changes before launching a long run.

## Smoke script passes but real training fails

The bundled smoke uses synthetic arrays, a tiny Unet decoder, `encoder_weights=None`, one batch, and no dataset IO. It does not validate:

- class names against a real label map;
- image loader color order;
- augmentation correctness;
- class imbalance or loss weighting;
- convergence;
- checkpoint paths/callback side effects;
- GPU memory limits.

Promote from smoke to real training by adding one real batch at a time: load one batch, assert image/mask shapes, preprocess images only, run `model.train_on_batch`, then expand to validation/evaluation.
