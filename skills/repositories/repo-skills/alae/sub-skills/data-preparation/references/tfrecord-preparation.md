# TFRecord Preparation for ALAE

## When to read

Read this when a user needs ALAE training/evaluation TFRecords, wants to adapt one of the repository dataset scripts, or asks why a dataset-preparation command is failing. Start with `references/data-layouts.md` and `scripts/validate_alae_data_layout.py` when the immediate task is only to verify paths.

## Common requirements and safety notes

- ALAE training reads TFRecords through DareBlopy/PyTorch. The conversion scripts write TensorFlow `Example` records with `data` bytes and usually a `label`.
- The conversion and split scripts use **TensorFlow 1.x APIs** such as `tf.python_io.TFRecordWriter`, `tf.python_io.TFRecordOptions`, `tf.Session`, and `tf.data.TFRecordDataset`. TensorFlow 2.x without `compat.v1` shims will fail.
- Run source dataset scripts from **the ALAE repository root** or set `PYTHONPATH` to that checkout root. The scripts import root modules such as `defaults` and `net`.
- Most original configs assume raw or generated datasets live under `/data/datasets/`. Override config keys at the command line or create a deliberate symlink; do not depend on a current production checkout path.
- These scripts are **not safe dry-run tools**: several download data, open large archives, or write many multi-resolution TFRecord shards. Confirm storage, network approval, and raw-data locations before running them.

Command shape for original source scripts from a checkout root:

```bash
cd <ALAE repository root>
PYTHONPATH="$PWD" python dataset_preparation/<script>.py \
  --config-file configs/<preset>.yaml \
  DATASET.PATH '/absolute/or/relative/train-r%02d.tfrecords.%03d' \
  DATASET.PATH_TEST '/absolute/or/relative/test-r%02d.tfrecords.%03d'
```

The trailing overrides use YACS `KEY VALUE` pairs. Quote path patterns so the shell preserves `%02d` and `%03d`.

## Dataset-specific recipes

| Dataset/workflow | Source script | Default config | What it writes or does | Caveats |
| --- | --- | --- | --- | --- |
| MNIST 32x32 | `dataset_preparation/prepare_mnist_tfrecords.py` | `configs/mnist.yaml` | Downloads MNIST through `dlutils`, pads 28x28 grayscale images to 32x32, writes train parts for LOD 5, 4, 3, 2 and test at LOD 5. | Network-bound by default; uses TensorFlow 1.x and PyTorch ops. The test branch does not generate every downsampled LOD shard used by generic train=False loaders. |
| CelebA 128x128 | `dataset_preparation/prepare_celeba_tfrecords.py` | `configs/celeba.yaml` | Reads CelebA split/identity metadata and `img_align_celeba.zip`, center-crops faces to 128, writes train/test TFRecords from `MAX_RESOLUTION_LEVEL` down to LOD 2. | Hard-coded raw data under `/data/datasets/CelebA/...`; large zip and metadata required; filters a fixed list of corrupted images. |
| CelebA-HQ 256x256 | `dataset_preparation/prepare_celeba_hq_tfrecords.py` | `configs/celeba-hq256.yaml` | Reads pre-generated CelebA-HQ PNG/JPG files, writes multi-resolution train/test TFRecords. | Hard-coded `source_path` is `/data/datasets/celeba-hq/data1024x1024`; obtaining CelebA-HQ is external and expensive. |
| FFHQ split | `dataset_preparation/split_tfrecords_ffhq.py` | `configs/ffhq.yaml` | Splits official StyleGAN FFHQ TFRecords from `DATASET.FFHQ_SOURCE` into `DATASET.PATH` train shards and `DATASET.PATH_TEST` test shards. | Requires existing official TFRecords at all LODs. Uses a fixed `ffhq_train_size = 60000`; remaining batches become test shards. Large disk writes. |
| LSUN bedroom split | `dataset_preparation/split_tfrecords_bedroom.py` | `configs/bedroom.yaml` | Splits official StyleGAN/LSUN bedroom TFRecords from `DATASET.FFHQ_SOURCE` into train shards under `DATASET.PATH`. | The config key name `FFHQ_SOURCE` is reused for bedroom source records. No test path is configured. Large dataset and disk use. |
| ImageNet samples / partial converter | `dataset_preparation/prepare_imagenet.py` | `configs/imagenet.yaml` (not present in this checkout) | Parses ImageNet metadata, writes sample images to `dataset_samples/imagenet256x256`, then the script exits before the full TFRecord conversion branch. | Hard-coded `/data/datasets/ImageNet_bak/...`; missing default config; treat as reference-only unless editing the script deliberately. |
| SVHN | `dataset_preparation/prepare_svhn_tfrecords.py` | `configs/svhn.yaml` (not present in this checkout) | Downloads SVHN through `torchvision.datasets.SVHN`, writes 32x32 RGB train/test TFRecords and downsampled LODs. | Network-bound; default config is absent; function is still named `prepare_mnist` internally. |
| Legacy CelebA pickle | `dataset_preparation/prepare_celeba.py` | none | Downloads CelebA zip and writes pickle folds, not TFRecords. | Source comment says it is not used in the current pipeline; import-time Google Drive download and old `scipy.misc` APIs make it legacy/reference-only. |

## Path pattern checklist

Before running any conversion or split:

1. Choose a config preset or custom YAML whose `MODEL.CHANNELS`, `MODEL.LAYER_COUNT`, and `DATASET.MAX_RESOLUTION_LEVEL` match the dataset resolution.
2. Ensure `DATASET.PATH` is an old-style Python pattern accepting `(lod, part_index)`, for example `.../ffhq-r%02d.tfrecords.%03d`.
3. Ensure `DATASET.PATH_TEST` is present when a train=False loader, FFHQ real reconstruction, or metric script needs test records.
4. Set `DATASET.PART_COUNT` to the number of train parts and, when using multiple GPUs, keep it divisible by the training world size.
5. Set `DATASET.PART_COUNT_TEST` when `PATH_TEST` contains more than one shard. FFHQ uses `2`; most defaults inherit `1`.
6. Check that parent directories are writable and have enough space for all LODs from 2 through `MAX_RESOLUTION_LEVEL`.
7. Run the bundled validator before the expensive command (shown relative to this sub-skill directory):

```bash
python scripts/validate_alae_data_layout.py \
  --config-file <ALAE repository root>/configs/ffhq.yaml \
  --repo-root <ALAE repository root> \
  --world-size 8
```

Add `--check-tfrecords` only when records should already exist; it can report many missing files.

## Command examples

MNIST with custom output paths:

```bash
cd <ALAE repository root>
PYTHONPATH="$PWD" python dataset_preparation/prepare_mnist_tfrecords.py \
  --config-file configs/mnist.yaml \
  DATASET.PATH '/data/datasets/mnist32/tfrecords/mnist-r%02d.tfrecords.%03d' \
  DATASET.PATH_TEST '/data/datasets/mnist32/tfrecords/mnist_test-r%02d.tfrecords.%03d'
```

FFHQ split from official StyleGAN records:

```bash
cd <ALAE repository root>
PYTHONPATH="$PWD" python dataset_preparation/split_tfrecords_ffhq.py \
  --config-file configs/ffhq.yaml \
  DATASET.FFHQ_SOURCE '/data/datasets/ffhq-dataset/tfrecords/ffhq/ffhq-r%02d.tfrecords' \
  DATASET.PATH '/data/datasets/ffhq-split/train/ffhq-r%02d.tfrecords.%03d' \
  DATASET.PATH_TEST '/data/datasets/ffhq-split/test/ffhq-r%02d.tfrecords.%03d'
```

CelebA with prepared local raw-data symlink or overridden paths:

```bash
cd <ALAE repository root>
PYTHONPATH="$PWD" python dataset_preparation/prepare_celeba_tfrecords.py \
  --config-file configs/celeba.yaml \
  DATASET.PATH '/data/datasets/celeba/tfrecords/celeba-r%02d.tfrecords.%03d' \
  DATASET.PATH_TEST '/data/datasets/celeba-test/tfrecords/celeba-r%02d.tfrecords.%03d'
```

If the user does not have the hard-coded raw-data tree, stop and either create a deliberate `/data/datasets` symlink or edit/adapt the source script for explicit raw-data arguments before launching a multi-hour conversion.
