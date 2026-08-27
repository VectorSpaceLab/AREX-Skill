# Data formats, labels, and root mappings

## Dataset key matrix

The dictionaries in `utils.py` are the authoritative routing table:

| Key | Loader | `data_root` suffix | Size | Classes |
|---|---|---|---:|---:|
| `I32` / `I64` / `I128` / `I256` | `datasets.ImageFolder` | `ImageNet` | 32 / 64 / 128 / 256 | 1000 |
| `I32_hdf5` / `I64_hdf5` / `I128_hdf5` / `I256_hdf5` | `datasets.ILSVRC_HDF5` | `ILSVRC32.hdf5` / `ILSVRC64.hdf5` / `ILSVRC128.hdf5` / `ILSVRC256.hdf5` | 32 / 64 / 128 / 256 | 1000 |
| `C10` | `datasets.CIFAR10` | `cifar` | 32 | 10 |
| `C100` | `datasets.CIFAR100` | `cifar` | 32 | 100 |

Thus `--data_root data --dataset I128` reads `data/ImageNet`, while
`--data_root data --dataset I128_hdf5` reads `data/ILSVRC128.hdf5`. The
`root_dict` values are appended with `/`; do not pass the already-appended
folder as `data_root` unless you intend the resulting doubled path.

`classes_per_sheet_dict` is presentation metadata, not a label validator: it
uses 50/50/20/20 for ImageNet 32/64/128/256, 10 for C10, and 100 for C100.
When adding a dataset, update the loader and all five convenience mappings,
not just the class count.

## ImageFolder / ImageNet tree

`ImageFolder` expects one or more class directories beneath the selected root:

```text
<data_root>/ImageNet/
  n00000001/
    image_0001.JPEG
  n00000002/
    nested/image_0002.jpg
```

The class directory names are sorted lexicographically and assigned indices
`0..N-1`; the recursive file walk and supported image extensions are sorted as
well. Files are decoded as RGB with the selected torchvision backend. Accepted
extensions in this repository are `.jpg`, `.jpeg`, `.png`, `.ppm`, `.bmp`, and
`.pgm` (case-insensitive).

On first construction the loader walks the tree and writes a compressed
`<dataset>_imgs.npz` index, for example `I128_imgs.npz`, using the current
working directory unless an explicit `index_filename` is passed. On later
runs it trusts that index. Delete or regenerate it after adding/removing
classes, moving files, or changing class names; an old cache can preserve
wrong paths or label ids.

## CIFAR10 and CIFAR100

`CIFAR10` follows torchvision's archive layout under
`<data_root>/cifar/cifar-10-batches-py`; it downloads by default in the class
constructor when the archive is absent. The download is network-dependent and
must be explicitly approved. `CIFAR100` subclasses this implementation with
`cifar-100-python`, the Toronto URL, its archive filename and checksums. It
uses `fine_labels` when present (otherwise `labels`), whereas CIFAR10 uses
`labels` (or its fallback). Training data is reshaped from the pickle's
`(N, 3*32*32)` arrays to HWC `(N, 32, 32, 3)`; test data is similarly HWC and
contains 10,000 examples in the source loader.

The loader can create a deterministic per-class validation subset with
`val_split`, `validate_seed`, and `train='validate'`; the normal
`get_data_loaders()` path does not expose those options. Its `load_in_mem`
parameter is not a switch for lazy decoding: the pickle arrays are read into
RAM during initialization in either case. Each returned sample is converted
to a PIL image and then passed through the configured transform.

## ILSVRC_HDF5 schema

`make_hdf5.py` creates one file named `ILSVRC{size}.hdf5` in `data_root`.
The required datasets are:

```text
imgs:   uint8, shape (N, 3, size, size), chunked on the sample axis
labels: int64, shape (N,), same N as imgs
```

For ImageNet, labels should be integer class ids in `0..999`, matching the
sorted ImageFolder class mapping. `imgs` contains channel-first pixels in
`[0, 255]`; the converter obtains them by reversing the regular loader's
`[-1, 1]` normalization and casting to `uint8`. HDF5 chunking is used on both
arrays and compression is optional LZF.

`ILSVRC_HDF5` reads `labels` length during initialization. With
`load_in_mem=False`, it opens the file and reads `imgs[index]` and
`labels[index]` for each sample; with `load_in_mem=True`, it reads both whole
arrays once. It then applies the fixed conversion
`((torch.from_numpy(img).float() / 255) - 0.5) * 2`, returns a CHW tensor and
an integer target, and does not apply a torchvision image transform. A valid
file therefore must not be HWC, float-valued, or already normalized.

Use the bundled read-only check before training. Set `SKILL_ROOT` to the
directory containing the root skill `SKILL.md` and `REPO_ROOT` to the checked-
out BigGAN-PyTorch repository; run the command from `REPO_ROOT`:

```bash
python "$SKILL_ROOT/sub-skills/data-preparation/scripts/validate_hdf5.py" \
  "$REPO_ROOT/data/ILSVRC128.hdf5" --resolution 128 --classes 1000 --check-label-range
```

The optional label-range scan reads labels but does not rewrite the file.
