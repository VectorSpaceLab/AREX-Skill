# Prompt And Soft Method Reference

This reference covers PEFT prompt-learning and prompt-adjacent methods. Install PEFT with `pip install peft`; contributors can use a source editable install. Import public configs from `peft` unless a specialized utility is explicitly noted.

## Shared Prompt-Learning Fields

`PromptTuningConfig`, `PrefixTuningConfig`, `PromptEncoderConfig`, `MultitaskPromptTuningConfig`, `CPTConfig`, and `CartridgeConfig` are prompt-learning configs. Common fields include:

- `task_type`: task wrapper selection, for example `TaskType.CAUSAL_LM` or `TaskType.SEQ_2_SEQ_LM`.
- `num_virtual_tokens`: number of virtual prompt tokens; for CPT this is set from `len(cpt_token_ids)`.
- `token_dim`: model hidden embedding dimension; PEFT can often infer it after model wrapping, but explicit overrides must match the model.
- `num_transformer_submodules`: defaults to `2` for `SEQ_2_SEQ_LM` and `1` otherwise when PEFT sets up prompt encoders.
- `num_attention_heads` and `num_layers`: needed by prefix-style methods to shape key/value prefixes.
- `modules_to_save`: extra full modules to train and save, often classifier heads for classification tasks.

## Prompt Tuning

`PromptTuningConfig` learns virtual-token embeddings directly. Use it when a simple soft prompt is enough and no prompt encoder network or KV-prefix representation is needed.

Important fields:

- `prompt_tuning_init="RANDOM"`: random continuous soft-token initialization.
- `prompt_tuning_init="SAMPLE_VOCAB"`: sample initial vectors from model vocabulary tokens.
- `prompt_tuning_init="TEXT"`: initialize from tokenized text; requires both `prompt_tuning_init_text` and `tokenizer_name_or_path`.
- `tokenizer_kwargs`: only valid with `TEXT` initialization.

For encoder-decoder models, use `task_type=TaskType.SEQ_2_SEQ_LM`; PEFT prepends prompt embeddings to encoder inputs for prompt tuning.

## Prefix Tuning

`PrefixTuningConfig` learns virtual key/value prefixes rather than input embeddings. It is useful when a decoder-only or encoder-decoder model should condition through cached attention prefixes.

Important fields:

- `num_virtual_tokens`: length of the KV prefix.
- `prefix_projection`: when `True`, PEFT uses a projection MLP; set `encoder_hidden_size` for the prompt encoder.
- `init_weights="zero"`: initializes activations as a no-op; otherwise PyTorch random initialization applies.
- `token_dim`, `num_layers`, `num_attention_heads`: must match the target model if manually specified.

PEFT rejects prefix tuning setup when the base model modules report gradient checkpointing, because prefix-style cache injection does not work with gradient checkpointing in this implementation.

## P-Tuning

`PromptEncoderConfig` implements P-tuning with a prompt encoder network. Choose it when you want prompt embeddings reparameterized through an MLP or LSTM.

Important fields:

- `encoder_reparameterization_type`: `"MLP"` or `"LSTM"`.
- `encoder_hidden_size`: hidden size for the prompt encoder.
- `encoder_num_layers`: number of encoder layers.
- `encoder_dropout`: prompt encoder dropout.

P-tuning still consumes `num_virtual_tokens` and task-specific prompt injection behavior from `PromptLearningConfig`.

## Multitask Prompt Tuning

`MultitaskPromptTuningConfig` extends prompt tuning with task factorization. It is intended for multiple related tasks sharing prompt parameters.

Important fields:

- `num_tasks`: number of tasks represented by the multitask prompt.
- `num_ranks`: rank count for task-specific factors.
- `prompt_tuning_init`: supports `TEXT`, `RANDOM`, `AVERAGE_SOURCE_TASKS`, `EXACT_SOURCE_TASK`, and `ONLY_SOURCE_SHARED`.
- `prompt_tuning_init_state_dict_path`: required for source-prompt initialization modes.
- `prompt_tuning_init_task`: source task ID used by `EXACT_SOURCE_TASK`.

Pass `task_ids` during forward or generation when selecting task-specific factors. If omitted, behavior falls back to default task handling rather than explicit per-example task routing.

## CPT

`CPTConfig` implements Context-aware Prompt Tuning and is constrained to `TaskType.CAUSAL_LM`. It raises during config construction for any other `task_type`.

Important fields:

- `cpt_token_ids`: token IDs used for CPT prompts; default is `[0]`.
- `num_virtual_tokens`: automatically set to `len(cpt_token_ids)`.
- `cpt_mask`: mask over CPT tokens; defaults to all ones with the same length as `cpt_token_ids`.
- `cpt_tokens_type_mask`: token type mask; defaults to all ones with the same length.
- `opt_weighted_loss_type`: `"none"` or `"decay"`.
- `opt_loss_decay_factor`, `opt_projection_epsilon`, `opt_projection_format_epsilon`: loss/projection tuning controls.
- `tokenizer_name_or_path`: tokenizer identity used by CPT examples and data preparation.

`cpt_token_ids`, `cpt_mask`, and `cpt_tokens_type_mask` must all have the same length.

## Adaption Prompt

`AdaptionPromptConfig` stores LLaMA-adapter-style prompt settings. It is not a `PromptLearningConfig`, but exposes `is_adaption_prompt=True`.

Important fields:

- `target_modules`: attention submodule name where adaption prompts are inserted. PEFT can fill defaults for supported model types.
- `adapter_len`: number of adapter prompt tokens.
- `adapter_layers`: number of top layers to receive adapters.

Supported model type defaults include `llama`, `mistral`, and `gpt2`. Unsupported model types fail during configuration preparation.

## CARTRIDGE

`CartridgeConfig` is a prefix-style prompt-learning config that stores the KV prefix directly as trainable parameters. It is served similarly to prefix tuning but does not learn the prefix through an MLP projection.

Important fields:

- `num_virtual_tokens`: length of the cartridge prefix.
- `num_frozen_tokens`: number of initial virtual tokens to freeze; default `1` preserves an attention-sink token.
- `task_type`: commonly `TaskType.CAUSAL_LM` for cartridge generation workflows.

Constraints:

- `num_frozen_tokens` must be non-negative.
- If `num_virtual_tokens` is set, `num_frozen_tokens <= num_virtual_tokens`.
- KV-cache initialization utilities require `CARTRIDGE` or non-projected `PREFIX_TUNING` adapters.

Useful utilities importable from `peft` include `initialize_kv_prefix_from_text`, `initialize_kv_prefix_from_past_key_values`, and `compose_cartridge_adapters`.

## Trainable Tokens

`TrainableTokensConfig` marks selected embedding rows trainable. It is useful for new special tokens, domain tokens, or controlled updates to existing token embeddings.

Important fields:

- `token_indices`: list of tokenizer IDs to train.
- `target_modules`: embedding module name, list, or regex. If omitted, PEFT tries `get_input_embeddings()` and then `embed_tokens`.
- `init_weights=True`: initializes trainable rows from current token embeddings, making the adapter initially a no-op.

Trainable tokens can also appear as a LoRA-side option through `trainable_token_indices`; handle save/load carefully because only selected rows should differ from the base embedding matrix.
