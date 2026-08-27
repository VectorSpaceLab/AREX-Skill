# Installation and compatibility

SSD.PyTorch is an older source-layout PyTorch repository. Treat it as a repository-specific codebase rather than a modern pip package.

## Import model

There is no `pyproject.toml`, `setup.py`, or requirements file in the source evidence. Future agents should make the repository modules importable by working in a checkout/copy or by adding the source root to `PYTHONPATH` in their own environment.

A minimal import smoke looks like:

```bash
python - <<'PY'
import torch, cv2, numpy
from ssd import build_ssd
net = build_ssd('train', 300, 21)
print(type(net).__name__, net.size, net.num_classes)
PY
```

If this fails before reaching `build_ssd`, check the COCO label-map caveat below.

## Core dependencies

Selected core workflows use:

- PyTorch (`torch`) and TorchVision.
- NumPy.
- OpenCV Python bindings (`cv2`).
- Pillow/PIL for `test.py` imports.

Optional workflow dependencies:

| Optional surface | Dependency |
|---|---|
| COCO dataset construction | `pycocotools` or usable `COCO_ROOT/PythonAPI` plus `coco_labels.txt` |
| Training loss visualization | `visdom` and a running Visdom server |
| Webcam demo | `imutils`, camera, OpenCV GUI/display support |
| Notebook demo | Jupyter/IPython and compatible pretrained weights |

Install only the optional dependency needed by the selected task.

## Known legacy issues

### Import-time COCO label map

The data package eagerly imports COCO classes, and `COCOAnnotationTransform()` opens a label map as a default argument. This can make even VOC-oriented imports fail with a missing `coco_labels.txt` error if the expected COCO label map is absent under the default user data root.

Mitigations:

- Put the label map where the runtime expects it.
- Patch the COCO dataset code in a local working copy to construct `COCOAnnotationTransform()` lazily.
- Use narrow imports only when they avoid package-level `data`, though many repository modules import `data` at top level.

### Modern PyTorch `Detect` failure

The inference/evaluation path uses `Detect`, an old-style `torch.autograd.Function` subclass with an instance `forward`. Modern PyTorch can raise:

```text
RuntimeError: Legacy autograd function with non-static forward method is deprecated.
```

`build_ssd('train')` and train-phase tensor-shape inspection may still work, but `build_ssd('test')` forward, `eval.py`, `test.py`, and demos need a ported `Detect` layer or a legacy-compatible PyTorch runtime before they are trusted.

### Python 3.13 argparse help failure

`train.py` creates an empty mutually exclusive group. On Python 3.13, formatting `train.py --help` can fail with a `ValueError` about an empty group. Remove the unused group in a local working copy or use the bundled training command planner for reviewed templates.

### NumPy `np.bool` in evaluation

`eval.py` uses `np.bool`, which is removed in newer NumPy releases. Full VOC evaluation on modern NumPy may need a local patch to use `bool` or `np.bool_`.

### Global default tensor type

The original scripts set the global default tensor type based on CUDA availability and the `--cuda` argument. Be explicit about CPU/CUDA intent and keep model parameters, inputs, priors, and targets on the same device.

## Safe smoke checks

From this skill directory, use:

```bash
python scripts/smoke_imports.py --build-model
```

From the model sub-skill, use:

```bash
python sub-skills/model-inference/scripts/check_box_utils.py
python sub-skills/model-inference/scripts/inspect_model_shapes.py --num-classes 21 --phase train --run-forward
```

These checks do not download datasets or weights. They assume the user's environment can import the repository modules.

## What is not verified by install/import checks

- README mAP values.
- VOC/COCO dataset download success.
- VGG base-weight download integrity.
- Full training completion.
- Full VOC mAP evaluation.
- Webcam access or GUI display.
- Notebook execution.

Use the sub-skills to plan those workflows and validate prerequisites before execution.
