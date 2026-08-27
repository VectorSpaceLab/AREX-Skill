# Model Operations

## Saved Keras models

StellarGraph exposes `stellargraph.custom_keras_layers`, a dictionary of custom
TensorFlow/Keras layer classes used by its model stacks. Use it when loading a
saved Keras model that contains StellarGraph layers:

```python
import stellargraph as sg
from tensorflow import keras

model = keras.models.load_model("model.h5", custom_objects=sg.custom_keras_layers)
```

If loading still fails, check that the saved model was created with a compatible
TensorFlow/Keras and StellarGraph version.

## Calibration APIs

Verified signatures:

```python
expected_calibration_error(prediction_probabilities, accuracy, confidence)
plot_reliability_diagram(calibration_data, predictions, ece=None, filename=None)
TemperatureCalibration(epochs=1000)
IsotonicCalibration()
```

`TemperatureCalibration.fit(x_train, y_train, x_val=None, y_val=None)` expects:

- binary: logits/probabilities shaped `(N,)` and binary labels shaped `(N,)`;
- multiclass: logits shaped `(N, C)` and one-hot labels shaped `(N, C)`.

`IsotonicCalibration.fit(x_train, y_train)` expects classifier probabilities and
labels; multiclass uses one regressor per class.

## Ensembles

Verified constructors:

```python
Ensemble(model, n_estimators=3, n_predictions=3)
BaggingEnsemble(model, n_estimators=3, n_predictions=3)
```

`model` must be a Keras model. `Ensemble` clones the model architecture for naive
ensembling. `BaggingEnsemble` adds bootstrap sampling during training. Compile
and fit the ensemble wrapper with StellarGraph Keras sequences from the owning
model route.

## History, seeds, and utilities

- `stellargraph.utils.plot_history` plots Keras training history.
- `stellargraph.random.set_seed` sets random state for StellarGraph/TensorFlow
  workflows where supported.
- Keep deterministic seeds in graph splitting, generators, NumPy, and TensorFlow
  when comparing experiments.
