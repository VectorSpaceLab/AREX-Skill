# MXNet model-zoo troubleshooting

Use this page for MXNet GluonCV model-zoo failures. For dataset, transform, script-command, PyTorch, AutoGluon, and export failures, route to the sibling sub-skills named in `../SKILL.md` or this sub-skill's `SKILL.md`.

## Quick diagnostic sequence

Run these from any project that has GluonCV installed:

```bash
python - <<'PY'
import gluoncv
print('gluoncv', gluoncv.__version__)
print('found mxnet', getattr(gluoncv, '_found_mxnet', None))
print('found pytorch', getattr(gluoncv, '_found_pytorch', None))
from gluoncv.model_zoo import get_model_list
print('mxnet model count', len(list(get_model_list())))
PY
```

Then run the bundled safe helper:

```bash
python scripts/mxnet_model_inventory.py --count --model cifar_resnet20_v1 --dry-forward
```

Expected verified signal: registry count 332 and dry-forward output shape `(1, 10)`.

## Symptoms, causes, fixes

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ImportError: Unable to import modules due to missing mxnet & torch` | Neither supported backend imports. | Install at least one supported framework. For this sub-skill, install MXNet compatible with GluonCV's guard. |
| `Unable to import dependency mxnet` when importing `gluoncv.model_zoo` | MXNet is missing or broken. | Install MXNet CPU/GPU matching the Python version and platform, then rerun the quick diagnostic. |
| `Legacy mxnet==... detected` or version guard failure | GluonCV requires MXNet `>=1.4.0,<2.0.0`. | Use an MXNet 1.x package accepted by that range. Avoid MXNet 2.x for this repo version. |
| `AttributeError: module 'numpy' has no attribute 'bool'` or related NumPy alias errors | MXNet 1.9-era code expects NumPy aliases removed in NumPy 1.24. | Use `numpy<1.24` with legacy MXNet. Reinstall/restart the Python process after changing NumPy. |
| Warning that both MXNet and Torch are installed | GluonCV found both frameworks and warns about increased GPU memory footprint. | Usually safe for CPU inspection. For GPU production, avoid importing/using both in one long-lived process when memory matters. |
| `ValueError` from `get_model(name)` with a long model list | Unknown or misspelled registry name. | Validate with `python scripts/mxnet_model_inventory.py --filter <substring> --names` and use the exact registry name. |
| Pretrained model construction hangs or fails with network errors | `pretrained=True` or a hash triggered a cache lookup/download. | Use `pretrained=False` for dry runs. If pretrained weights are required, allow network access or pre-populate the MXNet model cache. |
| Hash/checksum error after a weight download | Interrupted or corrupted cached parameter file. | Remove the affected cached `.params` file and retry when network is stable; do not switch to `pretrained=False` if the task requires pretrained accuracy. |
| `MXNetError` about CPU/GPU context mismatch | Parameters and input arrays are on different contexts. | Create inputs with the same `ctx`, pass `ctx` to pretrained constructors where supported, and use `net.collect_params().reset_ctx(ctx)` before forwarding. |
| GPU model fails but CPU works | CPU-only MXNet build, missing CUDA runtime, incompatible GPU build, or invalid GPU id. | Confirm `mx.context.num_gpus()` or use CPU. Do not claim CUDA behavior unless a CUDA MXNet package is installed and verified. |
| `ModulatedDeformableConvolution` missing for `dcnv2` models | Selected MXNet build lacks required contrib operator. | Choose a non-`dcnv2` model or install an MXNet build exposing `mx.gluon.contrib.cnn.ModulatedDeformableConvolution`. |
| `reset_class()` raises missing class name or index out of bounds | `reuse_weights` names/indices do not match old or new classes. | Inspect `net.classes`; use exact names or valid dataset-specific indices. For new classes with no old equivalent, omit them from `reuse_weights` and train/fine-tune. |
| Custom detector constructor fails with missing `classes` | `_custom` model names require class names. | Pass `classes=['class_a', 'class_b', ...]`; use `reset_class()` only when starting from an existing model instance. |
| Detector output shape looks unexpected | Detector returns task tuples, not a single logits tensor. | For SSD/YOLO/Faster R-CNN, unpack `(ids, scores, bboxes)`. For Mask R-CNN, also handle masks. Apply presets/NMS before visualization. |
| Semantic segmentation output is a list/tuple | Many segmentation models return auxiliary outputs. | Use the first output as the primary logits tensor when validating shape. |
| Pose model produces heatmaps, not coordinates | Pose coordinate decoding is a separate transform step. | Route transform details to `../data-transforms-datasets/` and use pose heatmap-to-coordinate helpers. |
| Tracking model alone does not track a video | The registry returns the SiamRPN network only. | Build the tracker with tracking utilities and provide frames plus an initial bounding box; route command/script work to `../training-evaluation-scripts/`. |
| Cython bbox/RPN extension import or performance issue | Optional Cython extensions were not built. | Most API workflows can run without them. For workflows requiring speed or a specific native extension, rebuild/install GluonCV with Cython available and the relevant extension build flag. |
| `PIL.Image.LINEAR` or Torch/Pillow error while doing MXNet work | Importing all GluonCV surfaces can touch PyTorch-side legacy code in some environments. | Use a legacy-compatible Pillow (`Pillow<10`) if importing Torch subpackages; otherwise restrict the task to MXNet imports. |

## Pretrained/cache policy

Default safe policy:

```python
net = get_model(name, pretrained=False, pretrained_base=False)
net.initialize(ctx=ctx)
```

Pretrained policy when allowed:

```python
net = get_model(name, pretrained=True, ctx=ctx)
# or, for documented alternate weights:
net = get_model(name, pretrained='hashstring', ctx=ctx)
```

Remember:

- `pretrained=True` may download into the MXNet model cache.
- `root` controls the model-cache location when constructors support it.
- A string `pretrained` value selects a documented weight hash, not a local path.
- For custom parameter files, use `pretrained=False` and `net.load_parameters(params_file, ctx=ctx)`.

## Custom class decision tree

1. Does the target model already have a pretrained detector whose old classes overlap the desired classes?
   - Yes: instantiate pretrained and call `reset_class(new_classes, reuse_weights=...)`.
   - No: instantiate a `_custom` model with `classes=[...]`, initialize/load your own parameters, then train/fine-tune.
2. Are the new class names identical to old class names?
   - Yes: a list reuse form is concise: `reuse_weights=['person', 'car']`.
   - No: use a dict mapping new class names/indices to old names/indices.
3. Are you trying to skip training for truly new labels?
   - Do not. `reuse_weights` cannot create a useful classifier for labels absent from the old model.

## Minimal recovery snippets

Import recovery:

```bash
python - <<'PY'
import numpy
print('numpy', numpy.__version__)
import mxnet as mx
print('mxnet', mx.__version__)
import gluoncv
print('gluoncv', gluoncv.__version__, gluoncv._found_mxnet)
PY
```

Registry recovery:

```bash
python scripts/mxnet_model_inventory.py --filter mask_rcnn --names --limit 20
```

Context recovery:

```python
ctx = mx.cpu()
net = get_model('cifar_resnet20_v1', pretrained=False)
net.initialize(ctx=ctx)
x = mx.nd.zeros((1, 3, 32, 32), ctx=ctx)
y = net(x)
```
