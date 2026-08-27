# Vision Transforms, Model Factories, and Utilities

This reference summarizes installed `tllib` public surfaces for vision data/model plumbing. It is intentionally no-network by default: pass `pretrained=False` or `pretrained_backbone=False` unless the user explicitly wants pretrained weights and has a configured cache/network path.

## Version and compatibility baseline

TLLib 0.4 was written for older PyTorch/TorchVision APIs. If model imports fail on current TorchVision, see `troubleshooting.md` before changing code. A known-compatible baseline for broad vision import coverage is Python 3.8 with Torch 1.8-era and TorchVision 0.9-era APIs plus NumPy below 1.24.

## Classification transforms

Import:

```python
import torchvision.transforms as T
from tllib.vision.transforms import (
    ResizeImage,
    MultipleApply,
    Denormalize,
    NormalizeAndTranspose,
    DeNormalizeAndTranspose,
    RandomErasing,
)
```

Common patterns:

```python
train_transform = T.Compose([
    ResizeImage(256),
    T.RandomResizedCrop(224),
    T.RandomHorizontalFlip(),
    T.ToTensor(),
    T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

weak_strong = MultipleApply([weak_transform, strong_transform])
```

Contracts and caveats:

- `ResizeImage(size)` returns a square `(size, size)` output for integer `size`.
- `MultipleApply` returns a Python list, not a stacked tensor; downstream loops must unpack or collate accordingly.
- `RandomErasing` expects a tensor image shaped `(C, H, W)`, not a PIL image.
- `NormalizeAndTranspose` uses BGR-style mean values and changes `(H, W, C)` to `(C, H, W)`; use it for segmentation/model code that expects that convention, not generic ImageNet preprocessing.
- `DeNormalizeAndTranspose` expects a NumPy-like `(C, H, W)` input and returns RGB-style `(H, W, C)` data.

## Segmentation transforms

Import:

```python
from tllib.vision.transforms import segmentation as SegT
```

Pattern:

```python
transform = SegT.Compose([
    SegT.Resize((1024, 512)),
    SegT.RandomHorizontalFlip(p=0.5),
    SegT.ToTensor(),
    SegT.NormalizeAndTranspose(),
])
image, label = transform(image, label)
```

Contracts:

- Transforms receive and return `(image, label)` pairs.
- `Resize` uses bicubic interpolation for images and nearest-neighbor interpolation for labels.
- `RandomCrop` requires the input image to be larger than the crop in both dimensions.
- Wrapped classification transforms such as `ColorJitter`, `Normalize`, `ToTensor`, and `ToPILImage` keep the segmentation label unchanged.

## Keypoint transforms

Import:

```python
from tllib.vision.transforms import keypoint_detection as KptT
```

Pattern:

```python
transform = KptT.Compose([
    KptT.Resize(256),
    KptT.RandomRotation(30),
    KptT.ToTensor(),
])
image, metadata = transform(
    image,
    keypoint2d=keypoint_array,
    intrinsic_matrix=intrinsic_matrix,
)
```

Contracts:

- Keypoint transforms pass metadata as keyword arguments and return `(image, kwargs)`.
- `Resize` assumes square source images in its helper and scales keypoint coordinates plus camera intrinsics.
- `ResizePad` preserves aspect ratio by padding.
- Heatmap losses expect output/target shaped `(N, K, H, W)`.

## Classification model factories

Import:

```python
from tllib.vision.models import resnet18, resnet50, lenet, dtn
```

No-download examples:

```python
backbone = resnet50(pretrained=False)
features = backbone(images)       # feature map, not logits
head = backbone.copy_head()       # copy of original ImageNet-style FC layer
out_features = backbone.out_features

digit_backbone = lenet(num_classes=10)
digit_features = digit_backbone(gray_images)  # expects 1x28x28 input
```

Contracts and caveats:

- TLLib ResNet subclasses TorchVision ResNet but removes the final average-pool/flatten/classifier behavior from `forward`; it returns a 4D feature map.
- `ResNet.out_features` is the feature dimension before the original FC layer (`512` for ResNet-18/34, `2048` for ResNet-50+).
- `copy_head()` returns a copy of the original FC layer; most TLLib workflows instead wrap the backbone with `tllib.modules.Classifier` or a task-specific head.
- `pretrained=True` downloads TorchVision weights through `torch.hub`; avoid it in offline or deterministic checks.
- `lenet` expects grayscale `1x28x28` images and outputs a 500-dimensional feature vector. `dtn` expects RGB `3x32x32` images and outputs a 512-dimensional feature vector.

## Semantic segmentation model surface

Import:

```python
from tllib.vision.models.segmentation.deeplabv2 import deeplabv2_resnet101
```

No-download instantiation:

```python
model = deeplabv2_resnet101(num_classes=19, pretrained_backbone=False)
logits = model(images)  # shape roughly (N, num_classes, H/8, W/8)
```

Contracts:

- The model is DeepLabV2 with a ResNet-101 backbone and ASPP classifier.
- `pretrained_backbone=True` downloads a backbone checkpoint from a remote URL; use `False` for smoke tests.
- `get_parameters(lr)` returns parameter groups with lower LR for the backbone and higher LR for the classifier.
- Inputs are RGB-like tensors shaped `(N, 3, H, W)`; segmentation examples often use BGR mean normalization through `NormalizeAndTranspose`.

## Keypoint model and losses

Imports:

```python
from tllib.vision.models.keypoint_detection.pose_resnet import pose_resnet101, PoseResNet, Upsampling
from tllib.vision.models.keypoint_detection.loss import JointsMSELoss, JointsKLLoss
```

No-download pattern:

```python
model = pose_resnet101(num_keypoints=21, pretrained_backbone=False)
heatmaps = model(images)  # (N, K, H_heatmap, W_heatmap)
loss = JointsMSELoss()(heatmaps, target_heatmaps, target_weight=None)
```

Contracts:

- `pose_resnet101` builds a ResNet-101 feature extractor plus three deconvolution upsampling layers and a `1x1` heatmap head.
- `JointsMSELoss` and `JointsKLLoss` consume `(N, K, H, W)` heatmaps and optional `target_weight` shaped `(N, K)`.
- `JointsKLLoss` normalizes target heatmaps internally; use non-negative target heatmaps and consider `epsilon` for numerical stability.

## Re-identification model surface

See `reid-and-metrics.md` for detailed re-id dataset/metric behavior. The key imports are:

```python
from tllib.vision.models.reid.resnet import reid_resnet50
from tllib.vision.models.reid.identifier import ReIdentifier
```

Pattern:

```python
backbone = reid_resnet50(pretrained=False)
model = ReIdentifier(backbone, num_classes=751, finetune=True)
```

Contracts:

- Re-id ResNet changes stride in the final stage and omits one activation in forward.
- `ReIdentifier.forward` returns `(predictions, raw_features)` in training mode and normalized bottleneck features in eval mode.
- Some legacy re-id loss constructors allocate CUDA modules unconditionally; use the metrics/functions on CPU, but verify GPU availability before using those loss classes in training.

## Object detection model surface

Imports under `tllib.vision.models.object_detection` wrap Detectron2 components:

- `TLGeneralizedRCNN`
- `TLRetinaNet`
- `TLRPN`
- `TLRes5ROIHeads`
- `TLStandardROIHeads`
- VGG-style detection backbone helpers

Operational constraints:

- Detectron2 is an optional dependency, not part of the minimum TLLib install.
- Detectron2 wheels are tightly coupled to Torch, CUDA, Python, and compiler versions.
- These classes accept Detectron2's `batched_inputs` and config-registered components; they are not drop-in TorchVision detection models.
- If Detectron2 is not installed, treat object-detection support as documented/optional rather than broken core TLLib vision support.

## Classification and segmentation metrics

Import:

```python
from tllib.utils.metric import accuracy, binary_accuracy, ConfusionMatrix
```

Examples:

```python
top1, top5 = accuracy(logits, targets, topk=(1, 5))

cm = ConfusionMatrix(num_classes=3)
cm.update(target_pixels, predicted_pixels)
summary = cm.format(["road", "sidewalk", "building"])
```

Contracts:

- `accuracy` expects logits/probabilities shaped `(N, C)` and integer targets shaped `(N,)`.
- `ConfusionMatrix.update` expects integer target and prediction tensors with values in `[0, num_classes-1]`; invalid target labels are ignored.
- `ConfusionMatrix.compute` can produce `nan` for a class with no ground-truth/predicted pixels. Handle empty classes before comparing mIoU.

## Keypoint metrics

Import:

```python
from tllib.utils.metric import keypoint_detection as KptMetric
```

Main functions:

- `get_max_preds(batch_heatmaps)` returns predicted coordinates and max values from heatmaps shaped `(N, K, H, W)`.
- `accuracy(output, target, hm_type='gaussian', thr=0.5)` returns per-keypoint accuracy, average accuracy, valid count, and predictions.

Use NumPy arrays, not Torch tensors, for these functions.

## Data, meters, schedulers, and logging

Imports:

```python
from tllib.utils.data import ForeverDataIterator, CombineDataset, send_to_device, concatenate
from tllib.utils.meter import AverageMeter, AverageMeterDict, Meter, ProgressMeter
from tllib.utils.logger import TextLogger, CompleteLogger
from tllib.utils.scheduler import WarmupMultiStepLR
```

Contracts:

- `ForeverDataIterator(loader, device=None)` restarts the loader after `StopIteration` and optionally sends nested tensors to a device.
- `CombineDataset([d1, d2])` returns list-spliced items and has length equal to the shortest inner dataset.
- `send_to_device` recursively moves tensors in lists, tuples, and dictionaries.
- `concatenate` concatenates tensors, lists of tensors, or dictionaries of tensors batch-wise.
- `AverageMeter` stores current, sum, count, and average values for console reporting.
- `CompleteLogger` redirects both stdout and stderr to a log file and creates checkpoint/visualization directories. Always call `close()` or restore streams after use in notebooks and tests.
- `WarmupMultiStepLR` applies linear or constant warmup followed by milestone decay.

## No-network smoke check

Run the bundled smoke script from any directory:

```bash
python /path/to/vision-data-models/scripts/tllib_vision_smoke.py
```

Expected successful signals:

- `tllib` imports from the installed environment.
- A temporary local `ImageList` loads a tiny image.
- `lenet`, `resnet18`, and `deeplabv2_resnet101(pretrained_backbone=False)` instantiate/forward where safe without downloads.
- Classification, segmentation/keypoint/re-id metric helpers run on tiny arrays/tensors.
- Detectron2-dependent object detection import is either available or explicitly reported as optional-skip.
