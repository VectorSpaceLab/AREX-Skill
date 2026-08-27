# Model API and tensor contracts

This reference summarizes the model-construction and inference-related APIs for the SSD300 implementation.

## Public construction API

```python
from ssd import build_ssd
net = build_ssd(phase, size=300, num_classes=21)
```

Signature:

```python
build_ssd(phase, size=300, num_classes=21)
```

Valid arguments:

- `phase`: only `'train'` or `'test'` are accepted. Any other value prints an error and returns `None`.
- `size`: only `300` is implemented. Other values print an error and return `None`; SSD512 config tables are empty in this repository.
- `num_classes`: includes the background class. Use `21` for VOC (20 foreground classes + background). COCO config metadata declares `201`, though published/demo weights in the README are VOC-oriented.

The underlying class signature is:

```python
SSD(phase, size, base, extras, head, num_classes)
```

The constructor selects the config with:

```python
self.cfg = (coco, voc)[num_classes == 21]
```

Therefore `num_classes == 21` selects the VOC SSD300 config; every other class count selects the COCO config. The confidence head shapes are still built from the exact `num_classes` you pass, so state-dict compatibility must match the weight file.

## Architecture components

Construction uses these helpers:

```python
vgg(cfg, i, batch_norm=False)
add_extras(cfg, i, batch_norm=False)
multibox(vgg, extra_layers, cfg, num_classes)
```

Important component facts:

- `vgg(base['300'], 3)` builds a VGG-like feature extractor ending in `pool5`, dilated `conv6`, ReLU, `conv7`, ReLU.
- `add_extras(extras['300'], 1024)` adds alternating 1x1/3x3 convolutional layers that provide additional SSD feature maps.
- `multibox(...)` builds six localization heads and six confidence heads.
- `L2Norm(512, 20)` normalizes the `conv4_3` feature map and applies a learned scale initialized to `20`.
- Localization heads output `boxes_per_location * 4` channels.
- Confidence heads output `boxes_per_location * num_classes` channels.

SSD300 box counts per feature-map location:

```python
mbox['300'] = [4, 6, 6, 6, 4, 4]
```

Feature maps and priors:

| index | feature map | step | boxes/location | VOC min/max size | VOC aspect ratios |
|---:|---:|---:|---:|---|---|
| 0 | 38 x 38 | 8 | 4 | 30 / 60 | `[2]` |
| 1 | 19 x 19 | 16 | 6 | 60 / 111 | `[2, 3]` |
| 2 | 10 x 10 | 32 | 6 | 111 / 162 | `[2, 3]` |
| 3 | 5 x 5 | 64 | 6 | 162 / 213 | `[2, 3]` |
| 4 | 3 x 3 | 100 | 4 | 213 / 264 | `[2]` |
| 5 | 1 x 1 | 300 | 4 | 264 / 315 | `[2]` |

The total number of SSD300 prior boxes is:

```text
38*38*4 + 19*19*6 + 10*10*6 + 5*5*6 + 3*3*4 + 1*1*4 = 8732
```

## Prior boxes

```python
from layers.functions.prior_box import PriorBox
priors = PriorBox(cfg).forward()
```

`PriorBox(cfg).forward()` returns a `torch.Tensor` with shape `(8732, 4)` for the VOC and COCO SSD300 configs. Coordinates are in center-size form:

```text
(cx, cy, width, height)
```

The config fields consumed by `PriorBox` are:

- `min_dim`: `300`
- `feature_maps`: `[38, 19, 10, 5, 3, 1]`
- `steps`: `[8, 16, 32, 64, 100, 300]`
- `min_sizes` and `max_sizes`: dataset-specific box scales
- `aspect_ratios`: dataset-specific list of extra aspect ratios
- `variance`: `[0.1, 0.2]`
- `clip`: `True`, so prior coordinates are clamped to `[0, 1]`

For each feature-map cell, priors include:

1. aspect ratio 1 with `min_size / image_size`,
2. aspect ratio 1 with `sqrt(min_size * max_size) / image_size`,
3. both orientations for each configured non-1 aspect ratio.

## Train-phase forward contract

Input tensor shape:

```text
(batch, 3, 300, 300)
```

For `build_ssd('train', 300, 21)`, a forward pass returns:

```python
loc, conf, priors = net(x)
```

Observed shape contract for a single VOC-sized batch:

```text
loc:    (1, 8732, 4)
conf:   (1, 8732, 21)
priors: (8732, 4)
```

`MultiBoxLoss.forward(predictions, targets)` consumes this tuple. It expects:

- `loc_data`: `(batch, num_priors, 4)`
- `conf_data`: `(batch, num_priors, num_classes)`
- `priors`: `(num_priors, 4)`
- targets per image: boxes in normalized point form plus a zero-based foreground label in the last column.

The loss path uses `match`, `encode`, `log_sum_exp`, and hard negative mining. Training datasets and commands are outside this sub-skill; route those to `../data-training/SKILL.md`.

## Test-phase detection contract

For `phase == 'test'`, `SSD.forward` applies:

```python
self.softmax(conf.view(batch, -1, num_classes))
self.detect(loc.view(batch, -1, 4), conf_probs, priors)
```

`Detect` signature:

```python
Detect(num_classes, bkg_label, top_k, conf_thresh, nms_thresh)
Detect.forward(loc_data, conf_data, prior_data)
```

The repository constructs it as:

```python
Detect(num_classes, 0, 200, 0.01, 0.45)
```

Detection internals:

- decodes predicted offsets with `decode(loc, priors, variance)`, using variances `[0.1, 0.2]` from the VOC config in the detection module;
- skips background class index `0`;
- thresholds each foreground class at `conf_thresh`;
- applies NMS with `nms_thresh` and `top_k`;
- returns an output tensor shaped `(batch, num_classes, top_k, 5)` where the last dimension is:

```text
(score, xmin, ymin, xmax, ymax)
```

Important compatibility warning: the repository's `Detect` class is an old-style `torch.autograd.Function` subclass. On modern PyTorch, `build_ssd('test')` may construct, but a forward pass can fail until `Detect` is ported or a legacy-compatible PyTorch is used.

## Box utility contracts

The main utilities in `layers/box_utils.py` are:

```python
point_form(boxes)      # center-size -> point form
center_size(boxes)     # intended point form -> center-size; patch source before relying on it in modern PyTorch
intersect(box_a, box_b)
jaccard(box_a, box_b)  # IoU matrix
match(threshold, truths, priors, variances, labels, loc_t, conf_t, idx)
encode(matched, priors, variances)
decode(loc, priors, variances)
log_sum_exp(x)
nms(boxes, scores, overlap=0.5, top_k=200)
```

Coordinate conventions:

- Priors are center-size `(cx, cy, w, h)` in normalized coordinates.
- Ground-truth boxes and decoded boxes use point form `(xmin, ymin, xmax, ymax)`.
- `encode` maps matched point-form truth boxes to loc offsets relative to center-size priors.
- `decode` maps loc offsets back to point-form boxes.
- `nms` returns `(keep, count)` for the selected box indices; use `keep[:count]`.

Compatibility note: the inspected source `center_size` implementation passes tensors to `torch.cat` as separate positional arguments rather than as one tuple. On modern PyTorch this raises `TypeError: cat() takes from 1 to 2 positional arguments but 3 were given`. Patch it to `torch.cat((cxcy, wh), 1)` before using that helper in live code.
