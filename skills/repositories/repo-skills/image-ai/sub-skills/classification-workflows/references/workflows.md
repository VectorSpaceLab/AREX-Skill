# Classification Workflows

This guide shows self-contained ImageAI classification workflows for ImageAI 3.x PyTorch weights. It assumes `imageai`, PyTorch, torchvision, Pillow, and numpy are installed in the active Python environment and that all model/image assets are supplied as local files.

## Asset prerequisites

### ImageNet mode

You need:

- One ImageAI PyTorch ImageNet model file with `.pt` or `.pth` extension.
- A model type selection matching that weight architecture: `mobilenetv2`, `resnet50`, `inceptionv3`, or `densenet121`.
- A local image file, numpy array, or PIL image.

The API loads ImageNet labels bundled with the package. No separate class JSON is used in ImageNet mode.

### Custom mode

You need:

- A `.pt` or `.pth` model file produced for ImageAI custom classification.
- The matching JSON class mapping produced with that model during training.
- The same architecture selected at inference time as was used during training.
- A local image file, numpy array, or PIL image.

The JSON mapping connects model output indices to labels. Current training writes a dictionary with string numeric keys and class-name values, for example:

```json
{
  "0": "chef",
  "1": "doctor",
  "2": "engineer"
}
```

`CustomImageClassification.loadModel()` reads the mapping values and sets the model's final layer size to the number of classes. If the JSON mapping does not match the trained model, loading or results can fail.

For creating the custom model and JSON, use [custom-training-and-data](../../custom-training-and-data/SKILL.md).

## Workflow 1: ImageNet classification with the helper CLI

Use the helper when a user wants a safe command that validates local paths, avoids source-checkout assumptions, and prints JSON.

```bash
python scripts/classify_image.py \
  --mode imagenet \
  --model-type resnet50 \
  --model-path /absolute/or/relative/models/resnet50-19c8e357.pth \
  --image /absolute/or/relative/images/input.jpg \
  --result-count 5 \
  --cpu
```

Notes:

- `--cpu` is optional. Use it when the runtime has no GPU, GPU setup is unreliable, or deterministic CPU placement is desired.
- `--result-count` can be 1 through 1000 for ImageNet.
- The helper does not download weights and does not assume the current working directory contains assets.
- Output is JSON with one object per prediction, preserving parallel `label` and `probability` values from ImageAI.

Expected output shape:

```json
{
  "ok": true,
  "mode": "imagenet",
  "model_type": "resnet50",
  "result_count": 5,
  "predictions": [
    {"label": "label_name", "probability": 99.1234}
  ]
}
```

## Workflow 2: Custom classification with the helper CLI

Use custom mode when the user already has ImageAI custom classification weights and the matching JSON mapping.

```bash
python scripts/classify_image.py \
  --mode custom \
  --model-type resnet50 \
  --model-path /models/resnet50-mydata-test_acc_0.90000_epoch-12.pt \
  --json-path /models/mydata_model_classes.json \
  --image /images/sample.jpg \
  --result-count 5 \
  --cpu
```

Validation rules:

- `--json-path` is required in custom mode.
- The JSON path must exist and be parseable JSON.
- `--result-count` should be no greater than the number of classes represented in the JSON mapping.
- The model file must be `.pt` or `.pth`; `.h5` is a TensorFlow-era artifact and is not accepted by ImageAI 3.x.

## Workflow 3: ImageNet classification in Python

Use direct API code when the application needs numpy or PIL inputs, repeated inference, or custom output formatting.

```python
from imageai.Classification import ImageClassification

classifier = ImageClassification()
classifier.setModelTypeAsMobileNetV2()
classifier.setModelPath("models/mobilenet_v2-b0353104.pth")
classifier.useCPU()      # optional; call before loadModel when possible
classifier.loadModel()

labels, probabilities = classifier.classifyImage("images/input.jpg", result_count=5)
for label, probability in zip(labels, probabilities):
    print(label, probability)
```

For repeated classifications, construct and load the classifier once, then call `classifyImage(...)` for each image.

## Workflow 4: Custom classification in Python

```python
from imageai.Classification.Custom import CustomImageClassification

classifier = CustomImageClassification()
classifier.setModelTypeAsDenseNet121()
classifier.setModelPath("models/densenet121-mydata-test_acc_0.92000_epoch-20.pt")
classifier.setJsonPath("models/mydata_model_classes.json")
classifier.useCPU()      # optional
classifier.loadModel()

labels, probabilities = classifier.classifyImage("images/input.jpg", result_count=3)
```

Current ImageAI 3.0.3 custom `loadModel()` takes no `num_objects` argument. The number of output classes comes from the JSON mapping.

## Workflow 5: file, numpy, and PIL inputs

Direct APIs accept three image input forms:

```python
from PIL import Image
import numpy as np

# File path
labels, probabilities = classifier.classifyImage("images/input.jpg", result_count=5)

# PIL image
pil_image = Image.open("images/input.jpg")
labels, probabilities = classifier.classifyImage(pil_image, result_count=5)

# numpy array
array_image = np.asarray(pil_image.convert("RGB"))
labels, probabilities = classifier.classifyImage(array_image, result_count=5)
```

If the array came from OpenCV, it may be BGR instead of RGB. Convert it first if color-sensitive results matter:

```python
import cv2
image_bgr = cv2.imread("images/input.jpg")
image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
labels, probabilities = classifier.classifyImage(image_rgb, result_count=5)
```

## Workflow 6: choosing model type

Choose the model type based on the weights you have:

- `mobilenetv2`: fastest and smallest, useful for CPU-only or low-latency classification.
- `resnet50`: balanced speed and accuracy; common default for examples.
- `inceptionv3`: slower, higher accuracy; select only if the weights were trained/exported for InceptionV3.
- `densenet121`: slower and accurate; select only if the weights were trained/exported for DenseNet121.

The model type setter determines the architecture. The model filename is not authoritative, but it is often the best clue. If loading fails with missing keys, unexpected keys, or size mismatch, first check the selected architecture and custom JSON class count.

## Workflow 7: validation before expensive loading

Before loading large weights, validate cheap facts:

```python
from pathlib import Path
import json

model_path = Path("models/custom.pt")
json_path = Path("models/classes.json")
image_path = Path("images/input.jpg")

assert model_path.is_file(), model_path
assert model_path.suffix.lower() in {".pt", ".pth"}
assert image_path.is_file(), image_path
classes = json.loads(json_path.read_text())
assert isinstance(classes, dict) and classes
```

Then run the helper's `--help` or import smoke checks if you are preparing verification that should not load weights.

## Workflow 8: result handling

ImageAI returns two arrays, not dictionaries. Zip them to avoid misalignment:

```python
labels, probabilities = classifier.classifyImage(image_input, result_count=5)
results = [
    {"label": label, "probability": probability}
    for label, probability in zip(labels, probabilities)
]
```

Probabilities are percentages, not 0-1 fractions.

## Runtime boundaries

- This sub-skill does not train custom classifiers. Use [custom-training-and-data](../../custom-training-and-data/SKILL.md) for training, dataset layout, and JSON/model artifact creation.
- This sub-skill does not detect or localize objects. Use sibling detection sub-skills for bounding boxes, video, extraction, and custom object detection.
- Native full inference tests require external model weights and images. When those assets are absent, restrict checks to imports, signatures, extension errors, path validation, helper `--help`, and documented return-shape assertions.
