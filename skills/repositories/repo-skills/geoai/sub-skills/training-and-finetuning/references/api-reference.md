# GeoAI training API reference

This reference covers the GeoAI `geoai-py` training/fine-tuning surface verified for
the generated skill. Prefer module imports when clarity matters, even though many
callables are also available through `import geoai`.

## Shared parameter conventions

- `num_channels` must match the image bands that will be read into the model. RGB
  data is `3`; RGBN is `4`; Sentinel-2 recipe data used `6`.
- For detection and instance segmentation, `num_classes` includes background at
  index `0`. Ten object classes therefore require `num_classes=11`.
- For semantic segmentation, `num_classes` is the number of mask class IDs the
  model predicts; background is usually class `0` and is included in that count.
- For image classification, `num_classes` is the number of class folders/classes and
  does not include an artificial background.
- `ignore_index` must be consistent across dataset normalization, loss functions,
  and metrics. Common values are `-100`, `0`, or `255`, depending on data encoding.
- `class_weights` length should equal `num_classes`. In landcover workflows,
  `compute_class_weights` can set the ignored class to weight `0`.
- `checkpoint_path` resumes a trainer checkpoint; `pretrained_model_path` initializes
  model weights for some detection APIs. Do not swap them.
- Top-level `geoai` exports are lazy. If an attribute fails to resolve, import the
  specific module directly and install the module's optional extra if needed.
- Hub push helpers are credentialed external side effects and are listed separately
  below.

## Optional dependency map

| Capability | Key modules | Common optional imports |
| --- | --- | --- |
| SegFormer training | `geoai.segmentation` | `transformers`, `albumentations`, `torch` |
| SMP/timm semantic segmentation | `geoai.train`, `geoai.timm_segment` | `segmentation_models_pytorch`, `timm`, `lightning.pytorch` |
| Image classification | `geoai.timm_train`, `geoai.recognize` | `timm`, `lightning.pytorch`, `scikit-learn`, `Pillow`, `rasterio` |
| TorchGeo classification | `geoai.classify` | `torchgeo`, `lightning.pytorch`, `albumentations` |
| Object detection | `geoai.train`, `geoai.object_detect` | `torch`, `torchvision`, `pycocotools` for some COCO masks |
| Pixel regression | `geoai.timm_regress` | `segmentation_models_pytorch`, `timm`, `lightning.pytorch`, `rasterio` |
| Hub publishing | `geoai.recognize`, `geoai.timm_segment`, `geoai.object_detect` | `huggingface_hub` |

## `geoai.segmentation`: SegFormer-style paired masks

Use this module for a compact Transformers/SegFormer training route when data is
already in paired image/mask folders.

- `CustomDataset(images_dir, masks_dir, transform=None, target_size=(256, 256), num_classes=2)`
  loads images as RGB and masks as single-channel labels. Binary masks map nonzero
  values to foreground; multi-class masks are clipped to `[0, num_classes - 1]`.
- `get_transform() -> albumentations.Compose` returns the default resize/flip/
  normalize/to-tensor transform.
- `prepare_datasets(images_dir, masks_dir, transform, test_size=0.2, random_state=42, num_classes=2) -> (train_dataset, val_dataset)`
  creates train/validation subsets.
- `train_model(train_dataset, val_dataset, pretrained_model="nvidia/segformer-b0-finetuned-ade-512-512", model_save_path="./model", output_dir="./results", num_epochs=10, batch_size=8, learning_rate=5e-5, num_classes=2) -> str`
  fine-tunes a SegFormer model and returns the saved model path.

`segment_image` and visualization helpers are post-training/inference utilities; route
pure prediction requests to the inference sub-skill.

## `geoai.train`: core segmentation, detection, and metrics

### Layout and dataset helpers

- `_validate_training_paths(images_dir, labels_dir, output_dir, input_format="directory")`
  checks required paths for `directory`, `coco`, `coco_detection`, and `yolo` formats
  and creates `output_dir` if valid.
- `_check_readable(path, max_retries=3, retry_delay=1.0)` verifies path readability,
  with Windows lock retries.
- `parse_coco_annotations(coco_json_path, images_dir, labels_dir) -> (image_paths, label_paths)`
  pairs COCO image entries with same-named raster/image labels.
- `parse_yolo_annotations(data_dir, images_subdir="images", labels_subdir="labels") -> (image_paths, label_paths)`
  expects `data_dir/images/` and `data_dir/labels/` and same-named label files.
- `get_transform(train: bool) -> torchvision.transforms.transforms.Compose` returns
  detection transforms.
- `get_semantic_transform(train: bool) -> Any` returns semantic segmentation
  transforms with optional training augmentations.
- `collate_fn(batch: List[Tuple[torch.Tensor, Dict[str, torch.Tensor]]]) -> Tuple[Tuple[torch.Tensor, ...], Tuple[Dict[str, torch.Tensor], ...]]`
  is the detection dataloader collate function.
- `SemanticSegmentationDataset(image_paths, label_paths, transforms=None, num_channels=None, target_size=None, resize_mode="resize", num_classes=2, ignore_index=-100)`
  loads GeoTIFF or standard-image masks, preserves `ignore_index`, and supports
  `resize`/`pad` target sizing.
- `ObjectDetectionDataset(image_paths, label_paths, transforms=None, num_channels=None, instance_labels=False, multiclass=False)`
  turns raster labels into masks/boxes for torchvision detection. Use `multiclass=True`
  only when mask pixel values are class IDs; use `instance_labels=True` only when
  values are pre-assigned instance IDs.
- `COCODetectionDataset(coco_json_path, images_dir, image_ids=None, category_mapping=None, transforms=None, num_channels=None, min_area=10, compute_masks=True)`
  reads COCO boxes/masks and maps category IDs to contiguous class labels starting
  at `1`.

### Model factories and device helpers

- `get_device() -> torch.device` selects CUDA when available, otherwise CPU.
- `get_smp_model(architecture="unet", encoder_name="resnet34", encoder_weights="imagenet", in_channels=3, classes=2, activation=None, **kwargs)`
  builds a segmentation-models-pytorch model.
- `get_detection_model(model_name="fasterrcnn_resnet50_fpn_v2", num_classes=2, num_channels=3, pretrained=True)`
  supports `fasterrcnn_resnet50_fpn_v2`, `fasterrcnn_mobilenet_v3_large_fpn`,
  `retinanet_resnet50_fpn_v2`, `fcos_resnet50_fpn`, and `maskrcnn_resnet50_fpn`.
- `get_instance_segmentation_model(num_classes=2, num_channels=3, pretrained=True)`
  builds a Mask R-CNN instance-segmentation model.
- `model_has_masks(model_name) -> bool` returns true for `maskrcnn_resnet50_fpn`.

### Training APIs

- `train_segmentation_model(images_dir, labels_dir, output_dir, input_format="directory", architecture="unet", encoder_name="resnet34", encoder_weights="imagenet", num_channels=3, num_classes=2, batch_size=8, num_epochs=50, learning_rate=0.001, weight_decay=1e-4, seed=42, val_split=0.2, print_freq=10, verbose=True, save_best_only=True, plot_curves=False, device=None, checkpoint_path=None, resume_training=False, target_size=None, resize_mode="resize", num_workers=None, early_stopping_patience=None, train_transforms=None, val_transforms=None, loss_fn=None, class_weights=None, ignore_index=-100, freeze_encoder=False, **kwargs) -> torch.nn.Module`
  trains semantic segmentation with SMP, metrics, checkpointing, optional custom loss,
  and `ignore_index` support.
- `train_MaskRCNN_model(images_dir, labels_dir, output_dir, input_format="directory", num_channels=3, num_classes=2, model=None, pretrained=True, pretrained_model_path=None, batch_size=4, num_epochs=10, learning_rate=0.005, seed=42, val_split=0.2, visualize=False, resume_training=False, print_freq=10, device=None, num_workers=None, verbose=True, model_name="maskrcnn_resnet50_fpn", instance_labels=False, multiclass=False) -> torch.nn.Module`
  trains a torchvision detection/Mask R-CNN-style model from directory, COCO, COCO
  detection, or YOLO-style data.
- `train_instance_segmentation_model(images_dir, labels_dir, output_dir, input_format="directory", num_classes=2, num_channels=3, batch_size=4, num_epochs=10, learning_rate=0.005, seed=42, val_split=0.2, visualize=False, device=None, num_workers=None, verbose=True, instance_labels=False, multiclass=False, **kwargs) -> torch.nn.Module`
  is a clearer wrapper around Mask R-CNN training.
- `train_one_epoch(model, optimizer, data_loader, device, epoch, print_freq=10, verbose=True) -> float`
  and `train_semantic_one_epoch(...) -> float` are lower-level loop helpers.

### Evaluation and metrics

- `evaluate(model, data_loader, device, use_mask_iou=True) -> dict[str, float]` for
  detection-style validation.
- `evaluate_coco_metrics(model, data_loader, device, class_names=None, iou_thresholds=None, verbose=True) -> dict[str, float]`
  returns COCO-style AP/mAP metrics such as `mAP@0.5`, `mAP@0.75`, and
  `mAP@[0.5:0.95]`.
- `evaluate_semantic(model, data_loader, device, criterion, num_classes=2, ignore_index=None) -> dict[str, float]`
  returns `loss`, `IoU`, `F1`, `Precision`, and `Recall`.
- `f1_score(pred, target, smooth=1e-6, num_classes=None, ignore_index=None) -> float`
- `iou_coefficient(pred, target, smooth=1e-6, num_classes=None, ignore_index=None) -> float`
- `precision_score(pred, target, smooth=1e-6, num_classes=None, ignore_index=None) -> float`
- `recall_score(pred, target, smooth=1e-6, num_classes=None, ignore_index=None) -> float`

The metric helpers accept `[H, W]` class maps or `[C, H, W]` logits/probabilities and
return `0.0` when all target pixels are ignored.

## `geoai.timm_train`: timm image classifiers

- `get_timm_model(model_name="resnet50", num_classes=10, in_channels=3, pretrained=True, features_only=False, **kwargs) -> torch.nn.Module`
  wraps `timm.create_model` and supports custom input channels.
- `modify_first_conv_for_channels(model, in_channels, pretrained_channels=3) -> torch.nn.Module`
  adapts the first convolution by copying RGB weights and mean-initializing extra
  channels.
- `RemoteSensingDataset(image_paths, labels, transform=None, num_channels=None)` loads
  raster image paths with integer labels.
- `TimmClassifier(model_name="resnet50", num_classes=10, in_channels=3, pretrained=True, learning_rate=0.001, weight_decay=0.0001, freeze_backbone=False, loss_fn=None, class_weights=None, **model_kwargs)`
  is the Lightning module with `train_acc`, `val_acc`, and `test_acc` logging.
- `train_timm_classifier(train_dataset, val_dataset=None, test_dataset=None, model_name="resnet50", num_classes=10, in_channels=3, pretrained=True, output_dir="output", batch_size=32, num_epochs=50, learning_rate=0.001, weight_decay=0.0001, num_workers=4, freeze_backbone=False, class_weights=None, accelerator="auto", devices="auto", monitor_metric="val_loss", mode="min", patience=10, save_top_k=1, checkpoint_path=None, **kwargs) -> TimmClassifier`
  trains from explicit PyTorch datasets.
- `list_timm_models(filter="", pretrained=False, limit=None) -> list[str]` helps choose
  an available timm model.

## `geoai.timm_segment`: timm/SMP semantic segmentation

- `SegmentationDataset(image_paths, mask_paths, transform=None, num_channels=None)`
  loads paired raster images and masks.
- `TimmSegmentationModel(encoder_name="resnet50", architecture="unet", num_classes=2, in_channels=3, encoder_weights="imagenet", learning_rate=0.001, weight_decay=0.0001, freeze_encoder=False, loss_fn=None, class_weights=None, use_timm_model=False, timm_model_name=None, **decoder_kwargs)`
  uses an SMP decoder with a timm encoder, or a full timm/HF segmentation model when
  `use_timm_model=True`.
- `train_timm_segmentation(train_dataset, val_dataset=None, test_dataset=None, encoder_name="resnet50", architecture="unet", num_classes=2, in_channels=3, encoder_weights="imagenet", output_dir="output", batch_size=8, num_epochs=50, learning_rate=0.001, weight_decay=0.0001, num_workers=4, freeze_encoder=False, class_weights=None, loss_fn=None, accelerator="auto", devices="auto", monitor_metric="val_loss", mode="min", patience=10, save_top_k=1, checkpoint_path=None, use_timm_model=False, timm_model_name=None, **kwargs) -> TimmSegmentationModel`
  trains from explicit datasets.
- `train_timm_segmentation_model(images_dir, labels_dir, output_dir, input_format="directory", encoder_name="resnet50", architecture="unet", encoder_weights="imagenet", num_channels=3, num_classes=2, batch_size=8, num_epochs=50, learning_rate=0.001, weight_decay=0.0001, val_split=0.2, seed=42, num_workers=4, freeze_encoder=False, class_weights=None, loss_fn=None, monitor_metric="val_iou", mode="max", patience=10, save_top_k=1, verbose=True, device=None, use_timm_model=False, timm_model_name=None, train_transforms=None, val_transforms=None, **kwargs) -> torch.nn.Module`
  builds datasets from `directory`, `coco`, or `yolo` layout and returns the underlying
  model.
- `push_timm_model_to_hub(model_path, repo_id, encoder_name="resnet50", architecture="unet", num_channels=3, num_classes=2, use_timm_model=False, timm_model_name=None, commit_message=None, private=False, token=None, **kwargs) -> str | None`
  publishes segmentation checkpoint/config artifacts to Hugging Face Hub.

`timm_semantic_segmentation` and `predict_segmentation` are inference/post-training
helpers; use them only for validation context, not inference-only tasks.

## `geoai.timm_regress`: pixel-level regression

- `create_regression_tiles(input_raster, target_raster, output_dir, tile_size=256, stride=None, input_bands=None, target_band=1, min_valid_ratio=0.8, target_min=None, target_max=None) -> (image_paths, target_paths)`
  creates paired image/target tiles from local rasters.
- `PixelRegressionDataset(image_paths, target_paths, input_bands=None, target_band=1, transform=None, normalize_input=True, image_mean=None, image_std=None, target_nodata=None)`
  loads paired raster tiles and handles NoData/NaN target values.
- `PixelRegressionModel(encoder_name="resnet50", architecture="unet", in_channels=3, encoder_weights="imagenet", learning_rate=0.0001, weight_decay=0.0001, freeze_encoder=False, loss_fn=None, loss_type="mse", **decoder_kwargs)`
  logs MSE, RMSE, MAE, and R².
- `train_pixel_regressor(train_image_paths, train_target_paths, val_image_paths=None, val_target_paths=None, encoder_name="resnet50", architecture="unet", in_channels=3, encoder_weights="imagenet", output_dir="output", batch_size=8, num_epochs=50, learning_rate=0.0001, weight_decay=0.0001, num_workers=0, freeze_encoder=False, loss_type="mse", normalize_input=True, accelerator="auto", devices=1, monitor_metric="val_loss", mode="min", patience=10, save_top_k=1, checkpoint_path=None, input_bands=None, verbose=True, **kwargs) -> PixelRegressionModel`
- `train_timm_regressor(...) -> PixelRegressionModel` mirrors `train_pixel_regressor`.
- `evaluate_regression(y_true, y_pred, mask=None, print_results=True) -> dict[str, float]`
  returns `mse`, `rmse`, `mae`, and `r2`.
- Plot helpers include `plot_regression_results`, `plot_regression_comparison`,
  `plot_scatter`, `plot_training_history`, and `visualize_prediction`.

## `geoai.classify` and `geoai.recognize`: classification workflows

### `geoai.classify`

- `train_classifier(image_root, label_root, output_dir="output", in_channels=4, num_classes=14, epochs=20, img_size=256, batch_size=8, sample_size=500, model="unet", backbone="resnet50", weights=True, num_filters=3, loss="ce", class_weights=None, ignore_index=None, lr=0.001, patience=10, freeze_backbone=False, freeze_decoder=False, transforms=None, use_augmentation=False, seed=42, train_val_test_split=(0.6, 0.2, 0.2), accelerator="auto", devices="auto", logger=None, callbacks=None, log_every_n_steps=10, use_distributed_sampler=False, monitor_metric="val_loss", mode="min", save_top_k=1, save_last=True, checkpoint_filename="best_model", checkpoint_path=None, every_n_epochs=1, **kwargs) -> SemanticSegmentationTask`
  uses TorchGeo datasets/samplers and a Lightning `SemanticSegmentationTask`.

### `geoai.recognize`

- `ImageDataset(image_paths, labels, transform=None, image_size=64, in_channels=None)`
  supports JPEG/PNG/BMP and GeoTIFF inputs.
- `load_image_dataset(data_dir, extensions=None) -> dict` scans class-named
  subdirectories and returns `image_paths`, `labels`, `class_names`, and
  `class_to_idx`.
- `train_image_classifier(data_dir, model_name="resnet50", num_epochs=20, batch_size=32, learning_rate=0.001, weight_decay=0.0001, image_size=64, in_channels=3, test_size=0.2, val_size=0.2, pretrained=True, freeze_backbone=False, output_dir="output", num_workers=4, seed=42, accelerator="auto", devices="auto", patience=10, extensions=None, **kwargs) -> dict`
  returns a dict with model, trainer, datasets, class names, and best checkpoint path.
- `evaluate_classifier(model, dataset, class_names, batch_size=32, num_workers=4, device=None) -> dict`
  returns accuracy, classification report, confusion matrix, and per-class accuracy.
- `plot_confusion_matrix`, `plot_predictions`, and `plot_training_history` visualize
  classifier results and Lightning logs.
- `push_classifier_to_hub(model_path, repo_id, model_name="resnet50", num_classes=10, in_channels=3, class_names=None, commit_message=None, private=False, token=None) -> str | None`
  publishes classifier weights/config to Hugging Face Hub.

`predict_images` and `predict_images_from_hub` are post-training/inference helpers;
route pure inference tasks elsewhere.

## `geoai.landcover_train`: losses, sparse IoU, and landcover training

### Loss classes and factory

- `LandcoverCrossEntropyLoss(weight=None, ignore_index=False, reduction="mean")`
- `FocalLoss(alpha=1.0, gamma=2.0, ignore_index=-100, reduction="mean", weight=None)`
- `DiceLoss(smooth=1.0, ignore_index=-100, reduction="mean", weight=None)`
- `TverskyLoss(alpha=0.5, beta=0.5, smooth=1.0, ignore_index=-100, reduction="mean", weight=None)`
- `UnifiedFocalLoss(lambda_=0.5, gamma=0.75, delta=0.6, smooth=1.0, ignore_index=-100, weight=None, region_weight=None, use_log_cosh=False)`
- `get_landcover_loss_function(loss_name="crossentropy", num_classes=2, ignore_index=-100, class_weights=None, use_class_weights=False, focal_alpha=1.0, focal_gamma=2.0, device=None, smooth=1.0, tversky_alpha=0.5, tversky_beta=0.5, ufl_lambda=0.5, ufl_gamma=0.75, ufl_delta=0.6, region_weights=None, use_log_cosh=False) -> torch.nn.Module`

### Metrics and weights

- `landcover_iou(pred, target, num_classes, ignore_index=False, smooth=1e-6, mode="mean", boundary_weight_map=None, background_class=None) -> float | tuple`
  modes: `mean`, `perclass_frequency`, `boundary_weighted`, and `sparse_labels`.
- `compute_class_weights(labels_dir, num_classes, ignore_index=-100, custom_multipliers=None, max_weight=50.0, use_inverse_frequency=True) -> torch.Tensor`
- `evaluate_sparse_iou(model, images_dir, labels_dir, num_classes, num_channels=3, batch_size=8, background_class=0, ignore_index=False, device=None, verbose=True) -> dict`

### Training

- `train_segmentation_landcover(images_dir, labels_dir, output_dir, input_format="directory", architecture="unet", encoder_name="resnet34", encoder_weights="imagenet", num_channels=3, num_classes=2, batch_size=8, num_epochs=50, learning_rate=0.001, weight_decay=0.0001, seed=42, val_split=0.2, print_freq=10, verbose=True, save_best_only=True, plot_curves=False, device=None, checkpoint_path=None, resume_training=False, target_size=None, resize_mode="resize", num_workers=None, loss_function="crossentropy", ignore_index=0, use_class_weights=False, focal_alpha=1.0, focal_gamma=2.0, smooth=1.0, tversky_alpha=0.5, tversky_beta=0.5, ufl_lambda=0.5, ufl_gamma=0.75, ufl_delta=0.6, region_weights=None, use_log_cosh=False, custom_multipliers=None, max_class_weight=50.0, use_inverse_frequency=True, validation_iou_mode="standard", boundary_alpha=1.0, background_class=0, training_callback=None, **kwargs) -> torch.nn.Module`

Use `validation_iou_mode="sparse_labels"` when background represents unlabeled pixels
rather than true negative evidence.

## `geoai.landcover_utils`: landcover-specific local preparation

- `export_landcover_tiles(in_raster, out_folder, in_class_data=None, tile_size=256, stride=128, class_value_field="class", buffer_radius=0, max_tiles=None, quiet=False, all_touched=True, create_overview=False, skip_empty_tiles=False, min_feature_ratio=False, metadata_format="PASCAL_VOC") -> dict`
  creates local image/label tiles and returns export counts/skip reasons. Use it only
  after upstream acquisition/clipping is complete.
- `normalize_radiometric(subject_image, reference_image, output_path=None, method="lirrn", p_n=500, num_quantisation_classes=3, num_sampling_rounds=3, subsample_ratio=0.1, random_state=None) -> (normalized_image, metrics)`
  normalizes multi-temporal image radiometry for more stable training data.

## `geoai.object_detect`: detector preparation, evaluation, and publishing

- `prepare_nwpu_vhr10(data_dir, output_dir=None, val_split=0.2, seed=42) -> dict`
  converts NWPU-style text boxes to COCO JSON and train/validation splits. Treat as a
  dataset-specific preparation pattern, not a generic downloader.
- `train_multiclass_detector(images_dir, annotations_path, output_dir, model_name="fasterrcnn_resnet50_fpn_v2", class_names=None, num_channels=3, batch_size=4, num_epochs=50, learning_rate=0.005, val_split=0.2, seed=42, pretrained=True, pretrained_model_path=None, device=None, num_workers=None, verbose=True) -> str`
  trains a COCO-format detector and returns `best_model.pth`.
- `evaluate_multiclass_detector(model_path=None, model_name=None, images_dir="", annotations_path="", num_classes=11, class_names=None, num_channels=3, batch_size=4, device=None, num_workers=None, repo_id=None, verbose=True) -> dict[str, float]`
  computes COCO-style mAP metrics.
- `visualize_coco_annotations(annotations_path, images_dir, num_samples=4, random=False, seed=None, figsize=(14, 14), cols=2, output_path=None)`
  can inspect annotation alignment before training; keep outputs local.
- `plot_detection_training_history(history_path, figsize=(15, 4), output_path=None)`
  visualizes saved detection training history.
- `push_detector_to_hub(model_path, repo_id, model_name="fasterrcnn_resnet50_fpn_v2", num_classes=11, num_channels=3, class_names=None, commit_message=None, private=False, token=None) -> str | None`
  publishes detection model weights/config to Hugging Face Hub.

Detector inference helpers such as `multiclass_detection`, `batch_multiclass_detection`,
and `predict_detector_from_hub` belong to inference workflows unless they are being used
only for post-training evaluation context.
