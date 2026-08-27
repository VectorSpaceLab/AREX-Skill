# MXNet model-zoo workflows

Use these recipes to complete common MXNet GluonCV model-zoo tasks without reopening the source repository.

## Registry inventory

The MXNet registry is exposed by `gluoncv.model_zoo.get_model_list()` and verified with 332 names. Names are lowercase in the registry; `get_model()` lowercases the input before lookup.

Safe inventory commands:

```bash
python scripts/mxnet_model_inventory.py --count
python scripts/mxnet_model_inventory.py --names --filter resnet50
python scripts/mxnet_model_inventory.py --model yolo3_darknet53_coco
python scripts/mxnet_model_inventory.py --dry-forward
```

`--dry-forward` runs only the tiny CPU `cifar_resnet20_v1` path with `pretrained=False`; it does not download weights.

## Model-name families

| Task | Common registry patterns | Notes |
| --- | --- | --- |
| CIFAR classification | `cifar_resnet*_v1`, `cifar_resnet*_v2`, `cifar_wideresnet*`, `cifar_resnext*`, `cifar_residualattentionnet*` | Tiny enough for CPU smoke checks. `cifar_resnet20_v1` is the verified no-download forward case. |
| ImageNet classification | `resnet*_v1`, `resnet*_v2`, `resnet*_v1b/v1c/v1d/v1e/v1s`, `resnest*`, `resnext*`, `se_*`, `senet_154`, `mobilenet*`, `mobilenetv2_*`, `mobilenetv3_*`, `vgg*`, `densenet*`, `squeezenet*`, `googlenet`, `alexnet`, `inceptionv3`, `xception`, `nasnet_*`, `dla34`, `darknet53`, pruned names such as `resnet50_v1d_0.48` | Standard 224x224 image models except families such as Inception/NASNet that expect larger canonical image sizes. |
| Quantized/int8 | `mobilenet1.0_int8`, `resnet50_v1_int8`, detection/segmentation/pose/action names ending `_int8` | Int8 models are calibrated variants. Treat as pretrained/model-cache workflows unless running explicit quantization tests. |
| Object detection | `ssd_*_{voc,coco,custom}`, `yolo3_*_{voc,coco,custom}`, `faster_rcnn_*_{voc,coco,custom}`, `center_net_*_{voc,coco}` | Detector outputs are `(ids, scores, bboxes)` for SSD/YOLO/Faster R-CNN/CenterNet. `set_nms()` is available on major detector classes. |
| Instance segmentation | `mask_rcnn_*_coco`, `custom_mask_rcnn_fpn` | Mask R-CNN outputs include masks in addition to ids/scores/boxes. Class reset shares the detector `reset_class()` pattern. |
| Semantic segmentation | `fcn_*`, `psp_*`, `deeplab_*`, `deeplab_v3b_plus_*`, `icnet_*`, `fastscnn_*`, `danet_*` | Names encode architecture, backbone, and dataset (`voc`, `coco`, `ade`, `citys`, `mhpv1`). Forward output may be a list/tuple; validate primary tensor shape. |
| Pose estimation | `simple_pose_*`, `mobile_pose_*`, `alpha_pose_*`, int8 pose names | Pose models emit heatmaps. Full person-detection-to-pose pipelines also use data transforms and visualization helpers from `../data-transforms-datasets/`. |
| MXNet action recognition | `vgg16_*`, `inceptionv*_ucf101/hmdb51/kinetics400/sthsthv2`, `c3d_*`, `p3d_*`, `r2plus1d_*`, `i3d_*`, `slowfast_*`, `resnet*_v1b_*`, custom action names | MXNet video models live here. PyTorch action recognition and config-driven workflows route to `../torch-video-workflows/`. |
| Depth | `monodepth2_resnet18_*_640x192`, `monodepth2_resnet18_posenet_*` | Monodepth2 examples use `model.predict(...)` and depth-specific postprocessing. Full video/image demos are data-heavy. |
| Tracking | `siamrpn_alexnet_v2_otb15` | Registry gives the network; source demos build a tracker around it. Full tracking demos need OpenCV and videos/frames. |
| Niche script-heavy areas | GAN, Re-ID, SMOT tracking internals | Mention only for routing unless the user asks for script command construction; route long command work to `../training-evaluation-scripts/`. |

## Dry-run instantiation, no downloads

Use dry-run paths when the user needs to confirm imports, a valid registry name, or output shape without network/model-cache assumptions.

```python
import mxnet as mx
from gluoncv.model_zoo import get_model

ctx = mx.cpu()
net = get_model('cifar_resnet20_v1', pretrained=False)
net.initialize(ctx=ctx)
x = mx.nd.random.uniform(shape=(1, 3, 32, 32), ctx=ctx)
y = net(x)
mx.nd.waitall()
assert tuple(y.shape) == (1, 10)
```

General no-download pattern for non-CIFAR models:

```python
net = get_model(model_name, pretrained=False, pretrained_base=False)
net.initialize(ctx=ctx)
# choose a small, task-appropriate input shape before forwarding
```

Cautions:

- Some constructors build large graphs even with `pretrained=False`; do not smoke-test every registry name unless the user accepts time/memory cost.
- `_custom` detector constructors require `classes=[...]`.
- Models containing `dcnv2` may need MXNet support for `ModulatedDeformableConvolution`.
- If a model has BatchNorm behavior that must use inference statistics, pass the source-backed `norm_layer`/`use_global_stats` pattern described in `api-reference.md`.

## Pretrained inference when network/cache is allowed

Use `pretrained=True` only when it is acceptable to use the MXNet model cache or download model parameters. Use `pretrained='<hash>'` when the docs list a specific parameter hash and the user needs that weight variant.

Classification sketch:

```python
from mxnet import nd, image
from gluoncv.data.transforms.presets.imagenet import transform_eval
from gluoncv.model_zoo import get_model

net = get_model('resnet50_v1d', pretrained=True)
img = image.imread('image.jpg')
x = transform_eval(img)
pred = net(x)
probs = nd.softmax(pred)[0]
```

Detection sketch:

```python
import mxnet as mx
from gluoncv.data.transforms import presets
from gluoncv.model_zoo import get_model

ctx = mx.cpu()
net = get_model('yolo3_darknet53_coco', pretrained=True, ctx=ctx)
net.set_nms(nms_thresh=0.45, nms_topk=200, post_nms=100)
x, img = presets.yolo.load_test('image.jpg', short=512)
x = x.as_in_context(ctx)
ids, scores, bboxes = [out[0] for out in net(x)]
```

Semantic segmentation sketch:

```python
net = get_model('fcn_resnet50_ade', pretrained=True, ctx=ctx)
# Feed an image tensor shaped (N, 3, H, W), commonly H=W=480 in tests.
out = net(x)
primary = out[0] if isinstance(out, (list, tuple)) else out
assert primary.shape[0] == x.shape[0]
```

Depth sketch:

```python
model = get_model('monodepth2_resnet18_kitti_mono_640x192', pretrained=True, ctx=ctx)
outputs = model.predict(x)  # depth recipes handle disparity/depth conversion separately
```

Tracking sketch:

```python
net = get_model('siamrpn_alexnet_v2_otb15', pretrained=True, ctx=mx.cpu())
# Build the tracker with GluonCV's SiamRPN tracker utilities before processing frames.
```

## Custom classes and `reset_class()`

Use `reset_class()` when starting from an existing pretrained detector/segmenter-like model and the target classes overlap the old classes. The source tests cover SSD, YOLO, Faster R-CNN, and Mask R-CNN reset workflows with list and dict mappings.

```python
from gluoncv.model_zoo import get_model

net = get_model('ssd_300_vgg16_atrous_voc', pretrained=True)
net.reset_class(['bus', 'car', 'bird'], reuse_weights=['bus', 'car', 'bird'])
```

Accepted `reuse_weights` forms:

```python
net.reset_class(['person'], reuse_weights={'person': 'person'})  # new name -> old name
net.reset_class(['person'], reuse_weights={'person': 14})        # new name -> old index
net.reset_class(['person'], reuse_weights={0: 14})               # new index -> old index
net.reset_class(['person'], reuse_weights={0: 'person'})         # new index -> old name
net.reset_class(['person'], reuse_weights=['person'])            # same name in old and new lists
```

Common mistakes:

- `reuse_weights` only copies compatible old predictor weights. It does not train the new classes.
- Class names must match the old model's class names exactly for name-based reuse.
- Old indices are dataset-specific; for example VOC and COCO use different label orderings.
- Calling `reset_class()` before loading pretrained weights loses the chance to reuse the pretrained classifier head.

Use `_custom` constructors when building an untrained class head from the start:

```python
net = get_model('yolo3_darknet53_custom', classes=['helmet', 'vest', 'person'], pretrained=False)
net.initialize(ctx=ctx)
```

For YOLO custom constructors, `transfer='voc'` or `transfer='coco'` can initialize from a related pretrained detector when the environment may download/cache weights. For SSD/Faster R-CNN custom constructors, `transfer` appears in the factory signatures and should be treated as a transfer-initialization hint, not a substitute for training.

## Output shape validation

Use minimal shape checks rather than relying on visual demos:

| Family | Input examples from tests/docs | Validation signal |
| --- | --- | --- |
| CIFAR classifiers | `(1, 3, 32, 32)` | logits shape `(1, 10)` for `cifar_resnet20_v1` |
| ImageNet classifiers | `(N, 3, 224, 224)`; InceptionV3 uses 299; NASNet often 331 | logits batch dimension `N`; class count from `net.classes` or constructor `classes` |
| SSD/Faster R-CNN/Mask R-CNN | non-square examples such as `(1, 3, 512, 544)` or `(1, 3, 300, 400)` | tuple outputs; first dimension matches batch; boxes use `[xmin, ymin, xmax, ymax]` style downstream |
| YOLO/CenterNet | examples around 320, 416, 512, or 608 resolution | tuple outputs `(ids, scores, bboxes)`; tune `set_nms()` for postprocessing |
| Segmentation | `(1, 3, 480, 480)`; custom-size tests use `(1, 3, H, W)` | primary output `(N, classes, H, W)` for custom-size FCN/PSP/DeepLab variants |
| Pose | simple/mobile pose around `(N, 3, 256, 192)` or variants | heatmap output; convert with pose transform helpers for coordinates |
| Action recognition | 2D models often `(N, 3, 224, 224)`; 3D models use `(N, 3, T, H, W)` | logits shape `(N, nclass)`; SlowFast and 3D models are expensive |
| Depth | image tensors resized to model resolution, e.g. 640x192 | model-specific prediction dictionary or depth/disp tensors |
| Tracking | frame arrays plus initial bbox via tracker utilities | tracker output dictionary with `bbox` and score-like fields |

## Source-script decisions

This sub-skill adapts only a safe model inventory helper. The following source scripts are reference-only here:

- Classification demos: show transform and inference patterns, but require images and optional pretrained weights.
- Detection, instance, pose, depth, and tracking demos: require images/videos, OpenCV or visualization, and often download sample data/weights.
- Training/evaluation scripts across classification, detection, segmentation, pose, action recognition, depth, and tracking: long-running, dataset/GPU/network-dependent; route command generation to `../training-evaluation-scripts/`.
- AutoGluon, deployment, export, ONNX, and TVM paths: route to `../automl-deployment-export/`.

## Export-adjacent model choice

When a user asks about export but starts with only a model name:

1. Validate that the model name exists in the MXNet registry with this sub-skill.
2. Confirm the task is truly export/deployment, not just model instantiation.
3. Route export command/prerequisite handling to `../automl-deployment-export/`.
4. Preserve that export generally needs MXNet, a supported model, and pretrained or locally loaded parameters; do not download weights unless the user permits it.
