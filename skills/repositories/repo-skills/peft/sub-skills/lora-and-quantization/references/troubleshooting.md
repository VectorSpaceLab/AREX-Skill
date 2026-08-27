# LoRA and Quantization Troubleshooting

## Target module problems

### PEFT cannot infer targets

Symptom: configuration or wrapping fails with a message asking to specify `target_modules` or `target_parameters`.

Fix:

- Use `target_modules="all-linear"` for QLoRA-style transformer tuning.
- Use explicit suffixes when only attention or MLP projections should be adapted, for example `['q_proj', 'v_proj']` or `['query', 'value']`.
- Use a regex string for architecture-specific naming patterns.
- Use `target_parameters=[...]` with `target_modules=[]` for raw expert parameters that are not `nn.Linear` modules.

### Too many or wrong layers are adapted

Fix:

- Add `exclude_modules` to remove output heads or unstable modules from a broad target.
- Print trainable parameters after wrapping and compare trainable counts with expectations.
- Prefer suffix names over short names that may match unrelated modules.

## Rank, alpha, and dropout issues

- Underfitting: raise `r`, raise `lora_alpha`, target more modules, or use `target_modules="all-linear"`.
- Instability after raising rank: try `use_rslora=True` so scaling is `alpha / sqrt(r)`.
- Overfitting or small data: add nonzero `lora_dropout` or reduce rank.
- Adapter-disabled output differs from base: check whether `bias` was `"all"` or `"lora_only"`.

## Initialization warnings and errors

### `loftq_config` ignored

`loftq_config` only applies when `init_lora_weights="loftq"`. If using an already quantized model, remove `loftq_config` and use ordinary LoRA plus `replace_lora_weights_loftq`.

### LoftQ requires `scipy`

Full LoftQ initialization checks for `scipy`. Install it or choose ordinary LoRA/QLoRA. The model-free sanity script can detect this before model loading.

### Full LoftQ used with an already quantized model

Do not pass a quantized base model to `LoraConfig(init_lora_weights="loftq", loftq_config=...)`. Full LoftQ quantizes the backbone itself. For an already loaded bitsandbytes 4-bit model, wrap with normal LoRA and call `replace_lora_weights_loftq(peft_model)`.

### PiSSA/CorDA/OLoRA/LoRA-GA conversion later fails

These initializers can modify base weights or require conversion state. Avoid combining `use_rslora=True`, `rank_pattern`/`alpha_pattern`, and post-training conversion that restores initial base values. Route save-time conversion mechanics to `save-load-merge`.

### `lora_bias=True` fails

`lora_bias=True` only supports `init_lora_weights=True` or `False`, and is incompatible with DoRA.

## Variant-specific issues

### DoRA is slow

DoRA adds a magnitude branch and has more overhead than standard LoRA. Use it when quality at low rank matters; merge for inference when the save/load workflow and quantization backend support it. Avoid DoRA with Megatron LoRA config.

### QDoRA with distributed training is unstable

QDoRA can work with bitsandbytes, but DeepSpeed ZeRO-2 has reported issues. Route launcher and distributed optimizer choices to `training-and-integrations`.

### QALoRA shape error

QALoRA requires targeted linear layer input dimensions to be divisible by `qalora_group_size`. Pick a smaller divisor, use the architecture hidden-size factors, or target only compatible modules. QALoRA is currently implemented for GPTQ.

### aLoRA does not activate

- Ensure `task_type="CAUSAL_LM"`.
- Ensure `alora_invocation_tokens` is the exact tokenized invocation sequence.
- Ensure every input string contains the invocation sequence.
- Do not expect merge support; aLoRA applies selectively based on token position.

### Trainable tokens do not train or save unexpectedly large files

- Add tokens to the tokenizer and resize model embeddings before applying PEFT.
- Pass token ids, not strings, to `trainable_token_indices`.
- For FSDP, use `use_orig_params=True`.
- If only trainable token deltas should be saved after resizing embeddings, consider `save_embedding_layers=False` when saving.

## Quantization backend issues

### Missing optional dependency

Map the checkpoint/backend to the package:

- bitsandbytes 4-bit/8-bit: `bitsandbytes`
- GPTQ: `gptqmodel` for PEFT's current GPTQ post-training path through Transformers/GPT-QModel
- AQLM: `aqlm`
- HQQ: `hqq`
- torchao: `torchao`
- INC: `neural-compressor[pt]`

Fallbacks:

- Use full/half precision with standard LoRA if memory allows.
- Choose bitsandbytes QLoRA if the hardware and package are available.
- Choose a prequantized checkpoint matching an installed backend.
- Avoid merge-dependent workflows on AQLM or INC quantized weights.

### `replace_lora_weights_loftq` fails

Check that:

- The PEFT model wraps a bitsandbytes 4-bit base model.
- The original/reference model weights are available as safetensors.
- The adapter was initialized as ordinary LoRA, not full LoftQ.
- The targeted modules are broad enough, ideally `target_modules="all-linear"`.

### Merge/unmerge unsupported or wrong after quantization

Quantization backends differ. AQLM adapters should be saved separately. INC does not support `merge()`/`unmerge()`. torchao merge correctness is limited to LoRA with int8 weight-only. Route detailed merge/save remediation to `save-load-merge`.

### Dtype warnings or slow training

- Align compute dtype with hardware: bfloat16 on supported accelerators, otherwise float16 or backend defaults.
- For bitsandbytes 4-bit, set `bnb_4bit_compute_dtype` intentionally.
- If warning says input dtype differs from compute dtype, expect slower training and adjust model load or quantization config.

## Quick preflight

Run:

```bash
python skills/peft/sub-skills/lora-and-quantization/scripts/lora_config_sanity.py --check
```

Use the output to catch config-time incompatibilities before loading a model. This does not prove that model-specific target names exist; it only verifies representative PEFT configuration construction and optional dependency caveats.
