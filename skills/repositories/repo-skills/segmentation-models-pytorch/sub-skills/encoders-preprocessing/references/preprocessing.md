# Preprocessing Reference

SMP preprocessing helpers expose the input normalization expected by pretrained encoders. Use them when inference or fine-tuning should match the encoder's pretraining data convention.

## APIs

```python
from segmentation_models_pytorch.encoders import (
    get_preprocessing_params,
    get_preprocessing_fn,
)

params = get_preprocessing_params("resnet18", pretrained="imagenet")
preprocess_input = get_preprocessing_fn("resnet18", pretrained="imagenet")
```

Installed signatures:

- `get_preprocessing_params(encoder_name, pretrained="imagenet")`
- `get_preprocessing_fn(encoder_name, pretrained="imagenet")`

`get_preprocessing_params` returns a dictionary with:

- `input_space`: usually `"RGB"`; if `"BGR"`, preprocessing reverses the last channel dimension.
- `input_range`: commonly `[0, 1]`; if input max is greater than 1 and target range is `[0, 1]`, preprocessing divides by 255.
- `mean`: per-channel mean.
- `std`: per-channel standard deviation.

`get_preprocessing_fn` returns a `functools.partial` around SMP's NumPy preprocessing implementation. It expects arrays with channels in the last dimension and applies channel order, range scaling, mean subtraction, and std division.

## Native Encoder Preprocessing

For native registry names, SMP looks up the requested `pretrained` key under the encoder's stored pretrained settings:

```python
params = get_preprocessing_params("resnet18", pretrained="imagenet")
# Typical result:
# {"input_space": "RGB", "input_range": [0, 1], "mean": [0.485, 0.456, 0.406], "std": [0.229, 0.224, 0.225]}
```

If the selected native encoder/pretrained pair is available in SMP's bundled legacy settings, preprocessing can still be resolved when online Hugging Face config loading fails. If neither current config nor bundled fallback exists, the original exception is raised.

Use the same `pretrained` string for preprocessing that you used as model `encoder_weights`. If `encoder_weights=None`, there is no pretrained distribution to match; choose a project-owned normalization policy deliberately instead of pretending it came from SMP weights.

## Timm Universal Preprocessing

For `tu-` names, preprocessing is resolved through timm pretrained configuration:

```python
params = get_preprocessing_params("tu-resnet18")
```

Rules:

- The `tu-` prefix is removed before querying timm.
- SMP checks `timm.models.is_model_pretrained(model_name)`; if false, it raises `ValueError` because there are no pretrained preprocessing parameters.
- The pretrained variant is part of the timm name. For example, a name with a suffix like `.augreg_in21k` carries the variant; the `pretrained` argument is not used for `tu-` lookup in SMP's implementation.
- `encoder_weights=True` means timm should load pretrained weights for the named variant; `encoder_weights=None` means random/offline initialization.

## Offline Patterns

Offline encoder instantiation and preprocessing metadata are separate decisions:

```python
# Offline-safe random encoder.
encoder = get_encoder("resnet34", weights=None)

# Preprocessing params may still be needed for a deployed model trained with ImageNet normalization.
params = get_preprocessing_params("resnet34", pretrained="imagenet")
```

Guidance:

- For offline inference with a model that was trained using pretrained ImageNet normalization, store the resolved params alongside the trained model or configuration.
- For new training from scratch with `encoder_weights=None`, preprocessing is not required by SMP; many projects still scale images to `[0, 1]` and normalize according to their dataset statistics.
- For `tu-` models, metadata comes from timm. If the timm package/version does not know the pretrained config or the name has no pretrained variant, SMP cannot synthesize params.
- Do not let a production inference path depend on live network access merely to fetch `config.json` preprocessing metadata.

## Applying Preprocessing

The helper operates on NumPy-style image arrays:

```python
preprocess_input = get_preprocessing_fn("resnet18", pretrained="imagenet")
image = preprocess_input(image)
```

Behavior from tests and implementation:

- If `input_range=[0, 1]` and image values are larger than 1, the helper divides by 255.
- If `input_space="BGR"`, it reverses the final channel dimension.
- Then it subtracts `mean` and divides by `std` using NumPy broadcasting.
- It does not perform resizing, padding, tensor conversion, channel-first conversion, batching, or augmentation.

## Common Choices

- `resnet18` / `resnet34` with `pretrained="imagenet"`: standard ImageNet RGB params.
- Native `mit_b*`, EfficientNet, MobileNet, and MobileOne names: use their available pretrained setting from the encoder reference table or inspect with `check_encoder.py`.
- `tu-...` names: inspect timm config through `get_preprocessing_params("tu-...")`; choose `encoder_weights=True` for matching pretrained weights or `None` for random initialization.
