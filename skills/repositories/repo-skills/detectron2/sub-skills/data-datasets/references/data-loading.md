# Data Loading, Mappers, and Augmentation Hooks

Detectron2 loader builders consume lightweight dataset records and apply a mapper to produce batched model inputs.

## Default Pipeline

1. A registered name in `cfg.DATASETS.TRAIN` or `cfg.DATASETS.TEST` resolves through `DatasetCatalog.get(name)` to a list of dataset dicts.
2. Each dict is passed through a mapper. The default mapper is `DatasetMapper` when using config-based loader construction.
3. Mapped outputs are batched as a list by default; Detectron2 does not collate detection samples into a single tensor batch.
4. Builtin models expect each mapped element to contain keys such as `image`, `height`, `width`, and task-specific fields like `instances` or `sem_seg`.

## DatasetMapper

Verified constructor shape:

```python
from detectron2.data import DatasetMapper

mapper = DatasetMapper(
    is_train=True,
    augmentations=[],
    image_format="BGR",
    use_instance_mask=False,
    use_keypoint=False,
    instance_mask_format="polygon",
    keypoint_hflip_indices=None,
    precomputed_proposal_topk=None,
    recompute_boxes=False,
)
```

Default behavior:

- Deep-copies each dataset dict before mutation.
- Reads `file_name` with Detectron2 image utilities and checks `height` / `width` if present.
- Reads `sem_seg_file_name` into `sem_seg` when present.
- Applies configured augmentations to image and supported annotations.
- Converts image to a contiguous CHW torch tensor in `dataset_dict["image"]`.
- During training, converts `annotations` into an `Instances` object at `dataset_dict["instances"]` and removes `iscrowd` instances.
- During inference, removes `annotations` and `sem_seg_file_name` unless customized.
- Removes segmentation or keypoint annotations unless `use_instance_mask` or `use_keypoint` is enabled.

Use the explicit constructor when you are not relying on a full config. When using `cfg`, `DatasetMapper(cfg, is_train=True)` is supported through Detectron2's configurable machinery and derives augmentation, mask, keypoint, and proposal options from config fields.

## Loader Builders

Verified explicit signatures:

```python
from detectron2.data import build_detection_train_loader, build_detection_test_loader

train_loader = build_detection_train_loader(
    dataset_records,
    mapper=mapper,
    sampler=None,
    total_batch_size=2,
    aspect_ratio_grouping=True,
    num_workers=0,
)

test_loader = build_detection_test_loader(
    dataset_records,
    mapper=mapper,
    sampler=None,
    batch_size=1,
    num_workers=0,
)
```

Config-style patterns:

```python
cfg.DATASETS.TRAIN = ("my_train",)
cfg.DATASETS.TEST = ("my_val",)
train_loader = build_detection_train_loader(cfg, mapper=custom_mapper)
test_loader = build_detection_test_loader(cfg, "my_val", mapper=custom_mapper)
```

Training loader details:

- Accepts a `list`, map-style dataset, or iterable dataset.
- If `dataset` is a list, it is wrapped in `DatasetFromList`.
- If `mapper` is not `None`, records are wrapped in `MapDataset`.
- Map-style datasets default to `TrainingSampler` if no sampler is passed.
- Iterable datasets require `sampler=None`.
- `total_batch_size` must be divisible by world size.
- `aspect_ratio_grouping=True` requires mapped or original records to have `height` and `width`; it drops incomplete batches.

Test loader details:

- Defaults to `InferenceSampler` for map-style datasets.
- Defaults to `batch_size=1` and `drop_last=False`.
- Uses a trivial collator by default, returning `list[mapped_element]`.

## Custom Mapper Pattern

Use a custom mapper when records contain task-specific keys or when image/annotation transformation differs from `DatasetMapper`.

```python
import copy
import torch
from detectron2.data import detection_utils as utils
from detectron2.data import transforms as T

augmentations = T.AugmentationList([T.Resize((800, 800))])

def mapper(dataset_dict):
    dataset_dict = copy.deepcopy(dataset_dict)
    image = utils.read_image(dataset_dict["file_name"], format="BGR")
    utils.check_image_size(dataset_dict, image)

    aug_input = T.AugInput(image)
    transforms = augmentations(aug_input)
    image = aug_input.image
    image_shape = image.shape[:2]

    annotations = [
        utils.transform_instance_annotations(obj, transforms, image_shape)
        for obj in dataset_dict.pop("annotations", [])
        if obj.get("iscrowd", 0) == 0
    ]

    dataset_dict["image"] = torch.as_tensor(image.transpose(2, 0, 1).copy())
    dataset_dict["instances"] = utils.annotations_to_instances(annotations, image_shape)

    # Consume or transform any custom keys here.
    # Example: dataset_dict["depth"] = load_depth(dataset_dict.pop("depth_file_name"))
    return dataset_dict
```

Mapper checklist:

- Start with `copy.deepcopy(dataset_dict)` because mapper code mutates records.
- Read heavy data inside the mapper, not in the catalog function.
- Call `utils.check_image_size` when using `height` and `width` from annotations.
- Apply the same transform object to boxes, masks, keypoints, semantic maps, and custom geometric data.
- Return only objects the model can consume: tensors, `Instances`, `ImageList`-compatible tensors, or custom structures handled by the model.
- Keep mapper output pickle-friendly when `num_workers > 0`.

## Augmentation Hooks

Useful imports:

```python
from detectron2.data import transforms as T
```

Common patterns:

- Pass an augmentation list to `DatasetMapper(..., augmentations=[...])` for standard fields.
- Use `T.AugInput(image, boxes=boxes, sem_seg=sem_seg)` when the augmentation decision should depend on multiple fields.
- Use the returned transform to apply the same operation to extra data: `transform.apply_image`, `transform.apply_coords`, `transform.apply_polygons`, or `transform.apply_segmentation`.
- For horizontal keypoint flips, set `keypoint_names` and `keypoint_flip_map` metadata and provide `keypoint_hflip_indices` when constructing custom mapper logic.
- For new data types, register transform handlers on a `Transform` subclass or call lower-level apply methods from the mapper.

## COCO and Extra Annotation Keys

When using COCO JSON with extra per-instance fields:

```python
from detectron2.data.datasets import load_coco_json

records = load_coco_json(
    "annotations.json",
    "images",
    dataset_name="my_train",
    extra_annotation_keys=["track_id", "attributes"],
)
```

The extra keys are preserved inside each annotation dict. A custom mapper must decide whether to transform, tensorize, or drop them.

## Config Routing

This sub-skill can identify when config changes are needed, but deeper training/config work belongs outside this sub-skill. After registering new datasets, route these changes to the config/training owner:

- `cfg.DATASETS.TRAIN` and `cfg.DATASETS.TEST` names.
- `MODEL.ROI_HEADS.NUM_CLASSES` or `MODEL.RETINANET.NUM_CLASSES` for thing classes.
- `MODEL.SEM_SEG_HEAD.NUM_CLASSES` for semantic/stuff classes.
- `MODEL.ROI_KEYPOINT_HEAD.NUM_KEYPOINTS` and `TEST.KEYPOINT_OKS_SIGMAS` for keypoints.
- `DATASETS.PROPOSAL_FILES_TRAIN` / `DATASETS.PROPOSAL_FILES_TEST` for precomputed proposals.
- `DATALOADER.FILTER_EMPTY_ANNOTATIONS`, sampler choice, repeat factors, and worker counts.

## Safe Loader Smoke Tests

Before training, validate in this order:

1. Call `DatasetCatalog.get(name)` twice and confirm same length, ids, and order.
2. Inspect one record and run `scripts/validate_dataset_dicts.py` on an exported JSON fixture.
3. Check metadata with `MetadataCatalog.get(name).as_dict()`.
4. Build a loader with `num_workers=0` and a minimal mapper to get the first batch.
5. Only then increase `num_workers`, augmentations, samplers, and training complexity.
