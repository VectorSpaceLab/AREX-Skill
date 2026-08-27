# Prompt And Soft Method Troubleshooting

## Invalid Task Type

Symptoms:

- Config construction raises an invalid task type error.
- `get_peft_model` returns an unexpected wrapper or generation path.
- CPT raises that it only supports `CAUSAL_LM`.

Fixes:

- Use `TaskType.CAUSAL_LM` for decoder-only language modeling and CPT.
- Use `TaskType.SEQ_2_SEQ_LM` for T5/BART-style encoder-decoder generation.
- Use classification/task wrappers only when the base model has the matching head.
- For CPT, do not attempt `SEQ_2_SEQ_LM`, `SEQ_CLS`, or token-classification variants; choose prompt tuning/P-tuning/prefix tuning instead.

## Virtual Token Count Problems

Symptoms:

- Shape errors in prompt embeddings or `past_key_values`.
- Attention mask length mismatches.
- Cartridge config raises `num_frozen_tokens` errors.

Fixes:

- Set `num_virtual_tokens` explicitly for prompt tuning, prefix tuning, P-tuning, multitask prompt tuning, and CARTRIDGE.
- For CPT, set `cpt_token_ids`; PEFT sets `num_virtual_tokens` to `len(cpt_token_ids)`.
- Keep `cpt_token_ids`, `cpt_mask`, and `cpt_tokens_type_mask` the same length.
- Ensure `CartridgeConfig(num_frozen_tokens)` is between `0` and `num_virtual_tokens`.
- Reduce real input length to account for virtual tokens when model context is tight.

## Prompt Init Text Or Tokenizer Failures

Symptoms:

- `PromptTuningConfig` raises that `tokenizer_name_or_path` is missing.
- `PromptTuningConfig` raises that `prompt_tuning_init_text` is missing.
- `tokenizer_kwargs` raises when prompt init is not `TEXT`.

Fixes:

- With `prompt_tuning_init="TEXT"`, always pass both `prompt_tuning_init_text` and `tokenizer_name_or_path`.
- Use `tokenizer_kwargs` only with `TEXT` initialization.
- If text initialization is not needed, use `RANDOM` or `SAMPLE_VOCAB` and remove text/tokenizer-only kwargs.
- Make sure initialization text tokenizes to a useful prompt; very short or tokenizer-incompatible text weakens initialization.

## Prefix Or CARTRIDGE Cache Errors

Symptoms:

- Prefix tuning setup fails when gradient checkpointing is enabled.
- KV-cache initialization from text or `past_key_values` fails.
- Shape errors mention `num_attention_heads`, `head_dim`, `token_dim`, or layer KV target shape.

Fixes:

- Disable gradient checkpointing for prefix tuning and CARTRIDGE setup.
- Use KV-cache initialization only for CARTRIDGE or prefix tuning without projection.
- Ensure the prefill text produces at least `num_virtual_tokens` cached tokens.
- If manually overriding prefix dimensions, match the model's hidden size, attention head count, and layer count.
- For model families with non-uniform KV shapes, avoid manual dimension guesses unless the architecture requires them.

## Multitask Prompt Routing Issues

Symptoms:

- Multitask prompt tuning behaves like a single-task prompt.
- Source-task initialization fails.
- Task-specific outputs do not change across tasks.

Fixes:

- Set `num_tasks` and `num_ranks` for the intended factorization.
- Pass `task_ids` in forward and generation calls when selecting task-specific prompts.
- For `AVERAGE_SOURCE_TASKS`, `EXACT_SOURCE_TASK`, or `ONLY_SOURCE_SHARED`, provide `prompt_tuning_init_state_dict_path`.
- For `EXACT_SOURCE_TASK`, verify `prompt_tuning_init_task` is within the source task range.

## CPT Non-Causal Rejection

CPT intentionally rejects non-`CAUSAL_LM` task types during `CPTConfig` construction. This is a config-level constraint, not a model-loading problem. If the desired workflow is encoder-decoder or classification, use `PromptTuningConfig`, `PromptEncoderConfig`, `PrefixTuningConfig`, or `TrainableTokensConfig` instead.

## Generation With Prompt Or Prefix Methods

Symptoms:

- `generate` complains that `input_ids` are missing for sequence-to-sequence prompt tuning.
- Passing precomputed `encoder_outputs` is ignored.
- Autoregressive decoding shape changes after the first token.

Fixes:

- For sequence-to-sequence prompt tuning generation, pass `input_ids`; let PEFT build `inputs_embeds` with the virtual prompt.
- Do not rely on caller-supplied `encoder_outputs` with prompt tuning; PEFT recomputes prompt-aware encoder inputs.
- For prefix tuning and CARTRIDGE, treat the prompt as cache state; debug `past_key_values` and `cache_position` rather than input embeddings.
- Pass `task_ids` to multitask prompt generation when task-specific behavior is required.

## Trainable Tokens Save/Load Interactions

Symptoms:

- New token embeddings are lost after reload.
- The whole embedding matrix appears modified or saved unexpectedly.
- Token IDs do not match the intended strings.

Fixes:

- Add tokenizer tokens and resize base embeddings before applying `TrainableTokensConfig`.
- Store adapters with `save_pretrained` and reload with PEFT adapter loading APIs.
- Verify only `token_indices` differ from the base embedding after training and load.
- When combining trainable tokens with another PEFT method, keep the token-index mapping in the method config and test a save/load round trip.
