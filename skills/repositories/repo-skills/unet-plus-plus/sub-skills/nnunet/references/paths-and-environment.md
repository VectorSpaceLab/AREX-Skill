# nnU-Net paths and environment

## Required path variables

nnU-Net expects three public path variables:

- `nnUNet_raw_data_base`
- `nnUNet_preprocessed`
- `RESULTS_FOLDER`

The package derives its working directories from those variables.

## Expected data layout

The canonical task layout uses a folder named like `TaskXXX_Name` with:

- `imagesTr/`
- `labelsTr/`
- `imagesTs/`

Common file shape expectations:

- Training and test images are NIfTI files.
- Modalities are encoded by suffixes such as `_0000.nii.gz`, `_0001.nii.gz`,
  etc.
- Task names are kept in the `Task###_...` pattern used by the repository and
  the Medical Segmentation Decathlon conversion helpers.

## Preprocessing and output folders

When the path variables are set, nnU-Net creates or uses:

- raw data under `.../nnUNet_raw_data/`
- cropped data under `.../nnUNet_cropped_data/`
- preprocessing output under `nnUNet_preprocessed/TaskXXX_Name`
- training and inference outputs under `RESULTS_FOLDER/nnUNet/...`

## Install / runtime assumptions

The inspected snapshot worked with:

- a modern PyTorch CUDA environment for `nnunet`
- `batchgenerators==0.21` because newer releases changed the import surface
- `matplotlib` for CLI imports
- `requests` for pretrained-model helpers

Those are workflow notes, not a promise that every future release uses the same
resolver results.

## CLI and runtime notes

- `nnUNet_train` and `nnUNet_predict` report missing path variables early.
- `nnUNet_plan_and_preprocess` needs a valid raw dataset root before it can do
  anything meaningful.
- `nnUNet_download_pretrained_model` and the pretrained-model info helpers need
  `requests`.
- The advanced `nnUNet_train_DP` and `nnUNet_train_DDP` entry points should be
  treated as separate operational paths from the default training script.

## What to check first when something fails

1. Are the three path variables set?
2. Does the Task folder name match the expected `TaskXXX_...` shape?
3. Are `batchgenerators`, `matplotlib`, and `requests` importable?
4. Does `torch.cuda.is_available()` report the expected GPU backend?
