# Classification API Reference

This reference summarizes the ImageAI 3.x PyTorch classification APIs verified from source and installed-package inspection. It is self-contained for runtime use; it does not require the source checkout.

## Classes and imports

| Workflow | Import | Class | Use when |
|---|---|---|---|
| ImageNet classification | `from imageai.Classification import ImageClassification` | `ImageClassification` | You have one of ImageAI's PyTorch ImageNet release weight files and want labels from the built-in ImageNet 1000-class list. |
| Custom classification inference | `from imageai.Classification.Custom import CustomImageClassification` | `CustomImageClassification` | You have a model trained by ImageAI custom classification plus its generated JSON class mapping. |

Both classes require PyTorch, torchvision, Pillow, and numpy through the ImageAI package. ImageAI 3.x is a PyTorch backend; TensorFlow/Keras `.h5` classifiers belong to old ImageAI 2.1.6-or-earlier workflows.

## Required call order

### ImageNet classification

```python
from imageai.Classification import ImageClassification

classifier = ImageClassification()
classifier.setModelTypeAsResNet50()        # choose exactly one model type
classifier.setModelPath("/models/resnet50-19c8e357.pth")
classifier.useCPU()                         # optional; call before loadModel when possible
classifier.loadModel()
labels, probabilities = classifier.classifyImage("/images/cat.jpg", result_count=5)
```

Required before `classifyImage(...)`:

1. One model type setter.
2. `setModelPath(path)` with an existing `.pt` or `.pth` file.
3. Optional `useCPU()` to force CPU.
4. `loadModel()`.

### Custom classification inference

```python
from imageai.Classification.Custom import CustomImageClassification

classifier = CustomImageClassification()
classifier.setModelTypeAsResNet50()         # architecture used during training
classifier.setModelPath("/models/custom-resnet50.pt")
classifier.setJsonPath("/models/custom_model_classes.json")
classifier.useCPU()                         # optional; call before loadModel when possible
classifier.loadModel()
labels, probabilities = classifier.classifyImage("/images/sample.jpg", result_count=5)
```

Required before `classifyImage(...)`:

1. One model type setter matching the custom trained architecture.
2. `setModelPath(path)` with an existing `.pt` or `.pth` file.
3. `setJsonPath(path)` with the JSON class mapping generated with the model.
4. Optional `useCPU()` to force CPU.
5. `loadModel()`.

## Verified methods and signatures

### `ImageClassification`

| Method | Signature / arguments | Notes |
|---|---|---|
| Constructor | `ImageClassification()` | Chooses CUDA when available, otherwise CPU, unless `useCPU()` is called. |
| Model type | `setModelTypeAsMobileNetV2()` | Selects MobileNetV2 ImageNet architecture. Source internal key: `mobilenetv2`. |
| Model type | `setModelTypeAsResNet50()` | Selects ResNet50 ImageNet architecture. Source internal key: `resnet50`. |
| Model type | `setModelTypeAsInceptionV3()` | Selects InceptionV3 ImageNet architecture. Source internal key: `inceptionv3`. |
| Model type | `setModelTypeAsDenseNet121()` | Selects DenseNet121 ImageNet architecture. Source internal key: `densenet121`. |
| Weights path | `setModelPath(path: str)` | `path` must be an existing file. Extension must be `.pt` or `.pth`; `.h5` raises a TensorFlow compatibility error. |
| Device | `useCPU()` | Forces CPU. If a model is already loaded, ImageAI marks it unloaded and calls `loadModel()` again. |
| Load | `loadModel()` | Loads selected architecture and state dict, moves model to selected device, loads ImageNet labels, and calls eval mode. Must be called before classification. |
| Predict | `classifyImage(image_input, result_count=5)` | `image_input` may be file path, numpy array, or PIL image. Returns `(labels, probabilities)`. |

`ImageClassification.classifyImage(image_input, result_count=5) -> tuple[list[str], list[float]]`.

- `result_count` should be a whole number from 1 to 1000 for ImageNet.
- Results are sorted by descending probability.
- Probabilities are percentage values rounded to 4 decimals in current source.
- If `loadModel()` has not succeeded, `classifyImage(...)` raises `RuntimeError("Model not yet loaded...")`.

### `CustomImageClassification`

| Method | Signature / arguments | Notes |
|---|---|---|
| Constructor | `CustomImageClassification()` | Chooses CUDA when available, otherwise CPU, unless `useCPU()` is called. |
| Model type | `setModelTypeAsMobileNetV2()` | Selects custom MobileNetV2 architecture. Source internal key: `mobilenet_v2` with underscore. |
| Model type | `setModelTypeAsResNet50()` | Selects custom ResNet50 architecture. Source internal key: `resnet50`. |
| Model type | `setModelTypeAsInceptionV3()` | Selects custom InceptionV3 architecture. Source internal key: `inception_v3` with underscore. |
| Model type | `setModelTypeAsDenseNet121()` | Selects custom DenseNet121 architecture. Source internal key: `densenet121`. |
| Weights path | `setModelPath(path: str)` | `path` must be an existing `.pt` or `.pth` file. The same extension checker rejects `.h5` and unrelated extensions. |
| Class map path | `setJsonPath(path: str)` | `path` must be an existing JSON file. `loadModel()` reads `json.load(f).values()` as class names. |
| Device | `useCPU()` | Forces CPU. If already loaded, reloads the model. |
| Load | `loadModel()` | Reads class JSON, creates the selected architecture with final layer size equal to the number of JSON classes, loads state dict with `map_location` set to the device, and calls eval mode. |
| Predict | `classifyImage(image_input, result_count)` | `result_count` is required in the signature. Returns `(labels, probabilities)`. |

`CustomImageClassification.classifyImage(image_input, result_count) -> tuple[list[str], list[float]]`.

- `result_count` should not exceed the number of classes in the JSON mapping.
- Class labels come from JSON values in insertion order after `json.load`. ImageAI training writes sorted classes with string numeric keys such as `{"0": "chef", "1": "doctor"}`.
- Probabilities are percentage values rounded to 4 decimals in current source.

## Model type mapping

Use these public CLI/model keys and setter names in generated commands or code:

| Public key | ImageNet setter | Custom setter | Typical file naming hints | Relative speed/accuracy notes from docs |
|---|---|---|---|---|
| `mobilenetv2` | `setModelTypeAsMobileNetV2()` | `setModelTypeAsMobileNetV2()` | ImageNet examples use `mobilenet_v2-...pth`; custom examples may use `mobilenet_v2-<dataset>-...pt`. | Fastest, smaller weights, moderate accuracy. |
| `resnet50` | `setModelTypeAsResNet50()` | `setModelTypeAsResNet50()` | ImageNet examples use `resnet50-...pth`; custom examples may use `resnet50-<dataset>-...pt`. | Fast, high accuracy. |
| `inceptionv3` | `setModelTypeAsInceptionV3()` | `setModelTypeAsInceptionV3()` | ImageNet examples use `inception_v3_google-...pth`; custom examples may use `inception_v3-<dataset>-...pt`. | Slower, higher accuracy. |
| `densenet121` | `setModelTypeAsDenseNet121()` | `setModelTypeAsDenseNet121()` | ImageNet examples use `densenet121-...pth`; custom examples may use `densenet121-<dataset>-...pt`. | Slower, high accuracy. |

The filename is only a hint. The architecture setter must match the architecture used to create the weights. A mismatch usually fails during `loadModel()` with state-dict size/key errors or produces invalid outputs.

## Image input forms

Both classifiers use the same preprocessing path:

1. Resize to 256.
2. Center crop 224.
3. Convert to tensor.
4. Normalize with ImageNet mean/std.

Accepted `image_input` forms:

| Input form | Accepted by direct API? | Accepted by helper script? | Notes |
|---|---:|---:|---|
| File path string | Yes | Yes | Must point to an existing image file readable by Pillow. Source converts to RGB. |
| `numpy.ndarray` | Yes | No | Source wraps with `Image.fromarray(...).convert("RGB")`. Useful for OpenCV/web API data, but remember OpenCV arrays are usually BGR. |
| `PIL.Image.Image` | Yes | No | Source checks for `"PIL"` in the type string and converts to RGB. |

The bundled CLI helper intentionally accepts file paths only so it can validate paths before loading weights and print clear JSON output.

## Return shape

Both APIs return two parallel Python lists:

```python
labels, probabilities = classifier.classifyImage(image_input, result_count=5)
assert isinstance(labels, list)
assert isinstance(probabilities, list)
assert isinstance(labels[0], str)
assert isinstance(probabilities[0], float)
```

Example structured result you can produce in downstream applications:

```json
{
  "mode": "imagenet",
  "model_type": "resnet50",
  "image": "image.jpg",
  "result_count": 5,
  "predictions": [
    {"label": "convertible", "probability": 52.4596},
    {"label": "sports_car", "probability": 37.6128}
  ]
}
```

## Model extension checks

`setModelPath(...)` calls ImageAI's extension checker:

- `.pt` and `.pth` are accepted if the file exists.
- `.h5` raises a TensorFlow compatibility `RuntimeError`: ImageAI 3.x uses PyTorch; TensorFlow models/custom `.h5` models require ImageAI 2.1.6 or earlier.
- Other extensions raise `ValueError` asking for `.pt` or `.pth`.

The extension check runs before model architecture loading, so extension errors are usually clearer than state-dict errors.

## Known API drift from older examples

Some older custom-classification documentation shows `prediction.loadModel(num_objects=10)`. Current ImageAI 3.0.3 source and installed inspection verify `CustomImageClassification.loadModel()` takes no `num_objects` argument; class count is inferred from `setJsonPath(...)` JSON values. Use `classifier.loadModel()`.
