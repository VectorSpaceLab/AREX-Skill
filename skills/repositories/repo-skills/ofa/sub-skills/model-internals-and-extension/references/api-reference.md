# API Reference

## Core shared task surface

### `tasks.ofa_task.OFAConfig`

Important fields verified from source:

- `data`
- `selected_cols`
- `bpe`
- `bpe_dir`
- `max_source_positions`
- `max_target_positions`
- `max_src_length`
- `max_tgt_length`
- `code_dict_size`
- `patch_image_size`
- `orig_patch_image_size`
- `num_bins`
- `imagenet_default_mean_and_std`
- `constraint_range`

### `tasks.ofa_task.OFATask`

Shared responsibilities:

- loads the BPE dictionary from `bpe_dir`,
- adds `<mask>`, `<code_*>`, and `<bin_*>` tokens,
- builds the model and generator using the Fairseq-style API,
- provides a batch iterator for dataset-backed tasks.

### `models.ofa.ofa.OFAModel`

- Registered as `ofa`.
- Inherits the shared transformer model.
- Adds classification-head support and architecture-specific arguments.
- Exposes `register_classification_head` and `register_embedding_tokens` helpers.

### `models.ofa.ofa.OFAClassificationHead`

- Used for sentence-level classification.
- Supports `mlp` or `linear` pooler classifiers.
- Can optionally use spectral normalization.

## Architecture names

Verified architecture registrations include:

- `ofa_large`
- `ofa_base`
- `ofa_huge`
- `ofa_medium`
- `ofa_tiny`

## Criterion names relevant to extension work

- `adjust_label_smoothed_cross_entropy`
- `adjust_label_smoothed_encouraging_loss`
- `scst_reward_criterion`
- `clip_scst_reward_criterion`
- `speech_pretrain_loss`

## Registration entry point

`ofa_module/__init__.py` imports `data`, `models`, `tasks`, `criterions`, and `utils` so their decorators run.

## Safe inspection helper

Run `scripts/inspect_ofa_registration.py` to print the currently registered tasks, models, architectures, and criteria without launching training.
