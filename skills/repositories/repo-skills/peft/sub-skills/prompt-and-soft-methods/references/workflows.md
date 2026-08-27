# Prompt And Soft Method Workflows

## Choose A Method

1. Start with the task wrapper: `TaskType.CAUSAL_LM` for decoder-only language modeling, `TaskType.SEQ_2_SEQ_LM` for encoder-decoder generation, and classification/task-specific wrappers for heads.
2. Choose the prompt representation: direct embeddings (`PromptTuningConfig`), generated embeddings (`PromptEncoderConfig`), KV prefix (`PrefixTuningConfig` or `CartridgeConfig`), multitask factorization (`MultitaskPromptTuningConfig`), CPT (`CPTConfig`), adaption prompt (`AdaptionPromptConfig`), or selected vocabulary rows (`TrainableTokensConfig`).
3. Set virtual-token counts intentionally. More virtual tokens increase prompt capacity and memory; too many can change effective sequence length and slow generation.
4. Use `modules_to_save` for randomly initialized heads that need to train and persist with the adapter.
5. Wrap with `get_peft_model(base_model, config)` and inspect trainable parameters before training.

## Configure SEQ_2_SEQ_LM Prompt Tuning

For T5/BART-like models, prompt tuning and P-tuning prepend virtual embeddings to encoder inputs. A safe pattern is:

```python
from peft import PromptTuningConfig, TaskType, get_peft_model

config = PromptTuningConfig(
    task_type=TaskType.SEQ_2_SEQ_LM,
    num_virtual_tokens=20,
    prompt_tuning_init="TEXT",
    prompt_tuning_init_text="Summarize the input document.",
    tokenizer_name_or_path="t5-small",
)
model = get_peft_model(base_model, config)
```

If using multitask prompt tuning for sequence-to-sequence tasks, set `num_tasks` and pass `task_ids` tensors when calling the PEFT model or `generate`.

## Configure Prefix Or CARTRIDGE Generation

Prefix-style methods inject `past_key_values`, not input embeddings. For decoder-only generation:

```python
from peft import CartridgeConfig, TaskType, get_peft_model

config = CartridgeConfig(
    task_type=TaskType.CAUSAL_LM,
    num_virtual_tokens=8,
    num_frozen_tokens=1,
)
model = get_peft_model(base_model, config)
```

For cartridge initialization from text, first create the PEFT model, then initialize the adapter from a tokenizer prefill:

```python
from peft import initialize_kv_prefix_from_text

initialize_kv_prefix_from_text(
    model,
    tokenizer,
    text="You are a concise domain assistant.",
)
```

Only use KV-cache initialization with `CartridgeConfig` or `PrefixTuningConfig(prefix_projection=False)`. If `prefix_projection=True`, initialize by training rather than copying a KV cache.

## Configure CPT

CPT is causal-LM only. It derives virtual token count from the CPT token list:

```python
from peft import CPTConfig, TaskType

config = CPTConfig(
    task_type=TaskType.CAUSAL_LM,
    cpt_token_ids=[101, 102, 103, 104],
    cpt_mask=[1, 1, 1, 1],
    cpt_tokens_type_mask=[1, 2, 3, 4],
    opt_weighted_loss_type="decay",
    opt_loss_decay_factor=0.95,
)
```

When preparing CPT data, keep `input_ids`, `attention_mask`, and input/type masks aligned. Length mismatches in CPT token fields are config errors; sample mask/type mask mismatches become training-time failures.

## Configure Trainable Tokens

1. Add new tokens to the tokenizer if needed and resize base model embeddings before wrapping with PEFT.
2. Convert token strings to token IDs with the tokenizer.
3. Pass those IDs to `TrainableTokensConfig(token_indices=...)`.
4. Save and load as a PEFT adapter, not by assuming the base embedding matrix changed permanently.

```python
from peft import TrainableTokensConfig, get_peft_model

new_token_ids = tokenizer.convert_tokens_to_ids(["<domain_a>", "<domain_b>"])
config = TrainableTokensConfig(token_indices=new_token_ids)
model = get_peft_model(base_model, config)
```

## Generation Caveats

- Causal-LM prompt learning prepends virtual prompts during prefill, then adjusts generation inputs so only the last input token is used during autoregressive decoding when cache length already includes prompts.
- Prefix tuning and CARTRIDGE inject prompt state through `past_key_values`; they may adjust `cache_position` by `num_virtual_tokens`.
- Sequence-to-sequence generation with prompt tuning requires `input_ids`; PEFT ignores supplied `encoder_outputs` for prompt-tuning generation and recomputes embeddings with virtual prompts.
- For multitask prompt tuning, pass `task_ids` to select task factors during generation.
- Prompt and prefix tokens consume effective context. Adjust max input length or truncation so real tokens plus virtual tokens fit model limits.
