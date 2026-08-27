# Conversion and validation

Use this page when source data is not already in nnU-Net v2 format or when a dataset should be checked before planning/preprocessing.

## Convert Medical Segmentation Decathlon data

Use the installed CLI wrapper:

```bash
nnUNetv2_convert_MSD_dataset -i /path/to/Task05_Prostate -overwrite_id 205 -np 8
```

Important behavior:

- Source must be a downloaded/extracted MSD-style task folder with `imagesTr`, `imagesTs`, `labelsTr`, and `dataset.json`.
- The tool infers the source task ID from a folder like `Task05_Prostate`.
- Without `-overwrite_id`, the target ID comes from the source task ID.
- The target is written to `$nnUNet_raw/DatasetXXX_Name`.
- 4D NIfTI images are split into separate channel files named `_0000.nii.gz`, `_0001.nii.gz`, and so on.
- Segmentations are copied to `labelsTr`.
- `dataset.json` is converted from MSD/v1-style `modality` and int-to-name `labels` into v2-style `channel_names` and name-to-int `labels`.
- Target ID conflicts are rejected if candidate datasets already exist in nnU-Net storage locations.

Use a new dataset ID unless you intentionally control all raw, preprocessed, and results folders for the reused ID.

## Convert old nnU-Net v1 tasks

Use the installed CLI wrapper:

```bash
nnUNetv2_convert_old_nnUNet_dataset /path/to/Task027_ACDC Dataset027_ACDC
```

Important behavior:

- The first argument is the old task folder path containing `imagesTr`, `labelsTr`, and `dataset.json`.
- The second argument is the new dataset name, not a path, and must follow `DatasetXXX_Name`.
- The target folder is created below `$nnUNet_raw`.
- Existing target dataset folders are refused to avoid accidental overwrites.
- `imagesTr`, `labelsTr`, optional `imagesTs`, `labelsTs`, `imagesVal`, and `labelsVal` are copied when present.
- `dataset.json` is changed from `modality` to `channel_names`, from int-to-name labels to name-to-int labels, and receives `file_ending: ".nii.gz"`.

## Manual conversion checklist

When writing a custom converter or preparing data manually:

1. Pick an unused `DatasetXXX_Name` under `nnUNet_raw`.
2. Create `imagesTr`, `labelsTr`, optional `imagesTs`, and `dataset.json`.
3. Rename each training image channel to `{case_id}_0000{file_ending}`, `{case_id}_0001{file_ending}`, ...
4. Rename each training label to `{case_id}{file_ending}`.
5. Ensure every case has all channels declared in `channel_names`.
6. Ensure image and segmentation geometries match for each case.
7. Use one lossless file ending consistently across images, labels, and inference.
8. Set labels with `background: 0`; add `regions_class_order` or `ignore` only when needed.
9. Preserve region label order if generating JSON programmatically.
10. Run the bundled validator before planning/preprocessing.

## Bundled metadata validator

From the root of a generated skill checkout or by path to this sub-skill:

```bash
python sub-skills/data-preparation/scripts/validate_dataset_json.py /path/to/nnUNet_raw/Dataset123_MyDataset
```

Use deeper filename checks:

```bash
python sub-skills/data-preparation/scripts/validate_dataset_json.py /path/to/nnUNet_raw/Dataset123_MyDataset --check-files
```

What it checks:

- Folder name matches `DatasetXXX_Name`.
- Required `imagesTr`, `labelsTr`, and `dataset.json` exist.
- `dataset.json` has required `channel_names`, `labels`, `numTraining`, and `file_ending` fields.
- Channel indices are consecutive from `0`.
- `background` is label `0`.
- Normal label values are consecutive.
- Region labels have a valid `regions_class_order`.
- `ignore` is the highest integer label and is not part of `regions_class_order`.
- `numTraining` matches label files when `--check-files` is used.
- Training and optional test image filenames use expected channel suffixes and file ending.
- Every training case has the expected channels and a matching label file.

What it does not check:

- Image readability.
- Geometry, spacing, orientation, or co-registration.
- Actual voxel label values inside segmentation files.
- Whether a custom reader/writer class is importable.

Run nnU-Net's planning/preprocessing validation after metadata/file-name checks when you need image geometry and label-content validation.

## Tiny fixture pattern for validator checks

The validator can run on empty placeholder files because it validates names and metadata only:

```text
Dataset901_Toy/
├── dataset.json
├── imagesTr/
│   ├── case001_0000.nii.gz
│   └── case001_0001.nii.gz
└── labelsTr/
    └── case001.nii.gz
```

Use this to test dataset conventions before wiring a real conversion pipeline.
