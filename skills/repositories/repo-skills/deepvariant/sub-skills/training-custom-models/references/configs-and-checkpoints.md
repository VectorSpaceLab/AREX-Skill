# Configs And Checkpoints

Use this reference with `training-workflows.md` when choosing a DeepVariant r1.10 training config, reviewing dataset metadata, warm-starting, exporting, or preparing `--customized_model` inference.

## Config Names

`train` uses `--config=<config_file.py>:<config_name>`. DeepVariant r1.10 recognizes these DeepVariant-focused training configs:

| Config name | Typical use | Important defaults and cautions |
| --- | --- | --- |
| `base` | Generic starting point or tutorial override base. | Optimizer `rmsprop`, 10 epochs, large default batch size, `tune/f1_weighted`; requires explicit dataset pbtxt paths. |
| `base+test` | Tiny native-test style smoke config. | Batch size 4, 2 epochs, `limit=50`; not a production recipe. |
| `wgs` | Whole-genome short-read training. | Optimizer `sgd`, EMA enabled, 10 epochs, `tune/f1_weighted`, no warm-start checkpoint by default. |
| `exome` | Whole-exome training or fine-tuning. | Optimizer `sgd`, EMA enabled, 20 epochs, `tune/f1_weighted`, expects a warm-start checkpoint path. |
| `pacbio` | PacBio long-read training. | Optimizer `adam`, EMA enabled, 8 epochs, `tune/categorical_accuracy`, expects a warm-start checkpoint path. |
| `ont` | ONT training. | Inherits PacBio-style hyperparameters but leaves `init_checkpoint` empty by default. |
| `hybrid` | Hybrid PacBio + Illumina training. | Optimizer `adam`, EMA enabled, 10 epochs, `tune/categorical_accuracy`, expects a warm-start checkpoint path. |
| `rnaseq` | RNA-seq fine-tuning. | Inherits WGS-style settings with lower learning rate, smaller batch size, 5 epochs, and warm-start checkpoint expectation. |
| `pangenome_wgs` | Pangenome-aware WGS training. | Inherits WGS settings and still requires explicit train/tune dataset pbtxt paths. |

The same source config file also contains DeepSomatic config names. This DeepVariant sub-skill does not make them primary targets; mention them only if the user explicitly asks and then verify scope separately.

## Important Config Fields

| Field | Meaning | Review notes |
| --- | --- | --- |
| `train_dataset_pbtxt` | Dataset config for training examples. | Must point to shuffled labeled examples with `name`, `tfrecord_path`, and positive `num_examples`. |
| `tune_dataset_pbtxt` | Dataset config for tune/validation examples. | Must be separate from held-out test data; ideally separate from train by sample/region/replicate. |
| `init_checkpoint` | Warm-start checkpoint prefix. | Empty means random/ImageNet-style init depending on config fields; non-empty requires shape/channel and assay review. |
| `num_epochs` | Number of epochs. | Tutorial values are not optimized; production use needs planned stopping and validation. |
| `batch_size` | Global batch size. | Defaults are large and accelerator-dependent; smoke/fine-tuning examples often override smaller. |
| `learning_rate` | Initial learning rate. | Fine-tuning often lowers it; record rationale. |
| `num_validation_examples` | Tune examples used per validation pass; `0` means full tune dataset in config comments. | In code, tune steps fall back to the tune dataset count when the division would be zero. |
| `best_checkpoint_metric` | Metric used for best-checkpoint selection. | Common values are `tune/f1_weighted` and `tune/categorical_accuracy`. |
| `use_ema` | Enables EMA checkpoint path and EMA evaluation. | Prefer EMA checkpoint for custom inference when this is enabled and logs support it. |
| `ablation_channels` | Drops named channels during preprocessing. | Training stores the original metadata plus ablation channel ids; review shape/channel implications carefully. |

## Dataset Config Contract

Each dataset pbtxt must parse as a `DeepVariantDatasetConfig` with:

```text
name: "dataset-name"
tfrecord_path: "path/to/shuffled-?????-of-?????.tfrecord.gz"
num_examples: 123456
```

The training data provider raises an error if `name`, `tfrecord_path`, or `num_examples` is missing or zero. `train` uses `num_examples` and `batch_size` to compute steps per epoch and tune steps. The bundled helper can check these scalar fields without importing protobuf or TensorFlow. From this sub-skill directory:

```bash
python scripts/training_config_summary.py validate-dataset train.dataset_config.pbtxt
```

## Example Info Files

DeepVariant uses several metadata filenames that are easy to confuse:

| File | Produced/used by | Meaning |
| --- | --- | --- |
| `*.example_info.json` | `make_examples --mode training` output shards. | Per-example-generation metadata with version, image shape, and channel enum ids. |
| `example_info.json` | Shuffled dataset directories and training checkpoint directories. | Directory-level metadata consumed by the training data loader and copied by training. |
| `model.example_info.json` | Inference wrappers and SavedModel packaging. | Model metadata used with `--customized_model` to configure calling-time example generation. |

`train` first looks for `example_info.json` in the directory containing the training dataset `tfrecord_path`, then for `<first_tfrecord_path>.example_info.json`. If neither exists, it fails before model initialization. Training writes `${EXPERIMENT_DIR}/checkpoints/example_info.json` and copies the same metadata into active checkpoint directories.

A common r1.10 WGS-style metadata shape is:

```json
{"version": "1.10.0", "shape": [100, 221, 7], "channels": [1, 2, 3, 4, 5, 6, 19]}
```

The seven channels correspond to `BASE_CHANNELS,insert_size`. Do not infer compatibility from assay names alone; inspect the metadata and checkpoint contract.

## Warm-Starting And Channel Shape

`keras_modeling.inceptionv3` builds a Keras InceptionV3-based classifier with DeepVariant's class count. When `config.init_checkpoint` is non-empty, the model detects the checkpoint channel count from first-convolution weights. If checkpoint channels and training-example channels differ, DeepVariant can construct an input model with the checkpoint channel count and copy overlapping channel weights into the target model, leaving extra channels initialized.

Review warm-starting with this checklist:

1. Compare train and tune `example_info.json` files for identical shape and channels.
2. Compare the dataset shape/channel count to the checkpoint's `model.example_info.json` or known checkpoint metadata.
3. Confirm the checkpoint is a current DeepVariant Keras InceptionV3 checkpoint; older unsupported formats can raise an error.
4. Decide whether any channel mismatch is intentional and document copied, added, or omitted channels.
5. Avoid mixing WGS, exome, PacBio, ONT, hybrid, RNA-seq, or pangenome checkpoints without assay-specific rationale and held-out validation.

Shape-compatible does not mean biologically or assay-compatible. For example, ONT examples may require a different channel plan and should not silently reuse a WGS checkpoint merely because a loader can copy overlapping weights.

## Checkpoint And SavedModel Outputs

Training stores outputs under `--experiment_dir`:

- `checkpoints/pre_ema/` stores non-EMA checkpoint manager state.
- `checkpoints/ema/` stores EMA checkpoints when `config.use_ema` is true.
- `checkpoints/example_info.json` and checkpoint-local `example_info.json` preserve training metadata.
- At the end, training attempts to save a SavedModel-format model under the active checkpoint path when a latest checkpoint exists.

A checkpoint prefix is not the same as a SavedModel directory. A checkpoint prefix often ends with a name like `checkpoint-8900-0.99915`; a SavedModel directory contains `saved_model.pb` and `variables/`. Ask which artifact a downstream runtime expects before converting or passing a path.

## Convert To SavedModel

Use conversion only in a TensorFlow-compatible runtime:

```bash
convert_to_saved_model \
  --checkpoint="${CHECKPOINT_PREFIX}" \
  --model_example_info_json="${MODEL_EXAMPLE_INFO_JSON}" \
  --output="${SAVEDMODEL_DIR}"
```

The converter reads `model_example_info_json`, initializes model shape from it, loads checkpoint weights with object-match assertions, saves a TensorFlow SavedModel, and copies the metadata to `${SAVEDMODEL_DIR}/model.example_info.json`. If metadata shape does not match checkpoint tensors, conversion can fail or produce an unusable model.

## Use In DeepVariant Inference

A custom-model held-out run typically passes control to `run_deepvariant`:

```bash
run_deepvariant \
  --model_type WGS \
  --customized_model "${CUSTOM_MODEL_PATH}" \
  --customized_model_json "${MODEL_EXAMPLE_INFO_JSON}" \
  --ref "${REF}" \
  --reads "${HELDOUT_READS}" \
  --regions "${HELDOUT_REGIONS}" \
  --output_vcf "${OUT}/custom.vcf.gz" \
  --num_shards "${N_SHARDS}" \
  --disable_small_model
```

If the explicit JSON flag is omitted, the wrapper searches next to the model for `model.example_info.json`. Keep this metadata paired with the model when copying to cloud storage or mounting into containers. If the trained channels match the released model type exactly, an existing released `model.example_info.json` may be usable, but only after confirming the shape/channel list; otherwise use metadata produced from the actual training examples.

## Helper Coverage

`scripts/training_config_summary.py` supports:

- `list-configs` for distilled DeepVariant config names.
- `show-config <name>` for key config defaults and cautions.
- `validate-dataset <pbtxt>` for required dataset config scalar fields.
- `inspect-example-info <json>` for shape/channel names and expected-channel warnings.
- `compare-example-info <left.json> <right.json>` for train/tune/model metadata compatibility checks.

The helper is intentionally static. It cannot validate checkpoint tensors, count TFRecord records, detect biological truth mismatch, or prove that TensorFlow/Keras is installed.
