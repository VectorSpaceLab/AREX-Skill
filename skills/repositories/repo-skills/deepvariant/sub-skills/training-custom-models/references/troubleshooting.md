# Training Troubleshooting

Use this matrix for DeepVariant custom-training preflight reviews and failure triage. Treat checks as planning guidance until the user confirms access to their data, official binaries or containers, TensorFlow/Keras runtime, accelerators, and cloud resources.

## Truth VCF, BED, And Reference Problems

| Symptom | Likely cause | Checks and recovery |
| --- | --- | --- |
| `make_examples --mode training` emits few or no labeled examples. | Truth VCF/BED does not overlap requested regions, contig names differ, or confident regions exclude the area. | Compare contig names across FASTA `.fai`, BAM/CRAM header, truth VCF header, BED, and `--regions`; verify reference build and coordinate convention. |
| Truth VCF opens slowly or errors during random access. | VCF is not bgzipped/indexed or index is missing/stale. | Require bgzipped/indexed VCF or compatible BCF; only regenerate indexes after user approval. |
| Labels are poor despite successful example generation. | Truth source is wrong for the sample, assay, or reference; confident regions are too broad/narrow; variants need normalization. | Confirm sample identity, truth release, reference build, normalization, phasing assumptions, and whether preprocessing is needed. |
| CRAM training fails with reference lookup errors. | CRAM cannot find the exact reference expected by the alignment. | Mount the matching FASTA as a local POSIX path and verify CRAM/reference MD5 compatibility before rerunning. |
| `--regions` appears valid but labels disappear. | Region syntax or contig prefix differs from truth/BED/read headers. | Check `chr1` versus `1`, BED coordinate convention, and overlap with confident regions. |

## Channel And Shape Mismatches

| Symptom | Likely cause | Checks and recovery |
| --- | --- | --- |
| Keras/InceptionV3 input shape error. | Example channel count differs from checkpoint/model metadata. | Inspect train/tune `example_info.json`, checkpoint `model.example_info.json`, and `shape[2]`; regenerate examples or choose a compatible checkpoint. |
| Custom inference uses wrong candidate behavior. | Missing or stale `model.example_info.json` means calling-mode `make_examples` did not receive model-specific metadata. | Place matching `model.example_info.json` next to `--customized_model` or pass the explicit custom-model JSON flag. |
| Train and tune metrics are inconsistent or fail early. | Train and tune examples used different `--channel_list` or pileup flags. | Compare example-info files; regenerate one split with identical channel-producing flags. |
| ONT training examples are warm-started from a WGS checkpoint without review. | Shape compatibility is mistaken for assay compatibility. | Require a modeling rationale, document copied/new channels, and evaluate on held-out ONT truth. |
| `ablation_channels` causes unexpected input shape. | Training subtracts ablated channels for model input while preserving original metadata plus ablation channel ids. | Confirm ablation channel names are valid and that downstream inference uses the same intended preprocessing behavior. |

## Missing Example Info JSON

| Symptom | Likely cause | Checks and recovery |
| --- | --- | --- |
| Training fails with `example_info.json not found`. | Shuffler did not copy metadata or dataset layout changed after shuffling. | Put the matching `example_info.json` in the shuffled TFRecord directory or keep `<first_tfrecord_path>.example_info.json` available. |
| Helper reports shape/channel count mismatch. | Metadata edited manually or copied from a different run. | Re-copy metadata from the exact `make_examples --mode training` output or regenerate examples. |
| Custom model is copied without metadata. | Checkpoint/SavedModel moved separately from `model.example_info.json`. | Package checkpoint/SavedModel and metadata together; verify before transferring to cloud or container mounts. |

## Checkpoint And SavedModel Confusion

| Symptom | Likely cause | Checks and recovery |
| --- | --- | --- |
| `--customized_model` path is rejected or metadata cannot be found. | User passed the wrong artifact type or copied files without metadata. | Determine whether the runtime expects a checkpoint prefix or SavedModel directory; keep `model.example_info.json` with the artifact. |
| `convert_to_saved_model` fails to load weights. | Metadata shape does not match checkpoint tensors or checkpoint prefix is wrong. | Pair the checkpoint with metadata from the same training/checkpoint packaging step; verify prefix includes matching index/data files. |
| Best checkpoint selection is unclear. | Multiple EMA/pre-EMA checkpoints and tune metrics exist. | Use training logs, `config.best_checkpoint_metric`, and checkpoint filenames; prefer EMA when `use_ema` is true and logs support it. |
| Warm-start silently changes early training behavior. | Initial evaluation uses `init_checkpoint` or ImageNet-style init and sets a starting best metric. | Review initial tune logs and make checkpoint comparisons against the same split. |

## Runtime, GPU, TPU, And Containers

| Symptom | Likely cause | Checks and recovery |
| --- | --- | --- |
| `train` command is missing. | Lightweight Python package import does not provide production training binaries. | Use official Docker/Bazel/source-built runtime; do not treat minimal package import success as training readiness. |
| TensorFlow/Keras import fails. | Minimal inspection environment lacks the training stack. | Ask for a verified training runtime or container; do not install TensorFlow automatically. |
| GPU is not visible to `train`. | Driver, CUDA, container GPU passthrough, or scheduler setup is wrong. | Ask the user to confirm `--gpus`, driver/toolkit/container compatibility, and accelerator availability before expensive runs. |
| `CUDA_ERROR_NO_DEVICE` appears during `make_examples`. | CPU stage ran in an environment without a visible GPU. | For CPU-only stages this can be harmless; for `train`, verify GPU visibility before proceeding. |
| TPU training fails to connect. | Incorrect `--strategy=tpu`, leader address, permissions, or runtime. | Confirm TPU leader, credentials, and compatible TensorFlow runtime; otherwise use `--strategy=mirrored` for local GPUs. |

## Data Leakage And Evaluation Gaps

| Symptom | Likely cause | Checks and recovery |
| --- | --- | --- |
| High tune metrics but poor held-out benchmark. | Tune/test leakage, overfitting, tiny data, or nonrepresentative truth. | Rebuild non-overlapping train/tune/test split and evaluate final test only after checkpoint selection. |
| Tutorial-sized model is presented as production-grade. | Training used too few samples/regions or only a demonstration chromosome. | Reframe as smoke/fine-tuning; require larger assay-specific training, tune, and held-out benchmarks. |
| Downsampled or augmented reads leak across splits. | Augmented copies placed in different splits from their source reads. | Keep all derived reads/examples with their source sample or region split. |
| Final metrics compare against an incompatible baseline. | Baseline model, regions, filters, truth, or small-model setting differs. | Align evaluation inputs and options, including `--disable_small_model` when assessing the custom CNN. |

## Beam, Dataflow, And Shuffling

| Symptom | Likely cause | Checks and recovery |
| --- | --- | --- |
| Shuffler fails before reading data. | Apache Beam/TensorFlow dependencies are missing or incompatible. | Treat shuffling as a separate optional environment; ask before installing or changing dependencies. |
| Dataflow job stalls or fails. | Project/API/region/staging/temp/credentials/network/quota issue. | Require project id, region, staging/temp buckets, API enablement, credentials, quota, and cost approval before submission. |
| Dataset config has zero or missing `num_examples`. | Input glob did not match files or shuffler could not count output records. | Check input/output patterns, shard names, and generated pbtxt; reject configs without positive examples. |
| Training cannot find shuffled TFRecords. | `tfrecord_path` glob/prefix does not match actual output files. | Expand the pattern in the target storage system and compare to the dataset pbtxt. |
| `example_info.json` disappears after shuffling. | Directory layout changed or the Beam copy step did not find matching metadata. | Copy the matching metadata into the shuffled output directory and verify shape/channels. |

## Quick Preflight Checklist

Before approving a training plan, assert:

- Reference FASTA, reads, truth VCF/BCF, confident BED, and regions use the same reference build and contig names.
- Train/tune/test splits are non-overlapping and leakage-aware.
- `make_examples --mode training` includes truth and confident-region flags.
- Train and tune examples use identical channel-producing flags.
- Shuffled dataset pbtxt files contain `name`, `tfrecord_path`, and positive `num_examples`.
- `example_info.json` files exist in expected directories and match train/tune/model shape requirements.
- Warm-start checkpoint, final checkpoint/SavedModel, and `model.example_info.json` are paired deliberately.
- GPU/TPU/Docker/Bazel/TensorFlow/Keras/Beam/Dataflow work is explicitly approved.
