# Dataset Conversion

MMSegmentation includes many source-level dataset converters, but this sub-skill intentionally does not bundle those converters. They are dataset-specific, often mutate or extract large raw archives, and may require optional packages or external downloads. Treat this page as a conversion planning guide, then create a project-local converter or run a native converter only when the current checkout explicitly contains one and the user approves the data mutation.

## Safe Conversion Workflow

1. Identify the target dataset class and expected config fields: `dataset_type`, `data_root`, `data_prefix`, `img_suffix`, `seg_map_suffix`, `ann_file`, `reduce_zero_label`, and `metainfo`.
2. Inspect the raw dataset license, split definition, label encoding, and whether masks are already class-id PNGs.
3. Convert raw images and masks into a stable MMSegmentation-style layout such as `img_dir/{train,val}` and `ann_dir/{train,val}` or the dataset-specific built-in layout.
4. Ensure mask pixels are class ids, not RGB colors, unless the dataset class explicitly expects otherwise.
5. Run `scripts/check_dataset_layout.py` against each split before editing the training config.
6. Inspect the expanded config with `scripts/inspect_mmseg_config.py --show-keys train_dataloader.dataset val_dataloader.dataset train_pipeline test_pipeline`.
7. Keep raw archives, temporary extraction folders, and generated conversion reports outside the runtime skill directory.

## Converter Pattern Catalog

The repository evidence shows converter patterns for these dataset families:

- Cityscapes: converts polygon JSON labels into `labelTrainIds` PNG masks; requires `cityscapesscripts`.
- Pascal VOC augmentation: converts SBD/VOC augmented annotations into VOC-compatible segmentation masks and split files.
- Pascal Context: converts annotation JSON/detail data into `SegmentationClassContext`; requires the `detail` package and PIL.
- COCO-Stuff 10k/164k: converts COCO-Stuff label encodings into segmentation masks; may require SciPy, NumPy, and PIL.
- CHASE_DB1, DRIVE, HRF, STARE, REFUGE: extract ophthalmology archives into `images/{training,validation}` and `annotations/{training,validation}` style directories.
- LoveDA, iSAID, Potsdam, Vaihingen: reorganize remote-sensing imagery and annotations, sometimes slicing large images into patches.
- Synapse and NYU: reorganize medical/depth datasets into image and annotation folders; check depth-vs-segmentation fields carefully.
- LEVIR-CD: prepares change-detection pairs with `img_path`, `img_path2`, and `seg_map_path`; this is adjacent to but not identical to ordinary semantic segmentation.

Because these converters are not bundled here, do not write runtime instructions that require a path to the original source converter. If a future task needs a converter, adapt the pattern into a local script for that task and document its inputs, outputs, optional dependencies, and destructive writes.

## Optional Dependency Signals

Common converter failures come from missing optional packages:

- `cityscapesscripts` for Cityscapes polygon conversion.
- `scipy` for MATLAB annotation files.
- `detail` for Pascal Context annotation parsing.
- `PIL`/Pillow for mask writing and palette handling.
- `cv2`/OpenCV for some image decoding and writing paths.
- geospatial packages such as GDAL for specialized remote-sensing formats.

If the dependency is only needed for conversion, avoid adding it to a training environment unless conversion is part of the requested work.

## Output Layout Checklist

For every converted split, verify:

- Image files match `img_suffix` exactly, including dataset-specific suffixes such as `_leftImg8bit.png`.
- Mask files match `seg_map_suffix` exactly, including full suffixes such as `_gtFine_labelTrainIds.png`.
- Relative subdirectories are mirrored when discovery is recursive.
- `ann_file` lines omit suffixes if the dataset appends suffixes.
- Test splits without masks remove `LoadAnnotations` and use an inference or format-only evaluation path.
- Class ids in masks match `classes`, `num_classes`, `ignore_index`, and `reduce_zero_label` choices.

## Post-Conversion Smoke Checks

Use layout checks first:

```shell
python sub-skills/data-configuration/scripts/check_dataset_layout.py \
  --data-root data/converted_dataset \
  --img-path img_dir/train \
  --seg-map-path ann_dir/train \
  --img-suffix .jpg \
  --seg-map-suffix .png \
  --sample-size 10
```

Then inspect config fields:

```shell
python sub-skills/data-configuration/scripts/inspect_mmseg_config.py \
  --config PATH/TO/CUSTOM_DATASET_CONFIG.py \
  --show-keys train_dataloader.dataset val_dataloader.dataset train_pipeline test_pipeline
```

Only after those checks should the training/evaluation sub-skill run native training, validation, browsing, or visualization commands.
