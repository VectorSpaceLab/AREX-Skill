# Path setup

nnU-Net v2 uses environment variables to find raw datasets, preprocessed data, trained models, and optional external trainer code.

## Required variables

Set these before dataset conversion, planning, preprocessing, training, or inference:

```bash
export nnUNet_raw="/path/to/nnUNet_raw"
export nnUNet_preprocessed="/path/to/nnUNet_preprocessed"
export nnUNet_results="/path/to/nnUNet_results"
```

Windows PowerShell equivalent:

```powershell
$Env:nnUNet_raw = "C:/path/to/nnUNet_raw"
$Env:nnUNet_preprocessed = "C:/path/to/nnUNet_preprocessed"
$Env:nnUNet_results = "C:/path/to/nnUNet_results"
```

Use persistent shell/profile settings for normal work and temporary exports for one-off commands.

## What each path stores

- `nnUNet_raw`: one folder per dataset, named `DatasetXXX_Name`, each containing `dataset.json`, `imagesTr`, `labelsTr`, and optional `imagesTs`.
- `nnUNet_preprocessed`: fingerprints, plans, and preprocessed arrays generated from raw data. Put this on fast local storage when possible.
- `nnUNet_results`: training outputs, checkpoints, folds, exported models, and installed pretrained models.
- `nnUNet_extTrainer`: optional OS-path-separator-separated directories for custom `nnUNetTrainer` subclasses outside the package.

## Lazy path behavior

In nnU-Net v2 these path objects are lazy environment-path wrappers. They can be imported while unset, but converting them to strings or using them as filesystem paths requires the corresponding environment variable. If unset, they raise a runtime error explaining which variable is missing.

Practical implication: a script may import `nnunetv2.paths.nnUNet_raw` successfully but fail later at `join(nnUNet_raw, ...)`, `str(nnUNet_raw)`, or `os.fspath(nnUNet_raw)` if the variable is not defined.

## Dataset ID location

Each dataset belongs under:

```text
$nnUNet_raw/DatasetXXX_Name/
├── dataset.json
├── imagesTr/
├── labelsTr/
└── imagesTs/        # optional
```

`XXX` is a three-digit dataset ID. Avoid IDs already present in `nnUNet_raw`, `nnUNet_preprocessed`, or `nnUNet_results`; conversion tools check for conflicts because reusing an ID can mix raw data, preprocessed data, and model outputs from different datasets.

## Updating an existing dataset

When replacing raw data for an existing dataset ID/name, remove stale preprocessed data for that dataset before planning again:

```bash
rm -rf "$nnUNet_preprocessed/Dataset123_MyDataset"
```

If old trained models no longer correspond to the new data, also move or remove the matching folder under `nnUNet_results`.
