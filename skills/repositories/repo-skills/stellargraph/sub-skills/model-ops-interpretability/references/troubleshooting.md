# Model Operations Troubleshooting

## Saved model cannot load

**Symptoms**

- `Unknown layer`, `Unknown metric`, or Keras deserialization errors.

**Recovery**

- Pass `custom_objects=stellargraph.custom_keras_layers` to `keras.models.load_model`.
- Use a TensorFlow/Keras/StellarGraph version compatible with the version that
  saved the model.

## Calibration shape errors

**Symptoms**

- `x_train and y_train must be numpy arrays`.
- Dimension mismatch in `TemperatureCalibration.predict`.

**Recovery**

- Convert logits/probabilities and labels to NumPy arrays.
- For multiclass temperature calibration, use `(N, C)` logits and one-hot labels.
- For binary Platt scaling, use 1D scores and labels.

## Ensemble constructor rejects model

**Symptom**

- `model must be a Keras model`.

**Recovery**

- Build a complete `tf.keras.Model` first, including StellarGraph inputs and the
  prediction head, then pass that model to `Ensemble` or `BaggingEnsemble`.

## Saliency input-count errors

**Recovery**

- Use the same dense/sparse full-batch generator path that built the model.
- Keep the generator object used for model construction.
- Use valid node indices and class indices.

## Neo4j failures

**Symptoms**

- `py2neo` missing, connection refused, auth errors, slow queries, duplicate IDs,
  or missing feature properties.

**Recovery**

- Install the `neo4j` extra for `py2neo`.
- Verify service host/auth outside model code.
- Create uniqueness constraints for node IDs where appropriate.
- Confirm every selected node has numeric `features` or the configured feature
  property.
