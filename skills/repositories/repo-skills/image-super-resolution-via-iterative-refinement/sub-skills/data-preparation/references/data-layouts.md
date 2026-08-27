# Data layouts

Purpose: capture the dataset layout contract used by the repo's data loader and preprocessing script so a later agent can validate or recreate a root without reopening the source tree.

Evidence consulted: README data-prepare sections, `data/prepare_data.py`, `data/LRHR_dataset.py`, `data/util.py`, and the dataset fields in `config/*.json`.

## Quick summary

The repo supports two storage styles for super-resolution data:

- `datatype: img` — a directory tree with three image folders: `lr_<L>`, `hr_<R>`, and `sr_<L>_<R>`.
- `datatype: lmdb` — a single LMDB root that stores the same triplets as keyed PNG bytes plus a `length` entry.

The paired widths come from the config fields `l_resolution` and `r_resolution`. The source scripts expect the low-resolution value first and the high-resolution value second.

## Image-directory layout (`datatype: img`)

A minimal root looks like this:

```text
example_16_128/
├── hr_128/
│   ├── 00000.png
│   ├── 00001.png
│   └── ...
├── lr_16/
│   ├── 00000.png
│   ├── 00001.png
│   └── ...
└── sr_16_128/
    ├── 00000.png
    ├── 00001.png
    └── ...
```

### Loader behavior

`LRHRDataset` resolves the directories from the config like this:

- `dataroot/sr_<L>_<R>` is always read.
- `dataroot/hr_<R>` is always read.
- `dataroot/lr_<L>` is read only when `mode: LRHR`.

The loader uses `data/util.py:get_paths_from_images`, which:

- requires the directory to exist,
- walks the tree recursively,
- accepts image files with these extensions: `.jpg`, `.JPG`, `.jpeg`, `.JPEG`, `.png`, `.PNG`, `.ppm`, `.PPM`, `.bmp`, `.BMP`,
- sorts the discovered paths,
- fails if no supported image file is present.

The dataset then opens each file with PIL and converts it to RGB before augmentation.

### Validation rules for the image tree

For a valid triplet root:

- `lr_<L>`, `hr_<R>`, and `sr_<L>_<R>` should all exist as directories.
- The image counts should match.
- The relative image paths should match across the three folders.
- The directory contents should be image-only or at least free of stray files that would change the sorted path lists.

The bundled validator script checks those rules for `img` layouts.

## LMDB layout (`datatype: lmdb`)

The preprocessing script writes a single LMDB root with these entries:

- `length` — UTF-8 string containing the number of samples written.
- `lr_<L>_<index>` — low-resolution PNG bytes.
- `hr_<R>_<index>` — high-resolution PNG bytes.
- `sr_<L>_<R>_<index>` — bicubic SR PNG bytes.

The source writer uses zero-padded indices with width 5, for example `00000`, `00001`, and so on. The reader uses the same key format.

### Loader behavior

`LRHRDataset` opens the LMDB root in read-only mode and reads `length` first. If `data_len <= 0`, the loader uses the full dataset length; otherwise it truncates to the smaller of the requested length and the stored length.

For each sample:

- it reads the `hr` and `sr` keys for the requested index,
- it also reads `lr` when `mode: LRHR`,
- if a key is missing, it retries with a random valid index until it finds a complete sample.

That means an interrupted or partial LMDB write can look like a dataset with holes rather than a hard failure until a sample hits the missing key.

## Config fields that matter

| Field | Meaning | Notes |
| --- | --- | --- |
| `datasets.*.dataroot` | Root path for the dataset | For `img`, this is the directory that contains the three layout folders. For `lmdb`, this is the LMDB root. |
| `datasets.*.datatype` | Storage style | Must be `img` or `lmdb`. Any other value is rejected by the dataset class. |
| `datasets.*.mode` | Which images the loader returns | `HR` loads HR/SR; `LRHR` loads LR/HR/SR. |
| `datasets.*.l_resolution` | Low-resolution size | Used in folder names and LMDB key names. |
| `datasets.*.r_resolution` | High-resolution size | Used in folder names and LMDB key names. |
| `datasets.*.data_len` | Optional sample cap | `<= 0` means use the full dataset length. |

## Source preprocessing behavior

The repo's `data/prepare_data.py` follows the same naming contract:

- `--size L,R` chooses the low/high pair.
- `--out ROOT` is expanded to `ROOT_L_R` before writing.
- `-l/--lmdb` switches from image folders to LMDB storage.
- The script writes `lr_<L>`, `hr_<R>`, and `sr_<L>_<R>` outputs with PNG content.
- The LMDB writer updates `length` as samples are written.

This sub-skill does not bundle the full converter. Use the layout contract above to validate a finished root or to create a small fixture with [`../scripts/prepare_tiny_dataset.py`](../scripts/prepare_tiny_dataset.py).

## Sanity checklist

- The config pair `(l_resolution, r_resolution)` matches the folder or LMDB key suffixes.
- The chosen `datatype` matches the storage style.
- The dataset root points at the final prepared root, not the unsuffixed source folder.
- The triplet counts match and the relative paths line up.
- If LMDB is used, `length` and the indexed keys are present for every sample.
