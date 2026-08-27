# language-models overview

## Purpose

Read this when you need to inspect or explain AXLearn's GPT-family trainer catalogs, tokenizer helpers, and MoE/flash-attention model variants.

## Verified API and catalog facts

The installed package exposes these key pieces:

- `axlearn.experiments.text.gpt.common.model_config(...)`
- `axlearn.experiments.text.gpt.common.tfds_input(...)`
- `axlearn.experiments.text.gpt.common.mixture_train_input_source(...)`
- `axlearn.experiments.text.gpt.common.evaler_config_dict(...)`
- `axlearn.experiments.text.gpt.common.make_config_name(...)`
- `axlearn.experiments.text.gpt.common.get_trainer_config_fn(...)`
- `axlearn.experiments.text.gpt.common.mesh_shape_from_axes(...)`
- `axlearn.experiments.text.gpt.common.scaled_hidden_dim(...)`
- `axlearn.experiments.text.gpt.fuji.trainer_configs(...)`
- `axlearn.experiments.text.gpt.gala.trainer_configs(...)`
- `axlearn.experiments.text.gpt.honeycrisp.trainer_configs(...)`
- `axlearn.experiments.text.gpt.gspmd.trainer_configs(...)`
- `axlearn.experiments.text.gpt.qwen.trainer_configs(...)`
- `axlearn.experiments.text.gpt.vocabulary_fuji_v3.FujiV3Vocabulary`

## Model families

### Fuji

Fuji is the main family for LLaMA-like decoder-only configs. It provides versioned model sizes and tokenizer choices, including a v3 tokenizer path that can use a local `Llama-3-tokenizer.json` file when `DATA_DIR=FAKE`.

### Gala and Honeycrisp

These families provide alternative norm and position-encoding choices, including ALiBi and different normalization structures.

### GSPMD

The GSPMD helpers demonstrate pipelined/streaming schedule variants and are useful when discussing mesh layout rather than just architecture.

### Qwen

Qwen helpers show a large-context MoE-style catalog and are useful when the task names Qwen3-specific vocab, head-dim, or mesh rules.

### Deterministic and Pajama variants

These catalogs wrap the same underlying model builders with specific datasets and deterministic or dataset-specific overrides.

## Common workflow patterns

### Inspect a config catalog

A GPT catalog module typically exposes `named_trainer_configs() -> dict[str, TrainerConfigFn]`. Use the bundled script to list those names and print a summary for one selection.

### Understand tokenization

Tokenizer files may come from either:

- The configured `DATA_DIR`, or
- Packaged repository data when `DATA_DIR=FAKE`.

The Fuji v3 vocabulary helper wraps a Hugging Face tokenizer JSON and exposes encode/decode methods used by the text input pipeline.

### Understand mesh / sequence choices

Common dimensions and knobs include:

- `MESH_AXIS_NAMES` for the standard pipeline/data/expert/fsdp/seq/model ordering.
- `flash_attention_config()` for flash-attention sharding.
- `scaled_hidden_dim()` for FFN dimension scaling.
- `get_trainer_config_fn()` for the common trainer wrapper.

## Practical guidance

- Prefer `c4_trainer` when you want the full text-model catalog entry point.
- Prefer the family module (`fuji`, `gala`, `honeycrisp`, `qwen`, or `gspmd`) when you want to inspect family-specific config builders.
- Treat tokenizer-file and MoE-import failures as dependency or path issues first, not as proof that the whole family is broken.
- Use `training-core` if the question is only about trainer mechanics, fake data, or launch flags.
