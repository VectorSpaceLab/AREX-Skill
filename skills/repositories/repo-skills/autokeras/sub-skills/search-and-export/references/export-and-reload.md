# Export and Reload

After `fit` completes:

```python
keras_model = model.export_model()
```

`export_model()` returns the best Keras `Model` found during the AutoKeras search and loaded with trained weights.

Prefer Keras' native `.keras` format:

```python
keras_model.save("model_autokeras.keras")
```

AutoKeras exposes custom layer objects in `ak.CUSTOM_OBJECTS`, including `CastToFloat32` and `ExpandLastDim`. When loading a model exported from AutoKeras, pass these custom objects if Keras cannot resolve them automatically:

```python
from keras.models import load_model
import autokeras as ak
loaded = load_model("model_autokeras.keras", custom_objects=ak.CUSTOM_OBJECTS)
pred = loaded.predict(x_test)
```

Validate an export by checking that the file exists, `load_model(..., custom_objects=ak.CUSTOM_OBJECTS)` returns a Keras model, `loaded.predict` accepts a tiny batch with the same preprocessing assumptions, and prediction shape matches the task target expectation.

The exported Keras model is for inference/further Keras use. It is not the same as the AutoKeras tuner project directory and does not preserve the full search history by itself.
