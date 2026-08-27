# MXNet model-zoo API reference

This reference covers the MXNet side of GluonCV. PyTorch model-zoo APIs route to `../torch-video-workflows/`.

## Primary registry API

```python
from gluoncv.model_zoo import get_model, get_model_list

names = get_model_list()
net = get_model(name, **kwargs)
```

Verified facts:

- `get_model(name, **kwargs)` returns an MXNet `HybridBlock`/`Block` for a known registry name.
- `get_model_list()` returns the registry keys; the verified registry has 332 names.
- `get_model()` lowercases `name` and raises `ValueError` listing valid names if the name is unknown.
- Tiny verified forward: `cifar_resnet20_v1`, `pretrained=False`, manual initialization, input `(1, 3, 32, 32)`, output `(1, 10)` on CPU.

Source signature:

```python
def get_model(name, **kwargs): ...
def get_model_list(): ...
```

Documented `get_model` parameters:

| Parameter | Meaning | Operational notes |
| --- | --- | --- |
| `name` | Registry name string | Lowercased before lookup. Use `get_model_list()` or `scripts/mxnet_model_inventory.py` to validate. |
| `pretrained` | `False`, `True`, or string hash | `False` avoids model-weight downloads. `True` loads default pretrained weights. A string selects a specific pretrained hash when available. |
| `classes` | Number or iterable of class names depending on constructor | `_custom` detector constructors require a class-name iterable. Some classifiers accept integer class counts. |
| `ctx` | MXNet context such as `mx.cpu()` or `mx.gpu(0)` | Used for loading pretrained parameters and some constructors. If loading on CPU then moving to GPU, call `net.collect_params().reset_ctx(ctx)`. |
| `root` | Model cache directory, default `~/.mxnet/models` | Applies to pretrained parameter lookup/download. Avoid setting this unless the user needs an explicit cache. |
| `pretrained_base` | Whether to use/load pretrained backbone/base network | Common in detection, segmentation, pose, action, and depth factories. Set `False` for strict no-download dry runs. |
| `norm_layer`, `norm_kwargs` | BatchNorm/SyncBatchNorm override | Used in YOLO, ResNet variants, segmentation, sync-BN models, and training/eval scripts. |
| `use_global_stats` | BatchNorm inference-statistics control | Source tests verify custom BatchNorm receiving `use_global_stats=True` for ResNet-v1b-style models. |
| task-specific kwargs | e.g. `nclass`, `num_segments`, `num_crop`, `height`, `width`, `rcnn_max_dets`, `rpn_test_pre_nms`, `rpn_test_post_nms` | Use only when matching the chosen family; many are passed through `**kwargs`. |

## Pretrained model-list helper

`gluoncv.model_zoo.model_store.pretrained_model_list()` returns the model names that have pretrained weights. It is used by tests before deciding whether `pretrained=True` is available. Treat it as an internal support helper; the main public constructor remains `get_model()`.

## Classification factories

Examples from registry/factory signatures:

```python
get_model('cifar_resnet20_v1', pretrained=False)
get_model('resnet50_v1d', pretrained=True, ctx=mx.cpu())
get_model('resnet18_v1b', pretrained=False, norm_layer=mx.gluon.nn.BatchNorm)
get_model('mobilenet1.0_int8', pretrained=True)
```

Representative source signatures:

```python
def resnet18_v1b(pretrained=False, root='~/.mxnet/models', ctx=cpu(0), **kwargs): ...
def cifar_resnet20_v1(**kwargs): ...
def mobilenet1_0(**kwargs): ...
```

Rules of thumb:

- For no-download construction, pass `pretrained=False`; call `net.initialize(ctx=ctx)` before a forward.
- If loading custom parameters, instantiate with `pretrained=False` and then `net.load_parameters(path, ctx=ctx)`.
- Use `net.classes` when a pretrained classifier exposes labels; otherwise provide your own labels alongside output indices.

## Detection and instance-segmentation factories

Representative factory signatures:

```python
def ssd_300_vgg16_atrous_custom(classes, pretrained_base=True, pretrained=False, transfer=None, **kwargs): ...
def yolo3_darknet53_custom(classes, transfer=None, pretrained_base=True, pretrained=False, norm_layer=BatchNorm, norm_kwargs=None, **kwargs): ...
def faster_rcnn_resnet50_v1b_custom(classes, transfer=None, pretrained_base=True, pretrained=False, **kwargs): ...
def mask_rcnn_resnet50_v1b_coco(pretrained=False, pretrained_base=True, **kwargs): ...
def center_net_resnet18_v1b_voc(pretrained=False, pretrained_base=True, **kwargs): ...
```

Common detector calls:

```python
net = get_model('ssd_512_resnet50_v1_voc', pretrained=False, pretrained_base=False)
net = get_model('yolo3_darknet53_coco', pretrained=True, ctx=mx.cpu())
net = get_model('faster_rcnn_resnet50_v1b_custom', classes=['helmet', 'vest'], pretrained=False)
net = get_model('mask_rcnn_resnet50_v1b_coco', pretrained=True)
```

Detector postprocessing methods:

```python
net.set_nms(nms_thresh=0.45, nms_topk=200, post_nms=100)
ids, scores, bboxes = net(x)[:3]
```

`set_nms()` is tested for SSD, Faster R-CNN, and YOLO. CenterNet and Mask R-CNN have related task-specific output/postprocessing flows.

## `reset_class(classes, reuse_weights=None)`

Source implementations and tests cover SSD, YOLO, Faster R-CNN, and Mask R-CNN. The method resets class categories and class predictors.

Signature:

```python
def reset_class(self, classes, reuse_weights=None): ...
```

Parameters:

| Parameter | Meaning |
| --- | --- |
| `classes` | Iterable of new class names, e.g. `['person', 'car']`. |
| `reuse_weights` | Optional mapping/list that copies old class-predictor weights into the new head. |

Accepted `reuse_weights` forms:

```python
{'new_name': 'old_name'}
{'new_name': old_index}
{new_index: old_index}
{new_index: 'old_name'}
['same_name_0', 'same_name_1']
```

Examples:

```python
net = get_model('ssd_300_vgg16_atrous_voc', pretrained=True)
net.reset_class(['bus', 'car', 'bird'], reuse_weights=['bus', 'car', 'bird'])

net = get_model('faster_rcnn_resnet50_v1b_coco', pretrained=True)
net.reset_class(['person', 'car', 'bird'], reuse_weights={'person': 0, 'car': 'car'})
```

Operational semantics:

- Name-based reuse searches old and new class lists; a missing name raises `ValueError` or warns depending on the implementation branch.
- Index-based reuse validates old/new index bounds.
- SSD explicitly preserves background weights while remapping class weights.
- `reset_class()` changes the prediction head; it does not retrain weights for unseen classes.
- Load pretrained weights first when you need to reuse old class weights.

## Semantic segmentation factories

Representative signatures:

```python
def get_fcn(dataset='pascal_voc', backbone='resnet50', pretrained=False,
            root='~/.mxnet/models', ctx=cpu(0), pretrained_base=True, **kwargs): ...
```

Examples:

```python
net = get_model('fcn_resnet50_ade', pretrained=False, pretrained_base=False)
net = get_model('psp_resnet101_voc', pretrained=True, ctx=mx.cpu())
net = get_model('deeplab_resnet101_citys', pretrained=False, pretrained_base=True)
```

Custom-size source test pattern:

```python
from gluoncv.model_zoo import FCN, PSPNet, DeepLabV3

height, width, num_classes = 64, 96, 5
net = FCN(num_classes, backbone='resnet50', aux=False,
          ctx=ctx, pretrained_base=True, height=height, width=width)
result = net(mx.nd.random.uniform(shape=(1, 3, height, width), ctx=ctx))
assert result[0].shape == (1, num_classes, height, width)
```

Use `pretrained_base=False` for no-download tests. Use `pretrained_base=True` only when the base-weight behavior is acceptable.

## Pose factories

Common names:

```python
simple_pose_resnet18_v1b
simple_pose_resnet50_v1b
simple_pose_resnet101_v1d
mobile_pose_mobilenet1.0
mobile_pose_mobilenetv3_small
alpha_pose_resnet101_v1b_coco
simple_pose_resnet50_v1b_int8
```

Usage:

```python
pose_net = get_model('simple_pose_resnet50_v1b', pretrained=True)
heatmaps = pose_net(pose_input)
```

Full image-to-keypoints workflows also need detector outputs and pose transforms; route data transform details to `../data-transforms-datasets/`.

## MXNet action-recognition factories

Representative signature:

```python
def resnet18_v1b_kinetics400(nclass=400, pretrained=False, pretrained_base=True,
                             use_tsn=False, partial_bn=False, num_segments=1,
                             num_crop=1, root='~/.mxnet/models', ctx=mx.cpu(), **kwargs): ...
```

Examples:

```python
net = get_model('resnet18_v1b_kinetics400', pretrained=False, pretrained_base=False)
net = get_model('i3d_resnet50_v1_kinetics400', pretrained=True)
net = get_model('slowfast_4x16_resnet50_custom', nclass=12, pretrained=False)
```

Input conventions from tests:

- 2D-style action models use image-like tensors `(N, 3, H, W)`.
- 3D models such as C3D/R2+1D/I3D use clip tensors `(N, 3, T, H, W)`.
- SlowFast models are expensive and use model-specific temporal layouts; prefer shape-only or small CPU checks unless the user accepts cost.

## Depth and tracking APIs

Depth examples:

```python
net = get_model('monodepth2_resnet18_kitti_mono_640x192', pretrained=True, ctx=mx.cpu())
outputs = net.predict(x)
```

Tracking examples:

```python
net = get_model('siamrpn_alexnet_v2_otb15', pretrained=True, ctx=mx.cpu())
```

The model-zoo call returns the network. Full tracking needs tracker utilities, OpenCV video/frame loading, and an initial bounding box; keep the model-name validation here and route script-heavy command construction to `../training-evaluation-scripts/`.

## Initialization and context checklist

No pretrained weights:

```python
ctx = mx.cpu()
net = get_model(name, pretrained=False, pretrained_base=False)
net.initialize(ctx=ctx)
y = net(x.as_in_context(ctx))
mx.nd.waitall()
```

Pretrained weights:

```python
ctx = mx.cpu()
net = get_model(name, pretrained=True, ctx=ctx)
# If using a list of contexts later:
net.collect_params().reset_ctx([ctx])
```

Custom parameters:

```python
net = get_model(name, pretrained=False, pretrained_base=False)
net.load_parameters(params_file, ctx=ctx)
```

Avoid mixing CPU arrays with GPU-resident parameters. Put inputs and parameters on the same MXNet context.
