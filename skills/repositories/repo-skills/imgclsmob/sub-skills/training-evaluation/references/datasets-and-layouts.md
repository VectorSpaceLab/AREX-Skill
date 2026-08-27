# Datasets and layouts

The classification entrypoints obtain a dataset metainfo object from
`gluon.dataset_utils.get_dataset_metainfo` or
`pytorch.dataset_utils.get_dataset_metainfo`. The generic metainfo parser
adds `--data-dir`, `--num-classes`, and `--in-channels`; Gluon also adds
`--net-root`. `--work-dir` only supplies the default root:
`<work-dir>/<root_dir_name>`. Always pass `--data-dir` when the data is not at
that preset location.

## Classification metainfo

| Dataset | Frameworks | Classes | Channels / input | Default root suffix | Local layout and split behavior | Metrics |
|---|---|---:|---|---|---|---|
| `ImageNet1K` | Gluon, PyTorch | 1000 | 3 / `(224, 224)` | `imagenet` | Folder layout: `train/<class>/...` and `val/<class>/...`. The dataset classes append `train` for training and `val` for every non-training mode. | `Top1Error` and `TopKError(top_k=5)`; labels `Val.Top1`, `Val.Top5`; key index `1`. |
| `ImageNet1K_rec` | Gluon only | 1000 | 3 / `(224, 224)` | `imagenet_rec` | MXNet image-record layout: `train.rec`, `train.idx`, `val.rec`, `val.idx` directly under the root. The record iterators are reset between passes. | Same ImageNet Top-1/Top-5 error pair; key index `1`. |
| `CIFAR10` | Gluon, PyTorch | 10 | 3 / `(32, 32)` | `cifar10` | Backend-native CIFAR cache under the root. Gluon and PyTorch dataset wrappers use their native cache formats; the PyTorch wrapper is constructed with `download=True` if data is absent. In this code, `mode="val"` selects the non-training/test partition. | `Top1Error`, label `Val.Err`; key index `0`. |
| `CIFAR100` | Gluon, PyTorch | 100 | 3 / `(32, 32)` | `cifar100` | Same native-cache rule as CIFAR10. Gluon uses the fine-label dataset; PyTorch uses its CIFAR100 wrapper. | `Top1Error`, label `Val.Err`; key index `0`. |
| `SVHN` | Gluon, PyTorch | 10 | 3 / `(32, 32)` | `svhn` | Native SVHN cache. The expected split files are `train_32x32.mat` and `test_32x32.mat`; the wrappers download them when absent. The source remaps SVHN label `10` (digit zero) to label `0`. | `Top1Error`, label `Val.Err`; key index `0`. |
| `CUB200_2011` | Gluon, PyTorch | 200 | 3 / `(224, 224)` inherited from ImageNet metainfo | `CUB_200_2011` | Metadata files and image tree are required; see the CUB section below. `mode="train"` uses `split_flag == 1`; `val` and `test` use `split_flag == 0`. | `Top1Error`, label `Val.Err`; key index `0`. |

`Top1Error` and `TopKError` report errors rather than accuracies, so lower is
better. The `saver_acc_ind` value identifies the metric index used by the
training controller; it is not a promise that a checkpoint is present.

## ImageNet folder versus record layouts

Do not interchange the two ImageNet names:

- **Folder (`ImageNet1K`)**: one root contains `train/` and `val/`; each split
  contains the class directories consumed by MXNet `ImageFolderDataset` or
  PyTorch `torchvision.datasets.ImageFolder`. The expected class count is
  1000. Use this name for both Gluon and PyTorch.
- **Record (`ImageNet1K_rec`)**: one root contains all four record/index files:
  `train.rec`, `train.idx`, `val.rec`, and `val.idx`. Only the Gluon dataset
  metainfo maps this name to `mx.io.ImageRecordIter`; PyTorch has no matching
  record metainfo in the classification dataset map. The recorded training
  sample count is `1,281,167`.

The folder transforms use ImageNet RGB mean/std `(0.485, 0.456, 0.406)` and
`(0.229, 0.224, 0.225)` after conversion to tensor values. Validation uses the
configured resize inverse factor `0.875`, so the default resize value is
`ceil(224 / 0.875) = 256`, followed by a center crop to `224`.

The Gluon record iterator has a separate, source-defined raw-pixel default:
mean `(123.68, 116.779, 103.939)` and std `(58.393, 57.12, 57.375)` passed as
`mean_r/g/b` and `std_r/g/b`. Do not copy those 0-255 record constants into a
folder/PyTorch command, and do not silently replace the record preprocessing
with the folder transform.

## CUB-200-2011 required tree

The supplied `--data-dir` must contain all of the following:

```text
<data-dir>/
├── images.txt
├── image_class_labels.txt
├── train_test_split.txt
└── images/
    └── <class-name>/<image-file>
```

`images.txt` maps image ids to relative image paths,
`image_class_labels.txt` supplies class ids, and `train_test_split.txt` supplies
split flags. Class ids are converted from 1-based metadata to 0-based labels.
The checker in [the bundled script](../scripts/check_dataset_layout.py) verifies
presence only; it does not decode images or download the archive.

CUB metainfo exposes `--no-aux`. In Gluon evaluation this clears the test
model's `aux` extra and changes the extra-layer loading policy. The PyTorch
metainfo also defines the flag, but its field naming differs from the field
consumed by the generic evaluation path; verify a CUB checkpoint's model shape
with [model-inference](../../model-inference/SKILL.md) rather than assuming the
flag remaps every checkpoint.

## Native-cache datasets and no-network operation

CIFAR10, CIFAR100, and SVHN are wrapped by backend-native dataset classes. A
missing cache can trigger a download when the real entrypoint constructs the
dataset. The layout checker deliberately does not invoke those classes and
never downloads. An empty root returns `missing_local_data`; a non-empty root
returns `indeterminate_native_cache`, because exact integrity is owned by the
selected framework's dataset implementation. For an offline run, populate the
cache out of band, run the framework's integrity check with downloading
explicitly disabled, and stop before the evaluation command if that check does
not pass.

The normalized CIFAR/SVHN transforms use mean `(0.4914, 0.4822, 0.4465)` and
std `(0.2023, 0.1994, 0.2010)`. These values are inherited by CIFAR100 and
SVHN metainfo in both verified classification paths.
