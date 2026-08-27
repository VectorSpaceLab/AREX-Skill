---
name: training-custom-models
description: "Plan DeepVariant labeled-example generation, custom training,
  fine-tuning, checkpoint export, and customized-model handoff."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# DeepVariant Training And Custom Models

Use this sub-skill when a user wants to prepare labeled DeepVariant training examples, train or fine-tune a Keras model, choose a `dv_config` config, package checkpoints or SavedModels, or use a trained model through DeepVariant custom-model flags.

Do not use this sub-skill for routine single-sample inference commands; route those to `../germline-calling/SKILL.md`. Route lower-level sharded TFRecord mechanics, non-training `make_examples` questions, and wrapper dry-run decomposition to `../pipeline-stages/SKILL.md`. Treat full Beam/Dataflow/cloud pipelines as reference-only planning unless the user explicitly approves cost, credentials, network, and runtime changes.

## Start Here

1. Confirm that custom training is justified; released DeepVariant models are trained on large, curated datasets and the r1.10 custom-training material is not a production-grade training pipeline.
2. Require labeled examples from `make_examples --mode training` with `--truth_variants`, `--confident_regions`, compatible indexed reads/reference/truth files, and an explicit train/tune/test split.
3. Keep train, tune, and held-out test data separated by sample, replicate, chromosome, or non-overlapping region; never tune on the final benchmark split.
4. Preserve `*.example_info.json` from example generation and the directory-level `example_info.json` after shuffling; these files define shape/channel contracts for training and custom inference.
5. Match `--channel_list`, model input shape, warm-start checkpoint, final checkpoint or SavedModel, and `model.example_info.json` before recommending `--customized_model`.
6. Treat Docker/Bazel binaries, TensorFlow/Keras, GPU/TPU use, Apache Beam/Dataflow, cloud buckets, and long training runs as unsafe without explicit user confirmation.

## Bundled References

- `references/training-workflows.md` covers labeled example generation, split design, shuffling, dataset config files, training/fine-tuning, export, and held-out inference handoff.
- `references/configs-and-checkpoints.md` summarizes DeepVariant `dv_config` names, dataset pbtxt contracts, checkpoint/SavedModel differences, `example_info.json` naming, and `--customized_model` metadata rules.
- `references/troubleshooting.md` maps common training failures to checks and recovery steps for truth data, channel shape, checkpoints, runtimes, leakage, and Beam/Dataflow.

## Safe Helper

Use the bundled helper for dependency-light planning and metadata review:

```bash
python scripts/training_config_summary.py --help
```

Run commands from this sub-skill directory, or adjust the script path to wherever the skill is installed. Useful checks:

```bash
python scripts/training_config_summary.py list-configs
python scripts/training_config_summary.py validate-dataset train.dataset_config.pbtxt
python scripts/training_config_summary.py inspect-example-info example_info.json --expect-wgs-insert-size
python scripts/training_config_summary.py compare-example-info train/example_info.json tune/example_info.json
```

The helper never imports DeepVariant, TensorFlow, Keras, Apache Beam, or genomics IO libraries. It does not read TFRecords, inspect checkpoint tensors, train a model, submit Beam/Dataflow jobs, or validate biological truth quality.

## Decision Rules

- Use `make_examples --mode training` only when the reference FASTA, reads, truth VCF/BCF, confident BED, and selected regions use the same reference build and contig naming.
- Use identical channel-producing flags for train and tune examples; when using WGS-style r1.10 examples, `BASE_CHANNELS,insert_size` usually yields shape `[100, 221, 7]` with channel enum ids `[1, 2, 3, 4, 5, 6, 19]`.
- Start from the closest DeepVariant config such as `base`, `wgs`, `exome`, `pacbio`, `ont`, `hybrid`, `rnaseq`, or `pangenome_wgs`; override dataset pbtxt paths, checkpoint, epochs, batch size, learning rate, and validation settings explicitly.
- Warm-start checkpoints may load across different channel counts by copying overlapping first-convolution weights, but this is a modeling choice that requires explicit review and held-out validation.
- For custom inference, pair the selected checkpoint prefix or SavedModel directory with matching `model.example_info.json` or pass the wrapper's explicit custom-model JSON flag.
- Prefer `--disable_small_model` during held-out custom-model evaluation when the goal is to force all candidates through the trained CNN.

## Safety Notes

The minimal inspected package fact for this skill is DeepVariant version `1.10.0` with lightweight Python import available. The minimal inspection environment did not include TensorFlow/Keras runtime support, so future agents must not treat import success as proof that training, conversion, or inference binaries are runnable. Do not silently install TensorFlow, pull containers, download training data, enable cloud APIs, submit Dataflow jobs, mutate GPU drivers, or start expensive native tests without user approval.
