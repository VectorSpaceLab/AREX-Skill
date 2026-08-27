# Custom Search Spaces

Use `AutoModel` when the request includes multiple inputs/outputs, forced or excluded block families, explicit normalization/augmentation/merge/reduction choices, or shared trunks between heads.

## Input/output API

```python
import autokeras as ak
model = ak.AutoModel(
    inputs=[ak.ImageInput(), ak.TextInput()],
    outputs=[ak.ClassificationHead(), ak.RegressionHead()],
    max_trials=1,
    overwrite=True,
)
```

## Functional API

```python
image_input = ak.ImageInput()
image = ak.Normalization()(image_input)
conv = ak.ConvBlock()(image)
resnet = ak.ResNetBlock(version="v2", pretrained=False)(image)
merged = ak.Merge()([conv, resnet])
output = ak.ClassificationHead(num_classes=2)(merged)
model = ak.AutoModel(inputs=image_input, outputs=output, max_trials=1, overwrite=True)
```

The block call returns an AutoKeras node. Pass final nodes, not raw Keras tensors, to `AutoModel`.

## Fixing versus tuning parameters

Most block parameters default to `None`, which means AutoKeras can tune them. Set concrete values to constrain the search:

```python
image = ak.ImageBlock(block_type="vanilla", normalize=True, augment=False)(image_input)
text = ak.TextBlock(max_tokens=500)(text_input)
tab = ak.StructuredDataBlock(normalize=True)(structured_input)
head = ak.ClassificationHead(num_classes=3, dropout=0.0)(tab)
```

Use fixed values for reproducible smoke checks or when a specific architecture family is requested. Leave values tunable when the goal is broad AutoML search.

## Safe custom graph smoke pattern

The bundled `scripts/build_tiny_custom_image_automodel.py` constructs a small graph using only synthetic image arrays. It defaults to dry-run mode so future agents can check graph construction without performing a training search. Add `--run-fit` only when a tiny local search is acceptable.
