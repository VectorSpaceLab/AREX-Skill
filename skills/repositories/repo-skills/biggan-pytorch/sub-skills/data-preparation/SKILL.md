---
name: data-preparation
description: "Prepare and route BigGAN-PyTorch ImageFolder, CIFAR10/CIFAR100,
  ImageNet HDF5, and Inception-moment data with the repository's exact mappings,
  transforms, and resource safeguards."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# BigGAN-PyTorch data preparation

Use this sub-skill when preparing a dataset for `train.py`, building an
ImageNet HDF5 cache, checking a cache, or generating the reference Inception
moments used by FID. This is runtime guidance for the checked-out
BigGAN-PyTorch repository. Run repository commands from the repository root;
invoke bundled helpers through the root skill directory, and keep large data
and metric outputs in an explicit data/output location.

Set `SKILL_ROOT` to the directory containing the root `SKILL.md` and
`REPO_ROOT` to the BigGAN-PyTorch checkout before using the commands below.

## Safety and route selection

- **ImageNet downloads and dataset acquisition are network-dependent and
  expensive.** Do not download ImageNet or CIFAR implicitly as a smoke test.
  CIFAR's torchvision download is also network-dependent; use
  `download=False` only after the archive has been installed and verified.
- **HDF5 conversion is expensive.** It reads every source image, writes a
  potentially very large file, and consumes substantial time and disk. The
  repository's `scripts/utils/prepare_data.sh` is a recipe, not a safe smoke
  test. Inspect with `--help` or use the bundled metadata-only validator
  before approving a conversion.
- **Inception moments require CUDA in the source implementation.**
  `calculate_inception_moments.py` hard-codes `device = 'cuda'`, walks the full
  dataset, and accumulates activations in host RAM. It is a full metric job,
  not a quick validation.
- Choose one representation and make its data root explicit:
  - `I32`, `I64`, `I128`, or `I256`: ImageFolder/ImageNet directories.
  - `I32_hdf5`, `I64_hdf5`, `I128_hdf5`, or `I256_hdf5`: preprocessed
    `ILSVRC_HDF5` files.
  - `C10` or `C100`: the repository's CIFAR loaders at native 32x32.

Read `references/data-formats.md` for schemas and root mappings,
`references/workflows.md` for command sequences and resource choices, and
`references/troubleshooting.md` for failure diagnosis. The references are
relative to this data-preparation sub-skill directory. Use the validator via
`$SKILL_ROOT/sub-skills/data-preparation/scripts/validate_hdf5.py` so the
command remains resolvable when copied from the skill root.

## Canonical command sequence

From the checkout, after an ImageNet tree has been deliberately provisioned
under `data/ImageNet`, the README's default 128px recipe is:

```bash
python make_hdf5.py --dataset I128 --batch_size 256 --data_root data
python calculate_inception_moments.py --dataset I128_hdf5 --data_root data
```

The first command creates `data/ILSVRC128.hdf5`; the second reads that file
and writes `I128_inception_moments.npz` in the **current working directory**.
The recipe does not download ImageNet. Confirm free disk, RAM, CUDA, and
whether the output moment file should instead be moved to the configured
metrics root before starting either expensive command.

For a small, already-installed dataset, first inspect a loader or run a
one-batch diagnostic with `num_workers=0`, then scale `batch_size` and workers.
Do not claim a full data-preparation verification from `--help` alone.

## Loader behavior that must be preserved

`utils.get_data_loaders()` appends `root_dict[dataset]` to `data_root`, builds
one training `DataLoader`, and returns it in a one-element list. The dataset
key controls resolution, class count, root name, and model metadata. Use
`--shuffle` for training unless deliberately reproducing ordered traversal;
`drop_last=True` is the default in normal loader use. `pin_memory` is enabled
by default and can be disabled with `--no_pin_memory`.

- ImageFolder data is decoded as RGB with PIL (or accimage when selected by
  torchvision), then transformed. Supported suffixes are `.jpg`, `.jpeg`,
  `.png`, `.ppm`, `.bmp`, and `.pgm`. Class directories and nested image files
  are traversed in sorted order, so classes receive stable lexicographic
  indices. An index listing is cached as `<dataset>_imgs.npz` in the process's
  current working directory; remove the cache after changing classes or files.
- CIFAR10 and CIFAR100 are read from torchvision-style pickle archives. Each
  sample becomes a PIL image before the configured transform. Both are native
  32x32; `C10` has 10 classes and `C100` has 100. The custom CIFAR loader reads
  the archive arrays into memory regardless of its `load_in_mem` argument.
  `val_split` and `train='validate'` are supported by the class but are not
  exposed by the normal `get_data_loaders` convenience call.
- HDF5 samples are stored as NCHW uint8 and are converted by
  `ILSVRC_HDF5` to float tensors with `((pixel / 255) - 0.5) * 2`, i.e.
  approximately `[-1, 1]`. The HDF5 loader intentionally ignores the
  torchvision `transform` argument; `--augment` therefore does not add random
  crops or flips to an `_hdf5` dataset.

## Transform and resource decisions

For non-HDF5 ImageNet, no augmentation means center-crop the shorter square
from the image's long-edge geometry, resize to the selected resolution, then
`ToTensor()` and normalize each channel with mean/std `[0.5, 0.5, 0.5]`.
With `--augment`, use a random long-edge square crop, resize to the selected
resolution, and random horizontal flip before the same tensor conversion and
normalization. CIFAR without augmentation applies only tensor conversion and
that normalization; CIFAR augmentation is `RandomCrop(32, padding=4)` plus
`RandomHorizontalFlip()`.

Run the bundled checker from the repository root as
`python "$SKILL_ROOT/sub-skills/data-preparation/scripts/validate_hdf5.py" "$REPO_ROOT/data/ILSVRC128.hdf5" --resolution 128 --check-label-range`;
it is metadata-only unless label range checking is requested.

`--load_in_mem` has different practical consequences:

- ImageFolder decodes and transforms every image during dataset construction
  and retains the transformed samples and labels. If the transform is random,
  its random crop/flip is sampled once at construction rather than anew each
  epoch. This is fast but can consume far more RAM than the compressed source.
- HDF5 loads both `imgs` and `labels` arrays into RAM. Omitting it causes the
  loader to open the HDF5 file and read the requested sample for each
  `__getitem__`; this saves RAM but can make I/O and multi-worker behavior
  slower. The README reports roughly a 64GB I128 file and recommends about
  96GB+ RAM for the training recipe that loads it.
- More `num_workers` can hide image decode/I/O latency, but each worker adds
  process overhead and HDF5 access pressure. Start HDF5 with `0` or a small
  worker count, then increase only after measuring. `pin_memory` improves
  host-to-CUDA transfer at the cost of pinned host memory.

For a custom dataset, add a loader in `datasets.py` and keep `dset_dict`,
`imsize_dict`, `root_dict`, `nclass_dict`, and `classes_per_sheet_dict` in
`utils.py` synchronized. Verify root, image size, channels, class ids, and
normalization before training or moments generation.
