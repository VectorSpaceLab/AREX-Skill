# training-core workflows

## Purpose

Read this when you need to compose a trainer config, inspect the launcher, or validate a fake-data tutorial without running a long experiment.

## Verified core API facts

These signatures were inspected from the installed package:

- `axlearn.common.config.config_for_function(fn)`
- `axlearn.common.config.config_for_class(cls)`
- `axlearn.common.module.functional(module, prng_key, state, inputs, *, method='forward', is_training, drop_output_collections=('module_outputs',), copy_args_tree=True)`
- `axlearn.common.launch_trainer.get_trainer_config(trainer_config_fn=None, *, flag_values=...)`
- `axlearn.common.trainer.SpmdTrainer.run(prng_key, *, return_evaler_summaries=None)`
- `axlearn.common.input_tf_data.tfds_read_config(*, is_training, num_shards=None, shard_index=None, read_parallelism=1, decode_parallelism=32)`
- `axlearn.common.input_tf_data.tfds_dataset(dataset_name, *, split, is_training, train_shuffle_buffer_size=None, train_shuffle_files=None, data_dir=None, download=False, read_config=None, decoders=None)`
- `axlearn.common.utils.get_data_dir()` and `set_data_dir(data_dir)`

## Core workflows

### 1) Inspect a named trainer config

Use `scripts/inspect_trainer_config.py` when you want to know which config names a module exports and what the resolved `SpmdTrainer` config looks like.

This is the fastest way to validate a new trainer catalog, check mesh settings, or see whether a fake-data branch is wired correctly.

### 2) Launch a small CPU-safe tutorial

The repository's own logistic-regression tutorial is the safest end-to-end probe because it uses synthetic data and a short training path.

Important details:

- Set `DATA_DIR=FAKE` or pass `--data_dir=FAKE` so the input pipeline stays synthetic.
- Use `--jax_backend=cpu` for local inspection.
- Write to a scratch `--trainer_dir` and do not expect a full production-quality checkpoint.

### 3) Validate tokenizer setup

Use the SentencePiece training helper when the task is about tokenizer generation or validation. This workflow is CPU-oriented and can require a lot of memory, so it is not a quick smoke test.

The important public facts are:

- `axlearn.experiments.text.train_spm` reads a TFDS dataset, a SentencePiece JSON config, and a model name.
- It expects the input and output data directory to be configured explicitly.
- It prints encode/decode validation before copying the generated model files.

### 4) Understand input behavior

Common input helpers:

- `fake_grain_source`
- `fake_text_source`
- `fake_speech_source`
- `tfds_read_config`
- `tfds_dataset`

Use fake inputs for CPU-safe smoke checks and TFDS inputs when you are documenting real dataset wiring.

## When to route elsewhere

- GPT-family trainer catalogs and MoE variants belong in `../language-models/`.
- Vision recipes belong in `../vision-workflows/`.
- ASR recipes belong in `../audio-asr/`.
- GCP launch/bundle behavior belongs in `../cli-cloud/`.
