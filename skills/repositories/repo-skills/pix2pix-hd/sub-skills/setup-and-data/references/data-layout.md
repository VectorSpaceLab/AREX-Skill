# Data layout

This reference covers the bundled Cityscapes sample fixture and the folder names that `AlignedDataset` expects.

## Loader rules

`data/aligned_dataset.py` builds folder names from `phase` and `label_nc`:

- `label_nc > 0`
  - labels: `<phase>_label`
  - instances: `<phase>_inst`
  - images: `<phase>_img`
- `label_nc == 0`
  - labels: `<phase>_A`
  - images: `<phase>_B`
  - instances still use `<phase>_inst` unless `--no_instance` is set

Other relevant loader rules:

- files are discovered through `data/image_folder.py`
- images are sorted before pairing
- the loader expects equal sample counts in the folders it actually uses
- `load_features` adds an additional `<phase>_feat` lookup; detailed feature-cache layout belongs to the instance-features sub-skill

## Bundled Cityscapes sample

The repository ships a small fixture under `datasets/cityscapes/`.

```text
datasets/cityscapes/
├── train_label/
├── train_inst/
├── train_img/
├── test_label/
└── test_inst/
```

Verified sample counts in the current fixture:

| Folder | Count | Role |
| --- | ---: | --- |
| `train_label/` | 8 | label maps for the training smoke sample |
| `train_inst/` | 8 | instance maps for the training smoke sample |
| `train_img/` | 8 | RGB images for the training smoke sample |
| `test_label/` | 15 | label maps for the test smoke sample |
| `test_inst/` | 15 | instance maps for the test smoke sample |
| `test_img/` | absent | not required for the default test smoke path |

## Pairing expectations

A valid smoke layout should satisfy all of the following:

- each required folder exists
- each required folder contains at least one supported image file
- required folders for a phase have the same number of samples
- the sample IDs match after removing the Cityscapes suffixes such as `_gtFine_labelIds`, `_gtFine_instanceIds`, and `_leftImg8bit`

## Supported file types

`data/image_folder.py` recognizes image files with these extensions:

- `.jpg`, `.JPG`
- `.jpeg`, `.JPEG`
- `.png`, `.PNG`
- `.ppm`, `.PPM`
- `.bmp`, `.BMP`
- `.tiff`, `.TIFF`

## What this fixture is for

- parser smoke and one-sample loader checks
- validating folder naming before training or inference
- confirming the `tensor2label` and `tensor2im` utilities still work on a real sample

## What this fixture is not for

- full Cityscapes download or training-scale evaluation
- feature cache generation
- checkpointed inference or HTML output generation
