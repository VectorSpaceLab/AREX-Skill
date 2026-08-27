---
name: prompt-and-soft-methods
description: "Configure and troubleshoot PEFT prompt-learning and soft-token
  methods: prompt tuning, prefix tuning, P-tuning, multitask prompt tuning, CPT,
  adaption prompt, CARTRIDGE, and trainable tokens."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# PEFT Prompt And Soft Methods

Use this sub-skill when the task is about PEFT methods that add trainable virtual tokens, prompt encoders, KV-prefix parameters, adaption prompts, or selected trainable vocabulary rows. It focuses on choosing and constructing configs, handling prompt initialization, task and virtual-token settings, and prompt-specific generation caveats.

For generic `PeftModel` lifecycle, adapter activation, mixed adapters, or `get_peft_model` mechanics, use the root PEFT skill and the `adapter-core` sub-skill. For `save_pretrained`, `from_pretrained`, merge behavior, and checkpoint formats, use `save-load-merge`. For training launchers, `Trainer`, Accelerate, DeepSpeed, or distributed jobs, use `training-and-integrations`.

## Method Routing

- Use `PromptTuningConfig` for directly learned virtual-token embeddings prepended to model embeddings; choose `RANDOM`, `SAMPLE_VOCAB`, or `TEXT` initialization.
- Use `PrefixTuningConfig` for learned key/value prefixes injected as `past_key_values`; it is prefix-style and incompatible with gradient checkpointing in PEFT setup.
- Use `PromptEncoderConfig` for P-tuning, where an MLP or LSTM encoder reparameterizes virtual prompt tokens.
- Use `MultitaskPromptTuningConfig` when one prompt table is factorized across multiple task IDs or initialized from a source multitask prompt state dict.
- Use `CPTConfig` for Context-aware Prompt Tuning on causal LM only; its `num_virtual_tokens` is derived from `cpt_token_ids`.
- Use `AdaptionPromptConfig` for LLaMA-adapter-style attention prompts on supported model types (`llama`, `mistral`, `gpt2`).
- Use `CartridgeConfig` for KV-cache-parameterized prefix adapters that can be initialized from a text prefill or existing `past_key_values`.
- Use `TrainableTokensConfig` for making specific vocabulary embedding rows trainable without training the full embedding matrix.

## Minimal Config Patterns

```python
from peft import PromptTuningConfig, TaskType

config = PromptTuningConfig(
    task_type=TaskType.SEQ_2_SEQ_LM,
    num_virtual_tokens=20,
    prompt_tuning_init="TEXT",
    prompt_tuning_init_text="Classify the sentiment of the input.",
    tokenizer_name_or_path="t5-small",
)
```

```python
from peft import PrefixTuningConfig, TaskType

config = PrefixTuningConfig(
    task_type=TaskType.CAUSAL_LM,
    num_virtual_tokens=16,
    prefix_projection=True,
    encoder_hidden_size=512,
)
```

```python
from peft import CPTConfig, TaskType

config = CPTConfig(
    task_type=TaskType.CAUSAL_LM,
    cpt_token_ids=[0, 1, 2, 3],
    cpt_mask=[1, 1, 1, 1],
    cpt_tokens_type_mask=[1, 2, 3, 4],
    opt_weighted_loss_type="decay",
)
```

## Required Checks

Before wrapping the base model with `get_peft_model`, verify these points:

- `task_type` matches the base model head and use case, such as `CAUSAL_LM`, `SEQ_2_SEQ_LM`, `SEQ_CLS`, `TOKEN_CLS`, or `QUESTION_ANS`.
- Prompt-learning methods have a positive `num_virtual_tokens`, except CPT where PEFT derives it from `len(cpt_token_ids)`.
- `PromptTuningConfig(prompt_tuning_init="TEXT")` includes both `prompt_tuning_init_text` and `tokenizer_name_or_path`.
- Prefix-style methods (`PrefixTuningConfig`, `CartridgeConfig`) have compatible `token_dim`, `num_layers`, and `num_attention_heads` when manually overriding inferred values.
- `MultitaskPromptTuningConfig` receives `task_ids` in forward/generation calls when task-specific factors are intended.
- `TrainableTokensConfig.token_indices` are real tokenizer IDs and the target embedding module is the one used by the model forward path.

Run `scripts/prompt_config_sanity.py` to validate config construction and surface method-specific constraints without loading a model.

## Cross-Links

- See `references/methods.md` for method distinctions, config fields, and constraints.
- See `references/workflows.md` for choosing settings and integrating with `get_peft_model` and generation.
- See `references/troubleshooting.md` for common failure modes involving task types, initialization, CPT, generation, and trainable tokens.
