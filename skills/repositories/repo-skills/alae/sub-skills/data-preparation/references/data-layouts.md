# ALAE Data Layouts and Config Path Schemas

## When to read

Read this before preparing TFRecords, launching training, running reconstruction, or debugging missing sample/style-mixing inputs. The goal is to verify the filesystem contract encoded by an ALAE YAML config without reopening source files.

## Core config keys

| Key | Meaning | Validation rule |
| --- | --- | --- |
| `DATASET.PATH` | Train TFRecord pattern. ALAE formats it as `PATH % (lod, part_index)`. | Must contain two old-style integer placeholders, usually `r%02d` and `%03d`. Parent directories must be writable before conversion and files must exist before training. |
| `DATASET.PATH_TEST` | Test/evaluation TFRecord pattern. Used by train=False loaders and some metric/reconstruction workflows. | Same two-placeholder pattern as `PATH`; may be empty for configs that do not support test-set loading. |
| `DATASET.PART_COUNT` | Number of train shards per LOD. | Positive integer. For distributed training, it must be divisible by the world size because the loader asserts `PART_COUNT % world_size == 0`. |
| `DATASET.PART_COUNT_TEST` | Number of test shards per LOD. Defaults to `1` unless overridden. | Positive integer when `PATH_TEST` is used. FFHQ sets `2`. |
| `DATASET.FFHQ_SOURCE` | Source TFRecord pattern for split scripts. The name is reused by the bedroom split script. | One old-style integer placeholder for LOD, for example `.../ffhq-r%02d.tfrecords`. |
| `DATASET.MAX_RESOLUTION_LEVEL` | Highest LOD/resolution exponent. Image size is `2 ** lod`. | TFRecords are expected for each LOD from `2` through this value. Examples: 5 => 32, 7 => 128, 8 => 256, 10 => 1024. |
| `DATASET.SAMPLES_PATH` | Directory of sample images used for reconstruction/sample previews. | Relative paths resolve from the ALAE repository root. Use `no_path` only when intentionally disabling sample previews in training. |
| `DATASET.STYLE_MIX_PATH` | Directory containing style-mixing `src/` and `dst/` image subdirectories. | The style-mixing script expects `src/0..4` and `dst/0..5` as `.png` or `.jpg` images by default. |
| `OUTPUT_DIR` | Training artifact directory for checkpoints, logs, and generated outputs. | Relative paths resolve from the checkout root. Generation/training sub-skills handle checkpoint details; this sub-skill only checks path readiness. |

## TFRecord shard naming

ALAE's generic loader builds filenames by looping:

```text
for lod in 2..DATASET.MAX_RESOLUTION_LEVEL:
  for part_index in assigned_parts:
    filename = DATASET.PATH % (lod, part_index)
```

A standard path therefore looks like:

```text
/data/datasets/ffhq-split/train/ffhq-r02.tfrecords.000
/data/datasets/ffhq-split/train/ffhq-r03.tfrecords.000
...
/data/datasets/ffhq-split/train/ffhq-r10.tfrecords.015
```

Each record stores channel-first image bytes. The loader expects `data` with shape `[channels, 2**lod, 2**lod]`; some scripts also store `label`.

## Preset path snapshot

These are the dataset-related values exposed by the repository presets and defaults. Paths shown under `/data/datasets` are source assumptions, not recommendations for every host.

| Preset | Train path | Test path | Parts | Samples path | Style path | Output dir |
| --- | --- | --- | --- | --- | --- | --- |
| defaults | `celeba/data_fold_%d_lod_%d.pkl` | empty | train `1`, test `1` | `dataset_samples/faces/realign128x128` | `style_mixing/test_images/set_celeba/` | `results` |
| `configs/celeba.yaml` | `/data/datasets/celeba/tfrecords/celeba-r%02d.tfrecords.%03d` | `/data/datasets/celeba-test/tfrecords/celeba-r%02d.tfrecords.%03d` | train `16`, test default `1` | `dataset_samples/faces/realign128x128` | `style_mixing/test_images/set_celeba` | `training_artifacts/celeba` |
| `configs/celeba-hq256.yaml` | `/data/datasets/celeba-hq/tfrecords/celeba-r%02d.tfrecords.%03d` | `/data/datasets/celeba-hq-test/tfrecords/celeba-r%02d.tfrecords.%03d` | train `16`, test default `1` | `dataset_samples/faces/realign1024x1024` | `style_mixing/test_images/set_ffhq` | `training_artifacts/celeba-hq256` |
| `configs/ffhq.yaml` | `/data/datasets/ffhq-dataset_new/tfrecords/ffhq/splitted/ffhq-r%02d.tfrecords.%03d` | `/data/datasets/ffhq-dataset_new/tfrecords/ffhq-test/splitted/ffhq-r%02d.tfrecords.%03d` | train `16`, test `2` | `dataset_samples/faces/realign1024x1024` | `style_mixing/test_images/set_ffhq` | `training_artifacts/ffhq` |
| `configs/bedroom.yaml` | `/data/datasets/lsun-bedroom-full/splitted/lsun-bedroom-full-r%02d.tfrecords.%03d` | absent | train `4`, test default `1` | `dataset_samples/bedroom256x256` | `style_mixing/test_images/set_bedroom` | `training_artifacts/bedroom` |
| `configs/mnist.yaml` | `/data/datasets/mnist32/tfrecords/mnist-r%02d.tfrecords.%03d` | `/data/datasets/mnist32/tfrecords/mnist_test-r%02d.tfrecords.%03d` | train `1`, test default `1` | default unless overridden | default unless overridden | `mnist_results` |
| `configs/mnist_fc.yaml` | `/data/datasets/mnist_fc/tfrecords/mnist-r%02d.tfrecords.%03d` | `/data/datasets/mnist_fc/tfrecords/mnist_test-r%02d.tfrecords.%03d` | train `1`, test default `1` | default unless overridden | default unless overridden | `mnist_results_fc2z_2` |

## Sample-image directories

Sample images are ordinary image files, not TFRecords. Typical layouts inside a checkout are:

```text
<ALAE repository root>/dataset_samples/faces/realign1024x1024/*.png
<ALAE repository root>/dataset_samples/faces/realign128x128/*.png
<ALAE repository root>/dataset_samples/bedroom256x256/*.png
<ALAE repository root>/dataset_samples/imagenet256x256/*.png
```

Training uses `DATASET.SAMPLES_PATH` for preview/reconstruction samples when it is not `no_path`. Figure scripts use the same key for reconstruction, interpolation, and traversal inputs. Missing sample images do not prevent TFRecord conversion, but they will break sample/reconstruction workflows.

## Style-mixing layout

The style-mixing source uses fixed counts by default:

```text
<ALAE repository root>/style_mixing/test_images/set_ffhq/src/0.png
...
<ALAE repository root>/style_mixing/test_images/set_ffhq/src/4.png
<ALAE repository root>/style_mixing/test_images/set_ffhq/dst/0.png
...
<ALAE repository root>/style_mixing/test_images/set_ffhq/dst/5.png
```

The same `src/` and `dst/` convention applies to `set_celeba` and `set_bedroom`. The script accepts `.png` first and falls back to `.jpg`. Images are resized downward by average pooling when larger than the model resolution; images smaller than the expected resolution fail an assertion.

## Validator usage

Shown relative to this sub-skill directory:

```bash
python scripts/validate_alae_data_layout.py \
  --config-file <ALAE repository root>/configs/ffhq.yaml \
  --repo-root <ALAE repository root> \
  --world-size 8
```

Use `--strict` when missing sample/style/output directories should fail the check. Use `--check-tfrecords` only when TFRecords are expected to already exist; otherwise it will warn about every missing shard.
