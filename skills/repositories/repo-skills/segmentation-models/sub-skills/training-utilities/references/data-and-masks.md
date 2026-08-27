# Data, Mask, Preprocessing, and Non-RGB Conventions

Segmentation Models creates ordinary Keras segmentation models. The model output spatial size is intended to match the input spatial size for valid constructor/input-size combinations, and the output channel count is the constructor `classes` argument.

## Batch and sample shapes

Use channels-last arrays unless the project has deliberately set a different Keras image data format.

| Object | Single sample shape | Batch shape | Notes |
| --- | --- | --- | --- |
| Image | `(H, W, C)` | `(N, H, W, C)` | RGB is `C=3`; non-RGB is supported with the constraints below. |
| Binary foreground mask | `(H, W, 1)` | `(N, H, W, 1)` | Values should be `0/1` or floats in `[0, 1]`. |
| Mutually exclusive multiclass mask | `(H, W, K)` | `(N, H, W, K)` | One-hot class channels; include a background channel when using `classes=len(CLASSES)+1`. |
| Overlapping multilabel mask | `(H, W, L)` | `(N, H, W, L)` | Independent binary channels; a pixel may be positive in multiple channels. |

Always check:

```python
assert x.ndim == 4 and y.ndim == 4
assert x.shape[0] == y.shape[0]
assert x.shape[1:3] == y.shape[1:3]
assert y.shape[-1] == n_classes
```

## Class-channel choices

### One foreground class

Use a single channel and a sigmoid output:

```python
CLASSES = ["car"]
n_classes = 1
activation = "sigmoid"
y.shape == (N, H, W, 1)
```

Each mask value means foreground probability/label for the named class. Do not add a background channel for the common binary foreground setup.

### Mutually exclusive multiple classes plus background

Use one channel per foreground class plus one background channel, with softmax output:

```python
CLASSES = ["car", "pedestrian"]
n_classes = len(CLASSES) + 1
activation = "softmax"
y.shape == (N, H, W, n_classes)
```

For an integer label mask where each pixel belongs to at most one class, a common conversion is:

```python
class_values = [class_to_id[name] for name in CLASSES]
foreground = [(label_mask == value) for value in class_values]
mask = np.stack(foreground, axis=-1).astype("float32")
background = 1.0 - mask.sum(axis=-1, keepdims=True)
background = background.clip(0.0, 1.0)
mask = np.concatenate([mask, background], axis=-1)
```

The background convention must match the model output order and the loss/metric class weighting order.

### Overlapping multilabel targets

Use independent channels and sigmoid output:

```python
LABELS = ["road", "wet_surface", "shadow"]
n_classes = len(LABELS)
activation = "sigmoid"
y.shape == (N, H, W, n_classes)
```

Do not compute `background = 1 - sum(foreground)` when labels can overlap; the sum may exceed 1 and background may not be a valid complement.

## Preprocessing rules

`preprocess_input = sm.get_preprocessing(BACKBONE)` returns the preprocessing function associated with the chosen backbone. Use it for images that feed an ImageNet-pretrained encoder.

Correct:

```python
preprocess_input = sm.get_preprocessing(BACKBONE)
x_train = preprocess_input(x_train)
x_val = preprocess_input(x_val)
```

For dataset wrappers or augmentation libraries, apply preprocessing to the image only:

```python
sample = transform(image=image, mask=mask)        # geometric transforms affect both
image, mask = sample["image"], sample["mask"]
image = preprocess_input(image)                   # image only
mask = mask.astype("float32").round().clip(0, 1)  # keep mask channels valid
```

Practical notes:

- Keep RGB/BGR ordering explicit. If data is loaded as BGR by an image library, convert it to RGB before RGB-trained backbone preprocessing unless the project has intentionally standardized otherwise.
- Do not normalize masks with image mean/std preprocessing.
- Do not preprocess the same image twice. Preprocessed training, validation, evaluation, and prediction images must follow the same convention.
- For random crop/resize/affine augmentation, use nearest-neighbor or mask-safe interpolation for masks and re-binarize masks after transformations that may introduce fractional edges.

## Non-RGB data strategies

Segmentation Models supports non-RGB input, but ImageNet pretrained encoders expect 3 channels. Do not directly combine `input_shape=(..., N)` where `N != 3` with `encoder_weights="imagenet"`.

### Strategy A: train from scratch with N channels

Use this when N-channel inputs are essential and pretrained RGB statistics are not appropriate:

```python
N = x_train.shape[-1]
model = sm.Unet(
    backbone_name="resnet34",
    input_shape=(None, None, N),
    encoder_weights=None,
    classes=1,
    activation="sigmoid",
)
```

With `encoder_weights=None`, choose a project-specific image normalization policy instead of blindly applying RGB ImageNet preprocessing to arbitrary N-channel data.

### Strategy B: learn a 1x1 input adapter before a 3-channel pretrained model

Use this when you want to keep a 3-channel ImageNet-pretrained base model but ingest N-channel data:

```python
import segmentation_models as sm
from tensorflow import keras

N = x_train.shape[-1]
base_model = sm.Unet("resnet34", encoder_weights="imagenet", classes=1, activation="sigmoid")

inp = keras.layers.Input(shape=(None, None, N))
x = keras.layers.Conv2D(3, (1, 1), name="n_channel_to_rgb_adapter")(inp)
out = base_model(x)
model = keras.models.Model(inp, out, name=base_model.name)
```

The adapter learns a projection from N channels to 3 channels. Validate the input scaling and the first few predictions carefully; the adapter does not magically convert sensor bands into natural RGB.

## Tiny synthetic data patterns

Binary smoke data:

```python
x = np.random.normal(size=(1, 32, 32, 3)).astype("float32")
y = (np.random.random(size=(1, 32, 32, 1)) > 0.5).astype("float32")
```

Mutually exclusive multiclass smoke data:

```python
n_classes = 3
labels = np.random.randint(0, n_classes, size=(1, 32, 32))
y = np.eye(n_classes, dtype="float32")[labels]
```

Non-RGB smoke data from scratch:

```python
x = np.random.normal(size=(1, 32, 32, 4)).astype("float32")
y = (np.random.random(size=(1, 32, 32, 1)) > 0.5).astype("float32")
model = sm.Unet("resnet18", input_shape=(32, 32, 4), encoder_weights=None)
```

These patterns validate plumbing only. Replace them with domain-specific loaders, normalization, augmentation, and train/validation splitting for real work.
