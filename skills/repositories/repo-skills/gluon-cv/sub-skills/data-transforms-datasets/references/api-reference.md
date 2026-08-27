# API reference: data transforms, batchify, loaders, metrics, and visualization

This page captures stable operating facts for GluonCV 0.11 data APIs. Prefer these facts over memory when diagnosing dataset/transform issues.

## Coordinate and tensor conventions

- Detection labels used by GluonCV transforms are NumPy arrays shaped `(N, 4+)` with coordinate columns `[xmin, ymin, xmax, ymax]`. Extra columns such as class id and `difficult` are preserved by bbox transforms.
- Pixel boxes are zero-based and absolute unless a dataset explicitly normalizes and then restores them.
- Width/height tuples in bbox APIs are `(width, height)`. Image arrays are HWC `(height, width, channels)`.
- MXNet image transform helpers generally expect `mxnet.nd.NDArray` in HWC layout and return MXNet NDArrays unless documented otherwise.
- Bbox transforms copy input arrays before changing coordinates; do not rely on in-place mutation.

## Bounding-box transforms: `gluoncv.data.transforms.bbox`

| API | Signature | Behavior and gotchas |
| --- | --- | --- |
| `crop` | `crop(bbox, crop_box=None, allow_outside_center=True)` | `crop_box` is `(xmin, ymin, width, height)`. Coordinates are clipped to the crop and shifted so the crop origin is `(0, 0)`. When `allow_outside_center=False`, boxes whose centers lie outside the crop are removed. Invalid zero-area boxes after clipping are removed. |
| `flip` | `flip(bbox, size, flip_x=False, flip_y=False)` | `size` is `(width, height)`. `flip_x=True` is horizontal; `flip_y=True` is vertical. |
| `resize` | `resize(bbox, in_size, out_size)` | `in_size` and `out_size` are `(width, height)`. Scales x columns by output/input width and y columns by output/input height. |
| `translate` | `translate(bbox, x_offset=0, y_offset=0)` | Adds offsets to both corners; it does not clip to image bounds. |
| affine helpers | `get_affine_transform`, `affine_transform`, `get_rot_dir`, `get_3rd_point` | Used by CenterNet/pose-style preprocessing. Requires OpenCV via GluonCV/MXNet helper paths. |

Verified smoke facts from unit tests:

```python
import numpy as np
from gluoncv.data import transforms
bbox = np.array([[10, 20, 200, 500], [150, 200, 400, 300]], dtype=np.float32)
transforms.bbox.resize(bbox, (600, 1000), (200, 300)).shape  # (2, 4)
transforms.bbox.flip(bbox, (500, 1000), flip_x=True).shape   # (2, 4)
```

## Image transforms: `gluoncv.data.transforms.image`

| API | Signature | Behavior and gotchas |
| --- | --- | --- |
| `imresize` | `imresize(src, w, h, interp=1)` | Namespace-consistent wrapper around MXNet image resize. Width and height are separate args. |
| `resize_long` | `resize_long(src, size, interp=2)` | Resizes the longer edge to `size`, preserving aspect ratio. |
| `resize_short_within` | `resize_short_within(src, short, max_size, mult_base=1, interp=2)` | Resizes the shorter edge to `short` but caps the longer edge at `max_size`; rounds to a multiple of `mult_base`. Useful for detector validation/inference. |
| `random_pca_lighting` | `random_pca_lighting(src, alphastd, eigval=None, eigvec=None)` | Adds PCA lighting noise to float image arrays. No-op when `alphastd <= 0`. |
| `random_expand` | `random_expand(src, max_ratio=4, fill=0, keep_ratio=True)` | Places image on a larger canvas and returns `(image, (offset_x, offset_y, new_width, new_height))`; pair with bbox `translate` or crop logic. |
| `random_flip` | `random_flip(src, px=0, py=0, copy=False)` | Returns `(image, (flip_x, flip_y))`; pair with bbox/mask/pose flip functions. |
| `resize_contain` | `resize_contain(src, size, fill=0)` | Fits image into a canvas of `(width, height)` and returns `(image, (offset_x, offset_y, scaled_x, scaled_y))`. |
| `ten_crop` | `ten_crop(src, size)` | Returns 10 crops shaped `(10, size[1], size[0], C)` in order: center, four corners, then their horizontal flips. Raises if crop is larger than input. |

## Mask, pose, and video transforms

| Module | Useful APIs | Notes |
| --- | --- | --- |
| `gluoncv.data.transforms.mask` | `flip`, `resize`, `to_mask`, `fill` | Keep mask polygons synchronized with bbox/image operations for instance segmentation. |
| `gluoncv.data.transforms.pose` | `flip_heatmap`, `flip_joints_3d`, `get_affine_transform`, `crop`, `detector_to_simple_pose`, `heatmap_to_coord` | Pose transforms include affine/heatmap conversion and detector-to-pose crop utilities. Many helpers require MXNet and sometimes OpenCV. |
| `gluoncv.data.transforms.video` | `VideoGroupTrainTransform`, `VideoGroupValTransform`, `VideoToTensor`, `VideoNormalize`, `VideoRandomHorizontalFlip`, `ShortSideRescale`, `RandomResizedCrop`, `VideoMultiScaleCrop`, `VideoCenterCrop`, `VideoThreeCrop`, `VideoTenCrop`, V2/V3/V4 train/val variants | Video transforms operate on groups of frames/clips. Confirm output shape before choosing a model or batchify. |
| `gluoncv.data.transforms.block` | `RandomCrop`, `RandomErasing` | MXNet Gluon `Block` transforms for image augmentation. |
| `gluoncv.data.transforms.experimental` | `bbox.random_crop_with_constraints`, `image.random_color_distort`, `image.np_random_color_distort` | Useful for augmentation but more version-sensitive; treat as lower-level helpers. |

## Preset transforms

Preset transforms encode detector/model-specific preprocessing and target generation. They should be paired with the matching model family and batchify function.

| Preset module | APIs | Inputs and pairings |
| --- | --- | --- |
| `presets.ssd` | `SSDDefaultTrainTransform(width, height, anchors=None, mean=..., std=..., iou_thresh=0.5, box_norm=(0.1,0.1,0.2,0.2), **kwargs)`, `SSDDefaultValTransform(width, height, mean=..., std=...)`, `transform_test(imgs, short, max_size=1024, ...)`, `load_test(filenames, short, max_size=1024, ...)` | Training transform needs anchors for target generation; obtain anchors from an SSD network dry forward. Validation pairs with `Tuple(Stack(), Pad(pad_val=-1))`; training commonly stacks image/class/box targets. |
| `presets.rcnn` | `FasterRCNNDefaultTrainTransform(short=600, max_size=1000, net=None, ...)`, `FasterRCNNDefaultValTransform(short=600, max_size=1000, ...)`, `MaskRCNNDefaultTrainTransform(...)`, `MaskRCNNDefaultValTransform(...)`, `transform_test`, `load_test` | Faster/Mask R-CNN train transforms use a `net` for feature/anchor target details. Validation often uses `Tuple(*[Append() for _ in range(3)])`; specialized train batchify classes infer feature shapes from the network. |
| `presets.yolo` | `YOLO3DefaultTrainTransform(width, height, net=None, mean=..., std=..., mixup=False, **kwargs)`, `YOLO3DefaultValTransform(width, height, ...)`, `transform_test(imgs, short=416, max_size=1024, stride=1, ...)`, `load_test(...)` | Training needs the YOLO network for target generation. Typical validation batchify is `Tuple(Stack(), Pad(pad_val=-1))`; training stacks target tensors and pads raw labels. |
| `presets.center_net` | `CenterNetDefaultTrainTransform(width, height, num_class, scale_factor=4, ...)`, `CenterNetDefaultValTransform(width, height, ...)`, `transform_test`, `load_test`, `get_post_transform` | Requires `num_class` and often a model scale factor; outputs heatmap/offset/wh-style targets. |
| `presets.imagenet` | `transform_eval(imgs, resize_short=256, crop_size=224, mean=..., std=...)` | Classification evaluation preprocessing. |
| `presets.segmentation` | `test_transform(img, ctx)` | Semantic segmentation test preprocessing. |
| `presets.simple_pose`, `presets.alpha_pose` | `SimplePoseDefaultTrainTransform`, `SimplePoseDefaultValTransform`, `AlphaPoseDefaultTrainTransform`, `AlphaPoseDefaultValTransform` | Pose/keypoint transform presets; require joint counts and joint-pair metadata. |

## Batchify functions: `gluoncv.data.batchify`

| API | Constructor | Use when | Output behavior |
| --- | --- | --- | --- |
| `Stack` | `Stack()` | Every sample field has the same shape/length. | Stacks arrays along a new batch dimension into an MXNet NDArray. |
| `Pad` | `Pad(axis=0, pad_val=0, num_shards=1, ret_length=False)` | Sample fields vary along one or more axes, e.g. detection labels with different object counts. | Pads to the maximum length per shard. If `ret_length=True`, also returns original lengths. |
| `Append` | `Append(expand=True, batch_axis=0)` | Samples are ragged or not directly stackable; common for R-CNN train/val outputs. | Returns a list of NDArrays; by default expands a batch axis per sample. |
| `Tuple` | `Tuple(fn, *args)` or `Tuple([fn0, fn1, ...])` | Each sample is a tuple/list with multiple fields. | Applies each batchify function to the corresponding field. Asserts the number of sample fields matches the number of functions. |
| `FasterRCNNTrainBatchify` | `FasterRCNNTrainBatchify(net, num_shards=1)` | Faster R-CNN train samples with image, bbox, RPN class targets, RPN box targets, RPN masks. | Pads images/labels and target maps using feature shapes inferred from `net.features`. |
| `MaskRCNNTrainBatchify` | `MaskRCNNTrainBatchify(net, num_shards=1)` | Mask R-CNN train samples with the Faster R-CNN fields plus masks. | Wraps Faster R-CNN batchify and pads masks along `(0, 1, 2)`. |

## Data loaders and samplers

- `DetectionDataLoader(dataset, batch_size=None, shuffle=False, sampler=None, last_batch=None, batch_sampler=None, batchify_fn=None, num_workers=0)` is a detection-friendly loader. Modern Gluon code can also use `mxnet.gluon.data.DataLoader(..., batchify_fn=...)` directly.
- `RandomTransformDataLoader(transform_fns, dataset, interval=1, ..., num_workers=0, pin_memory=False, prefetch=None)` randomly chooses transform functions across workers and periodically changes them; useful for random shape/augmentation schedules.
- `SplitSampler` and `ShuffleSplitSampler` split a dataset across parts; `SplitSortedBucketSampler` is useful when sorting/bucketing by sequence-like keys.
- Start with `num_workers=0` while debugging annotation parsing. Increase workers only after single-process loading succeeds.

## Dataset constructors: signatures to remember

```python
from gluoncv import data

data.VOCDetection(root='~/.mxnet/datasets/voc', splits=((2007, 'trainval'), (2012, 'trainval')), transform=None, index_map=None, preload_label=True)
data.COCODetection(root='~/.mxnet/datasets/coco', splits=('instances_val2017',), transform=None, min_object_area=0, skip_empty=True, use_crowd=True)
data.COCOInstance(root='~/.mxnet/datasets/coco', splits=('instances_val2017',), transform=None, min_object_area=1, skip_empty=True)
data.COCOKeyPoints(root='~/.mxnet/datasets/coco', splits=('person_keypoints_val2017',), check_centers=False, skip_empty=True)
data.ImageNet(root='~/.mxnet/datasets/imagenet', train=True, transform=None)
data.ADE20KSegmentation(root='~/.mxnet/datasets/ade', split='train', mode=None, transform=None)
data.CitySegmentation(root='~/.mxnet/datasets/citys', split='train', mode=None, transform=None)
data.UCF101(root='~/.mxnet/datasets/ucf101/rawframes', setting='~/.mxnet/datasets/ucf101/ucfTrainTestlist/ucf101_train_split_1_rawframes.txt', ...)
data.Kinetics400(root='~/.mxnet/datasets/kinetics400/rawframes_train', setting='~/.mxnet/datasets/kinetics400/kinetics400_train_list_rawframes.txt', ...)
data.HMDB51(root='~/.mxnet/datasets/hmdb51/rawframes', setting='~/.mxnet/datasets/hmdb51/testTrainMulti_7030_splits/hmdb51_train_split_1_rawframes.txt', ...)
data.SomethingSomethingV2(root='~/.mxnet/datasets/somethingsomethingv2/20bn-something-something-v2-frames', setting='~/.mxnet/datasets/somethingsomethingv2/train_videofolder.txt', name_pattern='%06d.jpg', ...)
data.LstDetection(filename, root='', flag=1, coord_normalized=True)
data.RecordFileDetection(filename, coord_normalized=True)
```

The video constructors share many arguments: `train`, `test_mode`, `name_pattern`, `video_ext`, `is_color`, `modality`, `num_segments`, `num_crop`, `new_length`, `new_step`, `new_width`, `new_height`, `target_width`, `target_height`, `temporal_jitter`, `video_loader`, `use_decord`, `slowfast`, `slow_temporal_stride`, `fast_temporal_stride`, `data_aug`, `lazy_init`, and `transform`.

## Metrics and visualization APIs

| Task | APIs | Practical use |
| --- | --- | --- |
| Detection metrics | `VOCMApMetric(iou_thresh=0.5, class_names=None)`, `VOC07MApMetric(...)`, `COCODetectionMetric(dataset, save_prefix, use_time=True, cleanup=False, score_thresh=0.05, data_shape=None, post_affine=None)` | For full evaluation loops, route command assembly to training/evaluation; for debugging, ensure prediction/result boxes use the same class ids and coordinate space as the dataset. |
| Instance/keypoint/tracking metrics | `COCOInstanceMetric`, `COCOKeyPointsMetric`, tracking metrics under `gluoncv.utils.metrics.tracking` | Require task-specific result JSON or tracking sequences; verify dataset object and optional `pycocotools` first. |
| Segmentation metrics | `SegmentationMetric(nclass)`, `batch_pix_accuracy`, `batch_intersection_union`, `pixelAccuracy`, `intersectionAndUnion` | Check `nclass` and ignored labels; predicted arrays and label arrays must have compatible spatial shape. |
| Visualization | `plot_bbox`, `cv_plot_bbox`, `plot_image`, `cv_plot_image`, `get_color_pallete`, `DeNormalize`, keypoint/mask/network viz helpers | Use after loading one sample to confirm class ids, colors, coordinate space, and channel order. Headless systems may need a non-interactive Matplotlib backend or OpenCV-only helpers. |

## Optional dependency map

- `mxnet` is required for most `gluoncv.data` datasets, transforms, batchify functions, and visualization examples.
- `pycocotools` is required for normal COCO detection/instance/keypoints/segmentation parsing and COCO metrics.
- `opencv-python` or OpenCV availability matters for image decoding/resizing, affine transforms, video frame extraction, and some visualization helpers.
- `Pillow` is used by COCO aspect-ratio probing and segmentation color palettes; legacy GluonCV stacks can require older Pillow versions in Torch submodules.
- `decord` is optional for direct video loading; frame-folder mode does not require it.
- DALI, Horovod, TVM, ONNX, CUDA, dense-flow tools, and AutoGluon are optional workflow-specific dependencies; do not treat them as required for basic data validation.
