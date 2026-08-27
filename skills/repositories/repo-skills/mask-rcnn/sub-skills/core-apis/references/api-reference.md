# Core API Reference

## Verified package facts

- Distribution: `mask-rcnn`.
- Import package: `mrcnn`.
- Main modules: `mrcnn.config`, `mrcnn.utils`, `mrcnn.model`, `mrcnn.visualize`, `mrcnn.parallel_model`.
- Main model class: `mrcnn.model.MaskRCNN`.
- Base configuration class: `mrcnn.config.Config`.
- Base dataset class: `mrcnn.utils.Dataset`.

## Key signatures

These signatures were verified from an installed package environment.

| Object | Signature | Use |
| --- | --- | --- |
| `Config.__init__` | `(self)` | Computes derived attributes such as `BATCH_SIZE`, `IMAGE_SHAPE`, and `IMAGE_META_SIZE`. |
| `Config.display` | `(self)` | Prints non-callable config attributes. Useful before training/inference logs. |
| `Dataset.__init__` | `(self, class_map=None)` | Initializes image/class registries. |
| `Dataset.add_class` | `(self, source, class_id, class_name)` | Registers class ids for a dataset source. `source` cannot contain `.`. |
| `Dataset.add_image` | `(self, source, image_id, path, **kwargs)` | Registers image metadata; kwargs carry polygons, annotations, dimensions, or synthetic specs. |
| `Dataset.prepare` | `(self, class_map=None)` | Builds class/image id mappings and must run before training/inference data use. |
| `Dataset.load_image` | `(self, image_id)` | Returns an RGB `[H, W, 3]` NumPy array. Subclasses may override for generated data. |
| `Dataset.load_mask` | `(self, image_id)` | Returns `(mask, class_ids)` where mask is `[H, W, instance_count]`. |
| `MaskRCNN.__init__` | `(self, mode, config, model_dir)` | Builds a training or inference Keras model. `mode` is `"training"` or `"inference"`. |
| `MaskRCNN.train` | `(self, train_dataset, val_dataset, learning_rate, epochs, layers, augmentation=None, custom_callbacks=None, no_augmentation_sources=None)` | Trains with a dataset pair and layer selection. |
| `MaskRCNN.detect` | `(self, images, verbose=0)` | Runs inference on a list whose length equals `config.BATCH_SIZE`. |
| `visualize.display_instances` | `(image, boxes, masks, class_ids, class_names, scores=None, title='', figsize=(16, 16), ax=None, show_mask=True, show_bbox=True, colors=None, captions=None)` | Draws detections or ground truth masks/boxes. |

## `Config` relationship notes

Subclass `Config` instead of mutating an instance after construction whenever possible. Important attributes:

- `NAME`: experiment/model name used in logs and checkpoint discovery.
- `GPU_COUNT` and `IMAGES_PER_GPU`: product becomes `BATCH_SIZE` at construction.
- `NUM_CLASSES`: background plus foreground classes. This controls classifier/mask heads and weight compatibility.
- `IMAGE_RESIZE_MODE`: common values are `square`, `pad64`, `crop`, and `none`.
- `IMAGE_MIN_DIM`, `IMAGE_MAX_DIM`, `IMAGE_MIN_SCALE`: image resize constraints.
- `BACKBONE`: `resnet50`, `resnet101`, or a callable with matching shape support.
- `TRAIN_BN`: defaults false because small batches make batch norm unstable.
- `RPN_ANCHOR_SCALES`, `RPN_ANCHOR_RATIOS`, `RPN_NMS_THRESHOLD`: anchor/proposal behavior.

`Config.__init__` computes `BATCH_SIZE`, `IMAGE_SHAPE`, and `IMAGE_META_SIZE`. If you change class attributes dynamically after construction, recompute or rebuild the config object.

## `MaskRCNN` lifecycle

1. Build mode-specific model:

   ```python
   model = modellib.MaskRCNN(mode="training", config=config, model_dir="logs")
   # or
   model = modellib.MaskRCNN(mode="inference", config=config, model_dir="logs")
   ```

2. Load weights with the method appropriate to the source:

   ```python
   model.load_weights("weights.h5", by_name=True)
   ```

3. Train or detect. The mode assertion will fail if you call `train()` on an inference model or `detect()` on a training model.

4. Use `model.find_last()` to locate the latest checkpoint in the configured model directory when resuming.

## Utility families

- Bounding boxes: `extract_bboxes`, `compute_iou`, `compute_overlaps`, `apply_box_deltas`, `box_refinement`, `norm_boxes`, `denorm_boxes`.
- Masks: `resize_mask`, `minimize_mask`, `expand_mask`, `unmold_mask`, `compute_overlaps_masks`.
- Anchors: `generate_anchors`, `generate_pyramid_anchors`.
- Metrics: `compute_matches`, `compute_ap`, `compute_ap_range`, `compute_recall`.
- Graph helpers: `batch_slice`, graph bbox normalization/denormalization, metadata composition/parsing in `mrcnn.model`.

Use utilities directly for small data-preparation, evaluation, and debugging tasks. Keep training/inference model calls in their owning sub-skills.
