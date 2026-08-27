# GeoAI training recipes

This reference turns prepared datasets into GeoAI training calls. It is intentionally
safe: the source examples that inspired these recipes download data, run long
training jobs, or push to remote services, so they are summarized here instead of
being used as runtime dependencies.

Use [`../scripts/check_training_layout.py`](../scripts/check_training_layout.py)
before selecting a trainer whenever file structure, band count, or label encoding is
uncertain.

## Boundary and routing

- If the user still needs STAC/NAIP/download work, vector-to-raster conversion,
  raw geospatial tiling, or batch pipeline construction, do that upstream with the
  geospatial-data-pipelines route.
- If the user only wants prediction with an existing model, use the
  detection-segmentation-inference route.
- If the user asks for foundation-model processors, embeddings, DINO/Prithvi/TESSERA
  feature workflows, or VLMs, use the foundation-models-embeddings-vlms route.
- This sub-skill assumes local training/evaluation data already exists or that the
  user has explicitly approved any additional preparation.

## Layout-to-API map

| Data layout / task | Primary GeoAI API | Key choices |
| --- | --- | --- |
| Paired images and semantic masks | `geoai.train.train_segmentation_model` or `geoai.timm_segment.train_timm_segmentation_model` | `num_channels`, `num_classes`, `ignore_index`, `architecture`, `encoder_name` |
| Small paired image/mask fine-tuning with SegFormer | `geoai.segmentation.prepare_datasets` + `geoai.segmentation.train_model` | `pretrained_model`, `target_size`, `num_classes` |
| COCO detection annotations | `geoai.object_detect.train_multiclass_detector` or `geoai.train.train_MaskRCNN_model(input_format="coco_detection")` | `num_classes` includes background; set `class_names` order |
| Directory/yolo-style instance masks | `geoai.train.train_instance_segmentation_model` or `geoai.train.train_MaskRCNN_model` | `input_format`, `instance_labels`, `multiclass`, `model_name` |
| ImageFolder-style classification | `geoai.recognize.train_image_classifier` | class subdirectories, `model_name`, `image_size`, `in_channels` |
| TorchGeo raster classification/segmentation task | `geoai.classify.train_classifier` | imagery root, label root, `model`, `backbone`, `loss`, `ignore_index` |
| Pixel-level continuous target regression | `geoai.timm_regress.create_regression_tiles` + `geoai.timm_regress.train_pixel_regressor` | paired target rasters, `loss_type`, `target_min/max`, `input_bands` |
| Sparse/incomplete landcover masks | `geoai.landcover_train.train_segmentation_landcover` | `ignore_index`, `validation_iou_mode`, class weights, focal/dice/tversky losses |
| Publish trained checkpoint | `push_classifier_to_hub`, `push_timm_model_to_hub`, `push_detector_to_hub` | confirm Hugging Face credentials and remote side effects |

## Recipe: semantic segmentation from paired tiles

Use this when `images/` and `labels/` contain matching raster/image files.

1. Validate the layout:

   ```bash
   python scripts/check_training_layout.py \
     --mode pairs \
     --images-dir tiles/images \
     --labels-dir tiles/labels \
     --expected-channels 3 \
     --expected-classes 2
   ```

2. Choose the trainer:

   - `geoai.train.train_segmentation_model` for the standard segmentation-models-
     pytorch path with explicit `ignore_index`, resize, and custom loss support.
   - `geoai.timm_segment.train_timm_segmentation_model` for timm/SMP encoder-decoder
     training with Lightning checkpointing and `monitor_metric="val_iou"`.
   - `geoai.segmentation.train_model` for a Transformers SegFormer-style fine-tune
     after `geoai.segmentation.prepare_datasets` has created train/validation
     subsets.

3. Keep critical parameters aligned:

   - `num_channels` must match the bands the model will receive.
   - `num_classes` is the count of valid output mask classes.
   - `ignore_index` should be a value that is present in masks only for pixels that
     must be excluded from loss and metrics.
   - For binary masks stored as `0/255`, remap to `0/1` or verify that the chosen
     dataset normalizer treats nonzero pixels as foreground without losing
     ignored pixels.

### Difficult binary-building case

For RGB tiles and binary building masks, start with a small timm/SMP configuration:

```python
import geoai

model = geoai.train_timm_segmentation_model(
    images_dir="tiles/images",
    labels_dir="tiles/labels",
    output_dir="runs/buildings",
    encoder_name="resnet50",
    architecture="unetplusplus",
    encoder_weights="imagenet",
    num_channels=3,
    num_classes=2,
    batch_size=4,
    num_epochs=10,
    learning_rate=1e-4,
    monitor_metric="val_iou",
    mode="max",
)
```

Scale `batch_size`, `num_epochs`, and encoder size only after a short dry run verifies
that masks, channels, and validation IoU are sane.

## Recipe: object detection and instance segmentation

Use this when the target output is boxes or per-object masks instead of one semantic
label per pixel.

- For COCO annotations, validate images and JSON first:

  ```bash
  python scripts/check_training_layout.py \
    --mode coco \
    --images-dir detection/images \
    --annotations detection/annotations.json
  ```

- For standard COCO training, call:

  ```python
  import geoai

  model_path = geoai.train_multiclass_detector(
      images_dir="detection/images",
      annotations_path="detection/annotations.json",
      output_dir="runs/detector",
      model_name="fasterrcnn_resnet50_fpn_v2",
      class_names=["background", "class_a", "class_b"],
      num_channels=3,
      batch_size=2,
      num_epochs=10,
  )
  ```

- For binary or multi-class raster masks, use `geoai.train.train_MaskRCNN_model` or
  `geoai.train.train_instance_segmentation_model` with `input_format="directory"`,
  `"coco"`, `"coco_detection"`, or `"yolo"`.
- `num_classes` includes background for detection. For ten object classes, use
  `num_classes=11` and put background at index `0` in `class_names`.
- `model_name="maskrcnn_resnet50_fpn"` produces masks; Faster R-CNN, RetinaNet, and
  FCOS are box-centric.

Post-training evaluation can use `geoai.object_detect.evaluate_multiclass_detector`
or the lower-level `geoai.train.evaluate_coco_metrics` when you already have a model
and dataloader.

## Recipe: image classification

For class-named directories:

```text
classifier_data/
  forest/
    img001.tif
  water/
    img010.png
  urban/
    img100.jpg
```

Validate and train:

```bash
python scripts/check_training_layout.py --mode imagefolder --root classifier_data
```

```python
import geoai

result = geoai.train_image_classifier(
    data_dir="classifier_data",
    model_name="resnet50",
    num_epochs=10,
    batch_size=16,
    image_size=128,
    in_channels=3,
    pretrained=True,
    freeze_backbone=True,
    output_dir="runs/classifier",
)
```

Use `result["checkpoint_path"]`, `result["class_names"]`, and
`geoai.recognize.evaluate_classifier` for evaluation. If the data is a TorchGeo
imagery/label pair rather than class folders, use `geoai.classify.train_classifier`
with `image_root`, `label_root`, `in_channels`, `num_classes`, and a TorchGeo model
configuration.

## Recipe: timm classifier from explicit datasets

If a caller already has image paths and integer labels, use
`geoai.timm_train.RemoteSensingDataset` plus `geoai.timm_train.train_timm_classifier`.
This avoids the ImageFolder scan and makes class splits explicit. Use
`freeze_backbone=True` for small labeled datasets, pass `class_weights` for imbalance,
and inspect `lightning_logs` plus `val_acc` to pick a checkpoint.

## Recipe: pixel-level regression

For continuous raster targets such as NDVI, biomass, temperature, or height:

1. Create local paired tiles from already available input and target rasters:

   ```python
   import geoai

   image_paths, target_paths = geoai.create_regression_tiles(
       input_raster="inputs/source.tif",
       target_raster="targets/target.tif",
       output_dir="regression_tiles",
       tile_size=256,
       stride=256,
       input_bands=[1, 2, 3],
       target_band=1,
       min_valid_ratio=0.8,
       target_min=-1.0,
       target_max=1.0,
   )
   ```

2. Train:

   ```python
   model = geoai.train_pixel_regressor(
       train_image_paths=image_paths,
       train_target_paths=target_paths,
       output_dir="runs/regressor",
       encoder_name="resnet50",
       architecture="unet",
       in_channels=3,
       loss_type="mse",
       num_epochs=10,
       batch_size=4,
   )
   ```

3. Use `geoai.evaluate_regression` on held-out arrays or rasters after prediction.

## Recipe: landcover training with sparse labels

Use `geoai.landcover_train` when masks are incomplete, background means
"unlabeled", or class imbalance dominates validation.

```python
import geoai

model = geoai.train_segmentation_landcover(
    images_dir="landcover/images",
    labels_dir="landcover/labels",
    output_dir="runs/landcover",
    architecture="unet",
    encoder_name="resnet34",
    num_channels=4,
    num_classes=8,
    loss_function="focal",
    ignore_index=0,
    use_class_weights=True,
    validation_iou_mode="sparse_labels",
    background_class=0,
    max_class_weight=50.0,
)
```

For sparse labels:

- Treat `background_class` as unlabeled if that matches the annotation process.
- Use `evaluate_sparse_iou` when false positives in unlabeled areas should not be
  penalized.
- Keep `ignore_index` consistent across loss, dataset normalization, and metrics.
- Use `compute_class_weights` and optional `custom_multipliers` for rare classes.

`geoai.landcover_utils.export_landcover_tiles` can export class-aware local tiles
once the raster/vector inputs already exist. If the user still needs upstream data
acquisition, clipping, or generic tiling, route that preparation away first.

## Hub publishing recipe

Only publish after the user explicitly approves remote side effects and credential
use. The available publish helpers are:

- `geoai.recognize.push_classifier_to_hub(...)` for image classifiers.
- `geoai.timm_segment.push_timm_model_to_hub(...)` for timm/SMP segmentation.
- `geoai.object_detect.push_detector_to_hub(...)` for detection checkpoints.

Credential rules:

- These helpers may create a remote repository and upload model/config files.
- They need `huggingface_hub` and either an explicit `token` argument or an existing
  Hugging Face login.
- Never hardcode API tokens in notebooks, scripts, prompts, or generated files.
- Keep `private=True` when the model, dataset, or class labels are not public.

## Reference-only source-script patterns and skip reasons

These source patterns were consulted, but the runtime skill does not link to or
execute them:

- `train_nwpu_detection`: downloads NWPU-VHR-10, prepares COCO splits, trains a
  multi-class detector, evaluates mAP, and optionally pushes to Hub. Skip reason:
  network download, long training, and optional credentials.
- `train_s2_water`: downloads Sentinel-2 water data, tiles 6-band scenes, trains
  EfficientNet-B4 + UNet++ with `num_channels=6`, evaluates IoU/Dice, and may push
  model/dataset artifacts. Skip reason: network, tiling-scale writes, training, and
  optional credentials.
- `train_whu_building`: converts WHU PNG imagery/masks to GeoTIFF, remaps `255` to
  foreground `1`, trains RGB binary segmentation, and evaluates test IoU. Skip
  reason: dataset acquisition/prep and long training.
- `preprocess_dales_ptv3`: converts DALES LAS tiles to Pointcept-style `.npy`
  blocks with centered coordinates, return-number strength, class weights, and
  `ignore_index=0`. Skip reason: large point-cloud dataset and heavy conversion.
- `train_ptv3_dales`: trains/evaluates Point Transformer V3 with Pointcept CUDA
  extensions, AMP, DDP, and Hugging Face checkpoint fine-tuning. Skip reason:
  external Pointcept backend, CUDA extension requirements, and long GPU training.
