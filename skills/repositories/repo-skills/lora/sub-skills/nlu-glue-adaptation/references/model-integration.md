# NLU model integration

## RoBERTa

When `config.apply_lora` is true, the repository's RoBERTa self-attention
constructs:

- `query = lora.Linear(hidden_size, all_head_size, r=config.lora_r,
  lora_alpha=config.lora_alpha)`;
- `key = nn.Linear(...)` unchanged; and
- `value = lora.Linear(hidden_size, all_head_size, r=config.lora_r,
  lora_alpha=config.lora_alpha)`.

This is a query/value-only adaptation. The classifier, embeddings, key
projection, and other encoder blocks remain ordinary modules unless separately
changed by the user.

## DeBERTa-v2

When `config.apply_lora` is true, disentangled self-attention constructs
`query_proj` and `value_proj` as `lora.Linear` with the configured rank and
alpha, while `key_proj` remains ordinary. The example sets
`merge_weights=False` for these projections so the forward path stays
explicitly unmerged during the Transformers model lifecycle.

The configuration carries `apply_lora`, `lora_r`, and `lora_alpha`. Keep those
fields present when saving/reloading the config; a model created without the
LoRA flag will not have the adapter parameter names expected by the checkpoint.

## Porting checklist

1. Confirm the host model's attention projection names and weight layout.
2. Replace only the intended query/value modules; preserve key, output, and
   classifier shapes.
3. Pass rank and alpha through the model configuration or constructor instead
   of hard-coding them in the forward method.
4. Initialize the base model, then inspect `named_parameters()` for the expected
   `lora_A`/`lora_B` paths.
5. Freeze the base model and verify a tiny forward/backward pass before loading
   a trained adapter.
6. Load the adapter state with `strict=False`, but investigate any unexpected
   LoRA keys or missing adapter keys.

## What not to copy blindly

The NLU directory contains a broad historical Transformers fork, including
unrelated upstream models and tests. Port only the LoRA-specific configuration,
attention replacement, runner flags, and checkpoint behavior needed by the
current model version. Modern Transformers/PEFT may use different config names,
loader APIs, and distributed launchers.
