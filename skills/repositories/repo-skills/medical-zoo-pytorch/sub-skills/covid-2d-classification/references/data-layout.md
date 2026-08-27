# COVID 2D data layout

## COVIDx

The `COVIDxDataset` branch is a **3-class** RGB image classification path.

### Active manifests

The source loader reads these split files:

- `train_split_v2.txt`
- `test_split_v2.txt`

Legacy sample files also exist in the source tree:

- `train_COVIDx.txt`
- `test_COVIDx.txt`

### Manifest line format

Each line has three space-separated fields:

```text
<subject_id> <relative_image_path> <label>
```

Example:

```text
3 SARS-10.1148rg.242035193-g04mr34g0-Fig8a-day0.jpeg pneumonia
```

### Label mapping

The loader maps labels exactly as follows:

- `pneumonia` → `0`
- `normal` → `1`
- `COVID-19` → `2`

### Image root

The dataset loader joins the dataset root with the current mode and the path from the manifest:

```text
<dataset_path>/<mode>/<relative_image_path>
```

For the generated training route, `mode` is `train` or `val`.

### Image processing

- image is opened as RGB
- resized to the requested `dim` tuple
- converted to a tensor
- normalized with mean `[0.5, 0.5, 0.5]` and std `[1, 1, 1]`

### Notes

- The manifest filename is hard-coded in the source loader.
- Manifest paths must match the on-disk image layout exactly.
- The parser expects the label tokens to match the mapping above.
- The parser stops early if it sees the legacy sentinel line containing `/ c o`.

---

## CovidCT

The `CovidCTDataset` branch is a **2-class** chest CT classification path.

### Directory tree

The loader expects this structure under the provided `root_dir`:

```text
root_dir/
├── CT_COVID/
│   ├── <image>.png
│   └── ...
├── CT_NonCOVID/
│   ├── <image>.png
│   └── ...
├── trainCT_COVID.txt
├── trainCT_NonCOVID.txt
├── valCT_COVID.txt
├── valCT_NonCOVID.txt
├── testCT_COVID.txt
└── testCT_NonCOVID.txt
```

### Text file format

Each text file contains **one image filename per line**.

Example:

```text
2020.03.24.20042655-p17-68-1.png
2020.03.24.20042655-p17-68-2.png
```

### Label mapping

The class folders define the labels in fixed order:

- `CT_COVID` → `0`
- `CT_NonCOVID` → `1`

### Image processing

Train mode uses:

- `Resize(256)`
- `RandomResizedCrop(224)`
- `RandomHorizontalFlip()`
- `ToTensor()`
- ImageNet normalization

Validation mode uses:

- `Resize(224)`
- `CenterCrop(224)`
- `ToTensor()`
- ImageNet normalization

### Notes

- `CovidCTDataset` joins each filename with `root_dir/<class_name>/`.
- The constructor's `transform` argument is ignored by the current source.
- The dataset returns integer class indices only.

---

## Practical reminders

- `COVIDx` expects RGB chest X-ray files, not 3D volumes.
- `COVID_CT` expects 2D slice images, not CT volumes.
- Do not reuse 3D segmentation folder conventions here.
- Keep labels and `args.classes` in sync with the chosen branch.
