# GeoAI training troubleshooting

Start with the bundled read-only layout checker when a training call fails before the
first epoch:

```bash
python scripts/check_training_layout.py --help
```

Then use the symptom map below. For callable details, see
[`api-reference.md`](api-reference.md).

## Missing images, labels, COCO JSON, or YOLO labels

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `Images directory not found` | Wrong `images_dir` or using a file where a directory is expected. | Use `--mode pairs`, `--mode coco`, or `--mode yolo` in the layout checker and pass the same paths to the trainer. |
| `Labels directory not found` | Semantic/instance layout needs a labels/masks directory but the task only supplied images. | Create or route for label generation upstream; do not train on image-only data unless using a classifier. |
| `COCO annotations file not found` or `not a file` | `labels_dir`/`annotations_path` points to a directory instead of JSON, or the wrong `input_format` was selected. | For COCO detector training, pass `annotations_path="...json"`. For raster mask training, use `input_format="directory"` with `labels_dir`. |
| YOLO `images/` or `labels/` missing | The root path is not the YOLO root expected by GeoAI. | Root must contain `images/` and `labels/`; label files should match image stems. |
| Same image count but mismatched labels | Basenames differ, labels are nested, or masks use a different extension. | Rename or copy labels so stems match images, or choose the parser that matches the actual format. |
| COCO images listed but files missing | `file_name` entries in JSON are relative to another image root. | Move images, rewrite `file_name`, or pass the correct image directory. |

Important format distinction:

- `input_format="coco_detection"` uses the COCO JSON as the annotation source for
  detector training.
- `input_format="coco"` in paired-mask segmentation routes can still expect label
  mask files derived from the COCO image filenames.
- GeoAI's `parse_yolo_annotations` expects matching image/label filenames under
  `images/` and `labels/`; if your YOLO data is text-box-only, validate that the
  chosen downstream training API actually consumes those text labels.

## Class counts and background labels

- Detection and instance segmentation: `num_classes` includes background. If there
  are `N` object classes, set `num_classes=N+1` and put `"background"` at index `0`
  in `class_names`.
- Semantic segmentation: `num_classes` includes every predicted mask class,
  commonly including background class `0`.
- Image classification: `num_classes` equals the number of class folders or class
  labels; no artificial background is added.
- COCO category IDs do not have to be contiguous, but GeoAI maps them to contiguous
  labels starting at `1`. Keep `class_names` sorted the same way you intend to
  interpret evaluation results.
- For binary masks stored as `0/255`, either remap masks to `0/1` before training or
  use a dataset path that correctly normalizes nonzero foreground values while
  preserving ignored pixels.

If the model learns only one foreground class in directory-style Mask R-CNN training,
check whether `multiclass=True` was required. Leaving `multiclass=False` with
multi-class raster masks can collapse all nonzero instances to class `1`.

## Ignore-index and sparse labels

| Situation | Recommended setting |
| --- | --- |
| Standard semantic masks with all pixels labeled | `ignore_index=None` or a value not present in masks. |
| Padding/crop regions should not train the model | Use a real ignored value such as `-100` or `255`, and preserve it during resizing. |
| Binary masks where `255` means ignored, not foreground | Pass `ignore_index=255` and verify normalization does not convert it to `1`. |
| Sparse landcover masks where `0` means unlabeled | Use `geoai.landcover_train.train_segmentation_landcover(..., ignore_index=0, validation_iou_mode="sparse_labels", background_class=0)`. |
| Sparse evaluation after training | Use `evaluate_sparse_iou` so predictions in unlabeled/background areas are not counted as false positives. |

Warnings:

- A wrong `ignore_index` can silently train the model to learn unlabeled pixels as a
  real class.
- `geoai.train` metric helpers return `0.0` when all target pixels are ignored; if
  this happens often, the validation split is not informative.
- Keep the same ignored value in loss construction, dataset transforms, IoU metrics,
  and visualization.

## Channel mismatch

Symptoms include first-convolution shape errors, unexpected zero-padded bands, or
poor accuracy after switching from RGB to multispectral data.

Fixes:

- Set `num_channels` / `in_channels` explicitly for every trainer and model factory.
- Verify with the layout checker:

  ```bash
  python scripts/check_training_layout.py \
    --mode pairs \
    --images-dir tiles/images \
    --labels-dir tiles/labels \
    --expected-channels 6
  ```

- For timm classifiers, `get_timm_model(..., in_channels=...)` and
  `modify_first_conv_for_channels` adapt the first convolution.
- For detector models, `get_detection_model(..., num_channels=...)` adjusts supported
  torchvision backbones; `num_channels` below `3` is not supported there.
- For multi-spectral ImageNet-pretrained encoders, consider whether RGB ImageNet
  normalization is appropriate. Regression utilities only use encoder preprocessing
  when the stats length matches channel count.

## Checkpoints, frozen encoders, and resumed runs

- `checkpoint_path` resumes a Lightning or training checkpoint. It must match the
  trainer class and architecture that created it.
- `pretrained_model_path` in detection training initializes or resumes model weights,
  not the same as a Lightning `.ckpt` file.
- If a timm segmentation checkpoint was trained with `use_timm_model=True`, load or
  push it with the same `use_timm_model` and `timm_model_name` values.
- `freeze_encoder=True` / `freeze_backbone=True` must be set when constructing the
  training model. It does not retroactively fix a checkpoint trained with all layers
  unfrozen.
- When changing `num_classes`, class-name order, or channel count, do a short run
  before resuming from a previous checkpoint; classifier/detector heads may no longer
  match.

## Lightning, SMP, timm, and TorchGeo imports

| Error family | Affected route | Action |
| --- | --- | --- |
| `No module named lightning.pytorch` | `timm_train`, `timm_segment`, `timm_regress`, `classify` | Install/use an environment with Lightning or choose a lower-level non-Lightning path. |
| `segmentation-models-pytorch is not installed` | `geoai.train.train_segmentation_model`, `timm_segment`, `timm_regress` | Install SMP or choose the Transformers `geoai.segmentation` path if appropriate. |
| `timm is required` | timm classifier/segmentation models | Install timm or choose a non-timm model path. |
| `torchgeo` import errors | `geoai.classify.train_classifier` | Use the ImageFolder `geoai.recognize.train_image_classifier` path unless TorchGeo is required. |
| `pycocotools is required for compressed RLE masks` | COCO masks with compressed RLE | Install pycocotools or convert annotations to polygons/uncompressed masks. |
| `huggingface_hub is required` | Hub push/download helpers | Install huggingface_hub only when user approves Hub operations. |

The minimum training choice should match available dependencies; do not install broad
optional stacks unless the user asked for that workflow.

## GPU OOM, CPU fallback, and long training

Safe first reductions:

- Decrease `batch_size`.
- Decrease `tile_size`, `window_size`, or `image_size`.
- Use a smaller encoder/backbone (`resnet18/34` before larger ConvNeXt/EfficientNet
  variants).
- Enable `freeze_encoder=True` or `freeze_backbone=True` for small fine-tunes.
- Reduce `num_workers` to `0` when raster/GDAL loading hangs or file locks appear.
- Start with fewer epochs and early stopping (`patience`) before committing to long
  training.
- Disable visualization and large probability outputs during training validation.

For detection, Mask R-CNN is memory heavier than bbox-only models. For segmentation,
overlap/window inference belongs to post-training validation; training tiles should be
kept modest.

## Hugging Face credentials and Hub pushes

Treat these as publish-time operations, not training prerequisites:

- `push_classifier_to_hub`
- `push_timm_model_to_hub`
- `push_detector_to_hub`

Rules:

- Confirm the user wants a remote repository to be created or updated.
- Use `private=True` unless the model and class labels are intended to be public.
- Use an existing `huggingface-cli login` or a token passed securely by the user.
- Never write tokens to generated skill files, notebooks, config files, or logs.
- If credentials are missing, finish local training/evaluation and defer publishing.

## Difficult synthetic usability cases

### RGB building segmentation with `0/255` masks

Problem: User has three-band GeoTIFF or PNG tiles and binary masks where buildings are
`255`; they want a timm/SMP model. Failure modes include treating `255` as class `255`,
setting `num_classes=1`, or picking `num_channels=4` from a copied recipe.

Safe path:

1. Validate `--expected-channels 3 --expected-classes 2`.
2. Remap masks to `0/1` if the chosen dataset path does not normalize binary masks.
3. Train with `train_timm_segmentation_model(..., num_channels=3, num_classes=2,
   monitor_metric="val_iou", mode="max")`.
4. Run a very short training pass before scaling epochs or encoder size.

### Sparse landcover masks with incomplete background

Problem: `0` means unlabeled, not true negative background, and rare classes should
not disappear during IoU model selection.

Safe path:

1. Use `train_segmentation_landcover` rather than the generic segmentation trainer.
2. Set `ignore_index=0`, `validation_iou_mode="sparse_labels"`, and
   `background_class=0`.
3. Compute class weights with a cap (`max_class_weight`) and inspect per-class counts.
4. Use `evaluate_sparse_iou` for validation reports.
