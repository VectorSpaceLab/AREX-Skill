# Configuration reference

H2O LLM Studio experiment configs are nested Python dataclasses serialized as YAML. The YAML `problem_type` key selects the problem-specific config tree, `load_config_yaml()` builds a `ConfigProblemBase` instance, and `save_config_yaml()` writes the normalized nested mapping back to YAML.

## Problem type values

Use these exact YAML values:

| YAML `problem_type` | Config module selected by the loader | Primary dataset shape |
|---|---|---|
| `text_causal_language_modeling` | `text_causal_language_modeling_config` | prompt / answer text, optional system text, optional conversation chains |
| `text_causal_classification_modeling` | `text_causal_classification_modeling_config` | prompt text plus one or more integer label columns |
| `text_causal_regression_modeling` | `text_causal_regression_modeling_config` | prompt text plus one or more float target columns |
| `text_sequence_to_sequence_modeling` | `text_sequence_to_sequence_modeling_config` | source prompt text and target answer text |
| `text_dpo_modeling` | `text_dpo_modeling_config` | prompt text plus chosen and rejected answer columns |

The config object's `problem_type` property is derived from the loaded module name. A YAML tagged with the wrong `problem_type` loads the wrong dataclass tree, so pass `--expect-problem-type` to `scripts/inspect_config.py` when the intended task is known.

## Top-level YAML layout

Every normalized config contains these top-level keys:

| Key | Meaning |
|---|---|
| `experiment_name` | Name used for the run and saved experiment directory. |
| `output_directory` | Destination directory for experiment outputs. |
| `llm_backbone` | Hugging Face model id or custom backbone path/name. |
| `dataset` | Dataframe paths, column names, text formatting, sampling, and validation split settings. |
| `tokenizer` | Sequence length, tokenizer keyword JSON, prompt/answer token behavior, and padding quantile. |
| `architecture` | Backbone dtype, pretrained-weight flags, gradient checkpointing, dropout, and optional weights. |
| `training` | Loss, optimizer, learning rate, batch size, epochs, LoRA/DoRA/RSLoRA, checkpoint, and validation cadence settings. |
| `augmentation` | Token masking, parent skipping/replacement probabilities, and NEFTune noise. |
| `prediction` | Evaluation metric, generation parameters, and inference batch sizing. |
| `environment` | GPU selection, mixed precision, DeepSpeed flags/buckets, worker count, seed, and Hugging Face branch/trust settings. |
| `logging` | Logger choice, W&B fields, log-step mode, and rank logging. |
| `problem_type` | Loader selector. Must be one of the exact values listed above. |

## Dataset section essentials

Common generation-style fields include:

- `train_dataframe`: local CSV / Parquet path used for training.
- `validation_strategy`: `automatic` or `custom`.
- `validation_dataframe`: required when `validation_strategy` is `custom`.
- `validation_size`: automatic holdout fraction.
- `data_sample` and `data_sample_choice`: optional sampling percentage and affected splits.
- `system_column`: optional system text column.
- `prompt_column`: one column or a list of columns; multiple prompt columns are joined with `prompt_column_separator`.
- `answer_column`: expected output column for generation; one or more label/target columns for classification and regression.
- `parent_id_column` and `id_column`: optional conversation chaining keys for generation-style tasks.
- `text_system_start`, `text_prompt_start`, and `text_answer_separator`: optional text tokens decoded with Python unicode-escape semantics.
- `add_eos_token_to_system`, `add_eos_token_to_prompt`, and `add_eos_token_to_answer`: append EOS tokens to the corresponding pieces.
- `limit_chained_samples`, `mask_prompt_labels`, and `only_last_answer`: causal-LM chain and label-mask controls.
- `personalize`, `chatbot_name`, and `chatbot_author`: optional replacements for Open Assistant / LAION-style strings in causal-LM data.

Classification and regression override the generation defaults: `parent_id_column` is not supported, `system_column` is hidden/disabled by default, and `answer_column` is expected to be a list of target columns.

DPO extends the causal-LM dataset with `rejected_prompt_column` and `rejected_answer_column`; the rejected prompt may be `None` to reuse the chosen prompt.

## Section notes

- `tokenizer.tokenizer_kwargs` is a JSON string. The default is equivalent to `{"use_fast": true, "add_prefix_space": false}`.
- `tokenizer.max_length` caps the total encoded sample length; causal-LM samples are truncated from the left for prompt context and from the right for answer-only encodings.
- `prediction.batch_size_inference: 0` means inference uses the training batch size.
- `environment.gpus` contains string GPU indices. Configs copied from another machine can select unavailable GPUs.
- Default causal-LM backbones and default sequence-to-sequence backbones can be overridden by environment variables before the app/config layer initializes.
- GPT metric template choices are discovered from local prompt-template files at config-construction time, so load configs from a project/runtime root that contains those prompt assets.

## Problem-specific validation checks

`check_config_for_errors()` combines common checks with the problem-specific `cfg.check()` method. Useful checks include:

| Scope | Checks |
|---|---|
| Common | At least one GPU selected; selected GPU count does not exceed available CUDA devices; minimum disk space; int4/int8 quantization requires pretrained weights; pure int4/int8 training without LoRA is warned; DeepSpeed is incompatible with int4/int8 and single-GPU selection; W&B relative step logging is rejected. |
| Causal language modeling | Dataset sanity check; temperature and `do_sample` consistency warnings. |
| Causal classification | Deprecated string `answer_column` is converted to a list; multilabel answer count must match `num_classes`; `CrossEntropyLoss` requires a single multiclass label with `num_classes > 1`; `BinaryCrossEntropyLoss` requires `num_classes == 1`; parent IDs are rejected. |
| Causal regression | Deprecated string `answer_column` is converted to a list; parent IDs are rejected. |
| Sequence-to-sequence | Same temperature / `do_sample` consistency warning as generation configs. |
| DPO | Dataset class requires `limit_chained_samples` and the rejected answer column. |

## Round-trip rules

- Saving converts dataclass sections into plain nested dictionaries.
- Tuples are serialized as YAML lists. Some constructors convert prompt columns back to tuples after loading.
- Unknown YAML keys are ignored by the dataclass loader with a warning, so treat unknown-key reports as real schema drift until proven otherwise.
- A safe round-trip is: YAML -> `load_config_yaml()` -> `convert_cfg_base_to_nested_dictionary()` -> `save_config_yaml()` -> reload -> same normalized dictionary.
- Use `scripts/inspect_config.py --config CONFIG.yaml --write-roundtrip normalized.yaml` to produce a canonical YAML copy without launching training.
