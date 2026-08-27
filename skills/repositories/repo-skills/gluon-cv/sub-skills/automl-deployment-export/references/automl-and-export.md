# AutoML and deployment export reference

This reference covers two optional GluonCV surfaces:

1. `gluoncv.auto` AutoGluon-backed task wrappers for image classification/prediction and object detection.
2. Deployment/export utilities for MXNet model-zoo networks, with notes for ONNX, TVM, DirectPose, and quantized/int8 inference.

Treat both as optional. A working base `import gluoncv` does not guarantee that AutoGluon, `timm`, ONNX, TVM, MXNet-MKL, GPU packages, pretrained weights, or COCO tooling are present.

## Optional dependency map

| Surface | Required packages beyond base GluonCV | Practical compatibility notes |
| --- | --- | --- |
| `gluoncv.auto.tasks` | `autogluon.core`; the package extra pins `autogluon.core==0.3.1` | This is an old AutoGluon stack. Prefer Python versions compatible with that pin rather than forcing it into a modern environment. |
| MXNet-backed AutoML | `autogluon.core`, MXNet `>=1.4,<2.0`, GluonCV model zoo | Legacy MXNet usually needs NumPy below the breaking `np.bool` removal era. Use CPU only for tiny sanity checks; real training is slow. |
| Torch/timm AutoML image classification | `autogluon.core`, `torch`, `timm` | `ImageClassification` gives `timm` model names priority when both `torch` and `timm` are importable. Old AutoGluon may constrain the usable Torch/Python combination. |
| Object detection AutoML | `autogluon.core`, MXNet, GluonCV detection estimators, optionally `pycocotools` for COCO data | Default transfer models are pretrained detector names, so training may need network/cache access for weights. |
| MXNet symbol/params export | MXNet, `gluoncv.model_zoo`, pretrained weights/cache, `gluoncv.utils.export_block` | Export writes deployment files and may download weights when `pretrained=True`. Validate the model name first. |
| ONNX export/inference | MXNet ONNX export support, `onnx`, `onnxruntime` | Export is a second stage after MXNet symbol/params export. Older released MXNet versions may not support many operators. |
| MXNet TVM export | `tvm`, MXNet, model weights/cache | `export_tvm` requires a fixed `data_shape` and writes TVM library/graph/params artifacts. |
| DirectPose TVM export | Torch, TorchVision, TVM, GluonCV Torch DirectPose config/model, custom TVM NMS converter | Requires TorchScript tracing and `cfg.CONFIG.MODEL.TVM_MODE=True`; often GPU/network/cache heavy. |
| Quantized/int8 inference | MXNet quantization support, often MXNet-MKL/MKLDNN, compatible CPU hardware for speedups | Use model names and script flags that explicitly support quantized/int8 paths. Accuracy/performance claims are hardware- and calibration-dependent. |

## AutoML task wrappers

Import task wrappers from `gluoncv.auto.tasks`:

```python
from gluoncv.auto.tasks import ImageClassification, ImagePrediction, ObjectDetection
```

Available task classes:

- `ImageClassification`: image classification HPO/training wrapper.
- `ImagePrediction`: subclass alias of `ImageClassification`; useful when code or docs use the older prediction name.
- `ObjectDetection`: object detector HPO/training wrapper over SSD, YOLOv3, Faster R-CNN, and CenterNet estimators.

When `gluoncv.auto.tasks` imports successfully, it emits a warning that the Auto module was planned for deprecation in favor of AutoGluon Vision. Treat the API as legacy and optional.

### Config defaults and GPU fallback

Both task constructors accept `config=None` or a dict-like config. If no config is supplied, they select a config based on detected resources from AutoGluon's scheduler resource helpers.

Image classification defaults:

- `LiteConfig`: model search over `resnet18`, `mobilenetv3_small_100`, `visformer_tiny`; `num_trials=1`; `epochs=5`; `batch_size=8`; `ngpus_per_trial=0`.
- `DefaultConfig`: model search over `resnet50`, `efficientnet_b0`, `visformer_small`; `num_trials=3`; `epochs=15`; `batch_size=16`; `ngpus_per_trial=8`.

Object detection defaults:

- `LiteConfig`: transfer search over `ssd_512_mobilenet1.0_coco` and `yolo3_mobilenet1.0_coco`; `num_trials=1`; `epochs=5`; `ngpus_per_trial=0`.
- `DefaultConfig`: transfer search over `ssd_512_resnet50_v1_coco`, `yolo3_darknet53_coco`, `faster_rcnn_resnet50_v1b_coco`, and `center_net_resnet50_v1b_coco`; `num_trials=3`; `epochs=10`; `ngpus_per_trial=8`.

Resource behavior to preserve:

- If no GPU is detected or allowed, constructors log that they are using the most conservative search space and select `LiteConfig`.
- If a config asks for more GPUs than detected, requested GPUs are capped to the detected count and a warning is logged.
- If `dist_ip_addrs` is supplied, the constructor expects explicit `nthreads_per_trial` and `ngpus_per_trial`; do not rely on automatic local resource inference for distributed workers.
- CPU-only AutoML is acceptable for tiny correctness experiments, but it is usually too slow for real image/detection training.

### ImageClassification and ImagePrediction patterns

Minimal pattern:

```python
from gluoncv.auto.tasks import ImageClassification

train, val, test = ImageClassification.Dataset.from_folders(
    "data/images",
    train="train",
    val="val",
    test="test",
)

task = ImageClassification({
    "model": "resnet18_v1",
    "num_trials": 1,
    "epochs": 1,
    "batch_size": 8,
    "ngpus_per_trial": 0,
})
classifier = task.fit(train, val, time_limit=3600)
print(task.fit_summary())
classifier.save("classifier.pkl")
classifier = ImageClassification.load("classifier.pkl")
```

Key methods and return values:

- `task.fit(train_data, val_data=None, train_size=0.9, random_state=None, time_limit=None)` returns an estimator.
- If `val_data` is omitted and `train_data` is a pandas/DataFrame-backed task dataset, it splits by `train_size`.
- `time_limit` must be an integer number of seconds or `None`.
- `task.fit_summary()` returns a shallow copy of the best summary, including fields such as train/validation accuracy, total time, and best config when available.
- `task.fit_history()` returns scheduler/HPO history when multiple trials are run.
- Use the estimator's `predict`, `predict_feature`, `evaluate`, `save`, and estimator/task `load` methods after `fit`.

Model dispatch behavior:

- If `custom_net` is supplied, it must be either a Torch `torch.nn.Module` when `torch`/`timm` are available, or an MXNet `mx.gluon.Block` when MXNet is available.
- Without `custom_net`, `ImageClassification` checks `timm.list_models()` when `torch` and `timm` are present and checks `gluoncv.model_zoo.get_model_list()` when MXNet is present.
- `timm` has priority when a model name is found in both worlds.
- A model-name failure often means that the name belongs to the backend that is not installed; install the missing backend only if the legacy dependency stack can support it.

Dataset entry points:

- `ImageClassification.Dataset.from_folder(root, exts=...)` for class-per-folder data.
- `ImageClassification.Dataset.from_folders(root, train='train', val='val', test='test', exts=...)` for split class folders.
- `ImageClassification.Dataset.from_csv(csv_file, root=None, image_column='image', label_column='label')` for tabular path/label lists.
- `random_split(test_size=..., val_size=...)` returns train/validation/test dataframes.

For deeper layout validation and custom records, route to `../data-transforms-datasets/`.

### ObjectDetection patterns

Minimal pattern:

```python
from gluoncv.auto.tasks import ObjectDetection

train = ObjectDetection.Dataset.from_voc("data/VOC2007")
train, val, test = train.random_split(val_size=0.1, test_size=0.1)

task = ObjectDetection({
    "num_trials": 1,
    "epochs": 1,
    "batch_size": 4,
    "ngpus_per_trial": 0,
    "transfer": "ssd_512_mobilenet1.0_coco",
})
detector = task.fit(train, val, time_limit=3600)
print(task.fit_summary())
detector.save("detector.pkl")
detector = ObjectDetection.load("detector.pkl")
```

Key object-detection config fields:

- `estimator`: may constrain search to one detector family, such as `ssd`, `yolo3`, `faster_rcnn`, or `center_net`.
- `transfer`: pretrained detection model name(s) used for transfer learning. If `estimator` and `transfer` are both provided, the task filters transfer names to those matching the estimator string.
- `base_network`: used by several estimator configs when not using a full transfer name.
- `batch_size`, `epochs`, `lr`, `momentum`, `wd`, `num_trials`, `search_strategy`, and AutoGluon search spaces (`ag.Categorical`, `ag.Int`, `ag.Real`) follow AutoGluon conventions.

Key object-detection methods and data:

- `task.fit(...)` returns a detector estimator.
- `task.fit_summary()` reports fields such as train/validation mAP, total time, and best config.
- `task.fit_history()` returns scheduler/HPO details.
- `ObjectDetection.load(filename)` asserts that the saved estimator is an SSD, YOLOv3, Faster R-CNN, or CenterNet estimator.
- `ObjectDetection.Dataset.from_voc(root, splits=None)` expects Pascal VOC-style `JPEGImages`, `Annotations`, and optional `ImageSets/Main` files.
- `ObjectDetection.Dataset.from_coco(anno_file, root=None, ...)` requires `pycocotools` and valid COCO image paths.

For object-detection annotation schema checks and bbox conventions, route to `../data-transforms-datasets/`.

## MXNet pretrained export

The simple pretrained export workflow is:

```python
import gluoncv as gcv

net = gcv.model_zoo.get_model("resnet18_v1", pretrained=True)
gcv.utils.export_block("resnet18_v1", net, preprocess=True, layout="HWC")
```

The command-style export helper in GluonCV performs the same pattern from a model name:

```bash
python export_pretrained.py --model resnet18_v1
```

In this generated skill, do not rely on the original helper script. Use the bundled checker first:

```bash
python scripts/export_name_check.py --model resnet18_v1
```

Only proceed to real export when all of these are true:

1. MXNet imports in a version accepted by GluonCV.
2. `gluoncv.model_zoo.get_model_list()` contains the model name.
3. Network/cache access for pretrained weights is explicitly allowed or the weights are already cached.
4. The requested model is a hybridizable MXNet model compatible with `export_block`.
5. The output directory may receive generated deployment files.

### `export_block` behavior

Signature:

```python
gluoncv.utils.export_block(
    path,
    block,
    data_shape=None,
    epoch=0,
    preprocess=True,
    layout="HWC",
    ctx=mx.cpu(),
)
```

Important behavior:

- Writes `path-symbol.json` and `path-0000.params` for `epoch=0`.
- Exports a `HybridBlock`/hybridizable block. Plain non-hybridizable Gluon Blocks may fail.
- If `preprocess=True`, the exported graph prepends default GluonCV preprocessing: subtract mean `[123.675, 116.28, 103.53]`, divide by std `[58.395, 57.12, 57.375]`, and transpose raw RGB input from HWC to CHW.
- Default preprocess requires `layout='HWC'` and expects raw image values in `[0, 255]`.
- If `preprocess=None` or otherwise disabled, use `layout='CHW'` for 2D models or `layout='CTHW'` for 3D/video models, and perform preprocessing outside the exported graph.
- If `data_shape` is omitted for HWC/CHW, export tries common square sizes. For segmentation, video, and unusual networks, set `data_shape` explicitly.

Common `data_shape`/layout hints:

| Model family | Export hint |
| --- | --- |
| Standard 2D classification/detection | Often works with `preprocess=True`, `layout='HWC'`, and omitted `data_shape`; specify `(224, 224, 3)`, `(512, 512, 3)`, etc. when needed. |
| Segmentation (`deeplab`, `psp`, `icnet`, `fcn`) | Prefer fixed `data_shape`, such as `(480, 480, 3)`, matching the intended input size. |
| 3D action models | Use `preprocess=None`, `layout='CTHW'`, and explicit shapes such as `(3, 32, 224, 224)` for many 3D models. |
| R(2+1)D | Use an explicit shape such as `(3, 16, 112, 112)` when appropriate. |
| SlowFast | Requires family-specific temporal shapes; examples include `(3, 36, 224, 224)` for 4x16 and `(3, 40, 224, 224)` for 8x8 style inputs. |
| Faster R-CNN | Export can require special handling of target-generator internals; validate with a real smoke only when pretrained weights are available. |
| Known difficult or skipped families | GroupNorm/DCNv2, SiamRPN, DANet/FastSCNN, some Monodepth, and some segmentation variants may not export cleanly through the generic helper. |

## ONNX workflow

ONNX is not the same as MXNet JSON/params export. The source pattern is:

1. Create/load a pretrained GluonCV MXNet model with `gluoncv.model_zoo.get_model(name, pretrained=True)`.
2. Export symbol/params with `gluoncv.utils.export_block(...)`.
3. Convert symbol/params to ONNX with `mxnet.contrib.onnx.export_model(...)`.
4. Validate inference using `onnxruntime.InferenceSession` and the session input name.

ONNX caveats:

- Older released MXNet versions may not support all operators needed by GluonCV models.
- 2D exported ONNX models may include preprocessing layers, but the caller still needs to resize/crop inputs to the expected shape.
- Detection output ordering can differ by model family; CenterNet-style outputs differ from many SSD/YOLO outputs.
- Video/action ONNX checks may require `decord` and real video fixtures; treat them as optional.

## TVM workflows

### MXNet `export_tvm`

`gluoncv.utils.export_tvm(path, block, data_shape, epoch=0, preprocess=True, layout='HWC', ctx=mx.cpu(), target='llvm', opt_level=3, use_autotvm=False)` exports TVM deployment artifacts.

Important notes:

- `tvm` must be installed.
- `data_shape` is required because TVM optimization needs fixed shapes.
- `use_autotvm=True` can be very slow because it tunes kernels.
- Output includes a runtime library, graph JSON, and params; treat it as a side-effecting deployment operation.

### Torch DirectPose TVM

DirectPose TVM export is a Torch/TorchScript/TVM workflow:

- Build a DirectPose config with `get_cfg_defaults(name='directpose')`.
- Set `cfg.CONFIG.MODEL.NAME` for a pretrained DirectPose model or merge a custom config.
- Set `cfg.CONFIG.MODEL.PRETRAINED=True` and `cfg.CONFIG.MODEL.TVM_MODE=True` for the pretrained path.
- Build `model_zoo.get_model(cfg)`, move it to CPU/CUDA as appropriate, and run `eval()`.
- Trace with `torch.jit.trace` on a representative input.
- Use TVM Relay's PyTorch frontend with the custom `torchvision::nms` converter supplied by GluonCV's TVM utilities.

Treat DirectPose TVM as optional and heavy: it may require Torch, TorchVision, TVM, pretrained weights, real images, custom operator conversion, and GPU support for CUDA targets.

## Quantized/int8 deployment

Quantized/int8 support is an MXNet deployment surface. Do not assume every model supports it.

Source-backed candidate families include:

- ImageNet classification: `mobilenet1.0_int8`, `resnet50_v1_int8`.
- SSD detection: `ssd_300_vgg16_atrous_voc_int8`, `ssd_512_mobilenet1.0_voc_int8`, `ssd_512_resnet50_v1_voc_int8`, `ssd_512_vgg16_atrous_voc_int8`.
- Segmentation: `fcn_resnet101_voc_int8`, `fcn_resnet101_coco_int8`, `psp_resnet101_voc_int8`, `psp_resnet101_coco_int8`, `deeplab_resnet101_voc_int8`, `deeplab_resnet101_coco_int8`.
- Pose: `simple_pose_resnet18_v1b_int8`, `simple_pose_resnet50_v1b_int8`, `simple_pose_resnet50_v1d_int8`, `simple_pose_resnet101_v1b_int8`, `simple_pose_resnet101_v1d_int8`.
- Some 2D video/action names also have quantized evaluation recipes.

Common script flags and API ideas:

- In evaluation scripts, `--quantized` selects an int8 pretrained path when supported.
- `--deploy --model-prefix=...` loads an already exported static model.
- Calibration workflows use MXNet quantization APIs such as `mxnet.contrib.quantization.quantize_net(...)` with calibration data or data shapes.
- Calibration modes include `none`, `naive`, and `entropy`; `entropy` generally needs representative calibration data.
- CPU speedups depend on CPU instructions and MXNet/MKL-DNN support; do not claim performance without benchmarking on the target hardware.

## Safe decision checklist

Before answering or acting, decide:

- Is the user asking for programmatic AutoML training, script command construction, model-zoo selection, dataset validation, or deployment export?
- Which optional packages are actually required for the requested workflow?
- Will the operation train, download, export, compile, or write files? If yes, ask/confirm when the user has not authorized side effects.
- Is CPU acceptable as a correctness substitute, or is GPU/performance behavior central to the task?
- Can the task be answered with model-name validation and a prerequisite plan instead of running a heavy export?
