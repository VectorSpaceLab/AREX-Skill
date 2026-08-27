# Training Workflows

This reference distills the DeepVariant r1.10 custom-training path for planning, command review, and troubleshooting. Custom training requires user data plus official DeepVariant binaries or containers, TensorFlow/Keras, compiled genomics dependencies, and usually accelerators. Treat commands as templates until the user confirms paths, runtime, cost, and permissions.

## When Custom Training Fits

Use custom training or fine-tuning only when a released DeepVariant model is not a good fit for the user's sequencing chemistry, sample preparation, organism/reference context, assay target, or evaluation target. First check whether a released `--model_type` is close enough; a custom model can underperform if labels, channels, data split, checkpoint metadata, or evaluation design are wrong.

DeepVariant r1.10 training material is an example workflow, not a production-grade turnkey training pipeline. For production claims, require the user to state the target assay, truth source, held-out benchmark, minimum metrics, cost budget, runtime backend, and rollback plan.

## Inputs To Confirm

| Input | Required checks |
| --- | --- |
| Reference FASTA | Same build and contig names as reads, truth, BED, and `--regions`; `.fai` available; local POSIX path when CRAM reference lookup is needed. |
| Training reads | Sorted BAM/CRAM with index; sample identity and replicate roles understood; aligned to the same reference as truth. |
| Truth variants | Indexed bgzipped VCF/BCF; high-confidence truth for the sample and reference; normalization/phasing assumptions understood. |
| Confident regions | BED regions where labels are trusted; same reference build and contig naming as reads and truth. |
| Split plan | Train/tune/test separated by sample, replicate, chromosome, or non-overlapping region. |
| Channels | `--channel_list` and channel-changing flags chosen deliberately and held constant across train/tune. |
| Runtime | Docker or Bazel `make_examples` and `train`, TensorFlow/Keras, optional GPU/TPU strategy, storage, and optional Beam/Dataflow permissions. |

Never train from unlabeled calling-mode examples. `make_examples --mode training` writes `tf.train.Example` records that include labels derived from `--truth_variants` and `--confident_regions`.

## Split Strategy

Keep three roles separate:

- Training set: examples used to update weights.
- Tune/validation set: examples used during training for metrics, early stopping, and best-checkpoint selection.
- Test set: held-out reads or regions never used for training or tuning, reserved for final calling and benchmarking.

Acceptable splits include non-overlapping chromosomes, non-overlapping genomic intervals, separate replicates, or separate samples. Reject plans that reuse a final benchmark region for tuning. If reads are downsampled or augmented, keep augmented copies in the same split as their source data.

The r1.10 BGISEQ case study demonstrates mechanics by using chr1 for training, chr21 for tune/validation, and chr20 for final testing, while noting that real training normally needs much more data. Released DeepVariant r1.10 model training used tens of millions to billions of examples depending on assay, so tutorial-scale runs are smoke or fine-tuning experiments, not proof of production accuracy.

## Generate Labeled Examples

A training-example command usually has this shape:

```bash
seq 0 "$((N_SHARDS - 1))" | parallel --halt 2 --line-buffer \
  docker run \
    -v "${WORKDIR}:${WORKDIR}" \
    "${DEEPVARIANT_IMAGE}" \
    make_examples \
      --mode training \
      --ref "${REF}" \
      --reads "${TRAIN_BAM}" \
      --examples "${OUT}/train.with_label.tfrecord@${N_SHARDS}.gz" \
      --truth_variants "${TRUTH_VCF}" \
      --confident_regions "${CONFIDENT_BED}" \
      --regions "${TRAIN_REGIONS}" \
      --channel_list "BASE_CHANNELS,insert_size" \
      --task {}
```

Repeat with non-overlapping reads or regions for tune examples. Use the same channel-producing flags in train and tune. `BASE_CHANNELS` means the six core channels `read_base`, `base_quality`, `mapping_quality`, `strand`, `read_supports_variant`, and `base_differs_from_ref`; adding `insert_size` commonly yields r1.10 WGS-style shape `[100, 221, 7]` with channel ids `[1, 2, 3, 4, 5, 6, 19]`.

After each run, preserve the generated `*.example_info.json`. For sharded output, it is written beside a shard and records version, image shape, and channel enum ids. Training and custom inference both depend on this metadata.

## Shuffle Examples And Build Dataset Configs

DeepVariant training expects globally shuffled examples. The repo shuffler is Apache Beam-based and can run locally with `DirectRunner` or remotely with `DataflowRunner`; both are reference-only until the user approves dependencies, storage, credentials, network, and cost.

A dataset config pbtxt should contain:

```text
name: "HG001-train"
tfrecord_path: "gs://bucket/path/train.with_label.shuffled-?????-of-?????.tfrecord.gz"
num_examples: 342038
```

`name`, `tfrecord_path`, and positive `num_examples` are required by the training data provider. The data loader first looks for `example_info.json` in the directory containing `tfrecord_path`; if not found, training tries `<first_tfrecord_path>.example_info.json` and then fails if neither exists. The Beam shuffler copies the input example-info JSON into the shuffled output directory when it can find a matching input metadata file.

For local shuffling, ask the user to confirm disk and memory. For Dataflow, require project id, region, staging/temp locations, API enablement, credentials, network rules, and cost approval.

## Train Or Fine-Tune

`train` reads an `ml_collections` config from syntax like `--config=dv_config.py:base` and accepts overrides as `--config.<field>=<value>`. A typical fine-tuning command shape is:

```bash
docker run --gpus 1 \
  -v "${WORKDIR}:${WORKDIR}" \
  -w "${WORKDIR}" \
  "${DEEPVARIANT_GPU_IMAGE}" \
  train \
    --config=dv_config.py:base \
    --config.train_dataset_pbtxt="${TRAIN_DATASET_PBTXT}" \
    --config.tune_dataset_pbtxt="${TUNE_DATASET_PBTXT}" \
    --config.init_checkpoint="${WARMSTART_CHECKPOINT}" \
    --config.num_epochs=10 \
    --config.learning_rate=0.0001 \
    --config.num_validation_examples=0 \
    --config.batch_size=384 \
    --experiment_dir="${EXPERIMENT_DIR}" \
    --strategy=mirrored
```

`--strategy=mirrored` uses TensorFlow mirrored strategy for local GPUs. `--strategy=tpu` requires TPU leader setup. Training logs report training examples, tune examples, batch size, epochs, steps per epoch, tune steps, total train steps, and steps per iter.

Training copies the training example metadata into `${EXPERIMENT_DIR}/checkpoints/example_info.json` and checkpoint subdirectories. When EMA is enabled, checkpoints are saved under `checkpoints/ema/`; otherwise the active path is `checkpoints/pre_ema/`. The selected best metric comes from `config.best_checkpoint_metric`, commonly `tune/f1_weighted` for WGS/exome/RNA-style configs and `tune/categorical_accuracy` for PacBio/ONT/hybrid-style configs.

Do not assume the newest file is best unless logs and checkpoint naming show the metric choice. Use tune metrics only for model selection; final model quality requires held-out inference and benchmarking.

## Export Or Package A Model

A checkpoint prefix and a SavedModel directory are different artifacts:

- A checkpoint prefix looks like `.../checkpoints/ema/checkpoint-8900-0.99915` and is paired with TensorFlow checkpoint files.
- A SavedModel directory contains `saved_model.pb` and variables.
- Inference wrappers expect matching model metadata, normally named `model.example_info.json`, next to the custom model unless an explicit custom-model JSON flag is provided.

Use `convert_to_saved_model` only in a TensorFlow-compatible runtime when a downstream runtime expects SavedModel format:

```bash
convert_to_saved_model \
  --checkpoint="${CHECKPOINT_PREFIX}" \
  --model_example_info_json="${MODEL_EXAMPLE_INFO_JSON}" \
  --output="${SAVEDMODEL_DIR}"
```

The converter initializes model shape from the metadata, loads checkpoint weights, saves the SavedModel, and copies metadata to `${SAVEDMODEL_DIR}/model.example_info.json`.

## Held-Out Inference Handoff

Complete inference command construction belongs to `../germline-calling/SKILL.md`, but training review must enforce the custom-model checks:

- Use `--customized_model` pointing at the selected checkpoint prefix or SavedModel directory.
- Provide matching `model.example_info.json` next to the model or pass `--customized_model_json` when supported by the wrapper.
- Use a compatible `--model_type` so calling-time `make_examples` receives the expected channel/model flags.
- Consider `--disable_small_model` so every candidate is evaluated by the custom CNN during model assessment.
- Benchmark only on held-out samples or intervals with compatible truth and confident regions.

Do not report training success from tune metrics alone. Require held-out VCF/gVCF validation and, where truth is available, benchmark metrics such as SNP/indel precision, recall, and F1.

## Source Scripts And Limitations

The repository's Beam shuffler and truth preprocessing utilities are not bundled as runtime scripts in this skill because they require Apache Beam, TensorFlow, genomics IO libraries, user data, and sometimes cloud side effects. This skill instead bundles `scripts/training_config_summary.py` for safe metadata planning. If a user needs actual shuffling or truth preprocessing, request explicit approval and a verified runtime rather than treating this repo skill as an execution environment.
