---
name: mxnet-model-zoo
description: "Choose, instantiate, customize, and smoke-check MXNet GluonCV
  model-zoo models."
disable-model-invocation: true
metadata:
  disco-role: operating
  parent-skill: gluon-cv
  source-framework: mxnet
  package: gluoncv
license: Apache 2.0
---

# MXNet GluonCV model zoo workflows

Use this sub-skill when the task mentions GluonCV's MXNet model zoo, `gluoncv.model_zoo.get_model`, pretrained MXNet models, model lists, MXNet inference, `reset_class`, SSD/YOLO/Faster R-CNN/Mask R-CNN/CenterNet, semantic or instance segmentation, pose, MXNet action recognition, depth, tracking, quantized/int8 variants, or MXNet import/version failures.

Verified operating facts:

- `gluoncv.model_zoo.get_model(name, **kwargs)` constructs MXNet GluonCV models by registry name.
- `gluoncv.model_zoo.get_model_list()` returns the MXNet registry; the verified registry contains 332 names.
- A CPU smoke check with `get_model('cifar_resnet20_v1', pretrained=False)`, initialized manually, returned output shape `(1, 10)` for input `(1, 3, 32, 32)`.
- `pretrained` accepts `False`, `True`, or a string hash selector. `True` or a hash may download weights into the MXNet model cache unless already present.

## Route first

Stay in this sub-skill for MXNet model-name selection, dry-run instantiation, pretrained inference recipes, output-shape checks, custom detector class heads, `reset_class`, model cache issues, and MXNet-specific compatibility problems.

Route elsewhere when the user's goal is not MXNet model-zoo API work:

- Dataset classes, transforms, presets, loaders, metrics, and annotation validation: `../data-transforms-datasets/`
- PyTorch action-recognition, DirectPose, COOT, Torch configs, and DDP: `../torch-video-workflows/`
- Full training/evaluation/demo command construction from source scripts: `../training-evaluation-scripts/`
- AutoGluon, export, deployment, ONNX/TVM, or programmatic export checks: `../automl-deployment-export/`

## Default workflow

1. Confirm the environment can import MXNet-backed GluonCV. If not, use `references/troubleshooting.md` before changing code.
2. Choose a model family and registry name with `references/model-zoo-workflows.md` or the bundled helper:

   ```bash
   python scripts/mxnet_model_inventory.py --filter yolo3 --names
   ```

3. For a no-network sanity check, instantiate with `pretrained=False`; initialize parameters before the first forward:

   ```python
   import mxnet as mx
   from gluoncv.model_zoo import get_model

   ctx = mx.cpu()
   net = get_model('cifar_resnet20_v1', pretrained=False)
   net.initialize(ctx=ctx)
   y = net(mx.nd.random.uniform(shape=(1, 3, 32, 32), ctx=ctx))
   assert tuple(y.shape) == (1, 10)
   ```

4. Use `pretrained=True` or `pretrained='<hash>'` only when network access or an existing model cache is acceptable.
5. For detector class changes, prefer a pretrained detector plus `reset_class(classes, reuse_weights=...)` when the new labels overlap the original dataset; otherwise instantiate a `_custom` model with `classes=[...]` and train/fine-tune normally.
6. Validate outputs by task family: classification logits `(N, classes)`, detection tuples `(ids, scores, bboxes)`, segmentation logits `(N, classes, H, W)` or list/tuple outputs, pose heatmaps, action logits, depth prediction dictionaries, and tracking tracker outputs.

## References

- `references/model-zoo-workflows.md` — model-name families and recipes for inventory, dry-run, pretrained inference, reset-class, and export-adjacent decisions.
- `references/api-reference.md` — verified signatures, kwargs, return conventions, and source-backed reset behavior.
- `references/troubleshooting.md` — import/version/cache/GPU/custom-class/Cython fixes.
- `scripts/mxnet_model_inventory.py` — safe inventory and tiny CPU dry-forward helper; it performs no downloads.

## Source notes

This sub-skill distills public API and behavior from `setup.py`, `README.md`, `docs/model_zoo`, `docs/tutorials/index.rst`, `gluoncv/model_zoo/model_zoo.py`, `tests/model_zoo/test_model_zoo.py`, and the source script families under `scripts/classification`, `scripts/detection`, `scripts/instance`, `scripts/pose`, `scripts/segmentation`, `scripts/action-recognition`, `scripts/depth`, and `scripts/tracking`. Long demo/train/eval scripts are treated as reference evidence because they require external images/videos/datasets, pretrained downloads, GPUs, or long-running jobs.
