# GPTQ troubleshooting

Start with the safe probe:

```bash
python scripts/gptq_availability_probe.py --json
```

Use `--strict` when the current task requires full GPTQ quantization or quantized loading, not just documentation/config inspection.

## Dependency and import failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `RuntimeError: GPT-QModel is required... pip install gptqmodel>=7.0.0` | `gptqmodel` is not installed. | Install `gptqmodel>=7.0.0` in the runtime environment if the user approved optional GPTQ dependencies. Re-run the probe. |
| `ImportError: Found an incompatible version of GPT-QModel` | `gptqmodel` is installed but older than `7.0.0`. | Upgrade to `gptqmodel>=7.0.0`. Avoid working around the version gate. |
| `NameError` or constructor failure involving `QuantizeConfig` | `GPTQQuantizer` was instantiated even though GPT-QModel classes were unavailable. Importing `optimum.gptq` alone is not enough. | Run the probe; instantiate `GPTQQuantizer` only when GPT-QModel is present and compatible. |
| `You need to install accelerate...` from `load_quantized_model` | `accelerate` is missing. | Install `accelerate`; it is required for quantized checkpoint dispatch. |
| Backend enum or kernel import error | Explicit `backend` does not exist or is unsupported by the installed GPT-QModel/hardware combination. | Retry with `backend="auto"`. Use explicit backends only when GPT-QModel documents support for the exact environment. |

## CUDA, accelerator, and CPU-only limitations

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Probe reports `torch.cuda.available = false` | No CUDA-visible GPU in the environment, or CPU-only PyTorch. | Treat full GPTQ quantization and kernel validation as unavailable. A CPU import/config probe is partial and does not validate quantized inference kernels. |
| Quantization is extremely slow or runs out of memory | GPTQ is expensive and model-size dependent. | Reduce model size, calibration sample count, or batch size; request more GPU memory/time; check whether a pre-quantized model already exists in the user's approved source. |
| `device_map=None` fails in a no-CUDA environment | `load_quantized_model` defaults to `torch.cuda.current_device()` when no `device_map` is given. | Pass `device_map` explicitly. For full GPTQ inference, ensure the selected map is supported by GPT-QModel kernels. |
| `ValueError: disk offload is not supported with GPTQ quantization` | The model has an `hf_device_map` containing `"disk"`. | Remove disk offload from the quantization device map, rebalance `max_memory`, use a smaller model, or use a larger accelerator. Do not claim disk-offloaded quantization is supported. |

## Model and dtype failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Tokenizer/model error says only text models are supported | The model is not a text causal language model, or the tokenizer cannot be resolved. | Use a text `AutoModelForCausalLM`-style model and a matching tokenizer. Route vision/speech/multimodal quantization elsewhere. |
| Quality is poor or quantization errors mention dtype/kernel assumptions | Model was not loaded in `torch.float16`. | Load the model with `torch_dtype=torch.float16` before quantization. Treat fp16 as required for this Optimum GPTQ path. |
| `You need to pass dataset in order to quantize your model` | `GPTQQuantizer.dataset` is `None`. | Provide a list of representative strings, tokenized examples, or a supported dataset name. |
| Dataset helper raises about `pad_token_id` | `batch_size > 1` without a padding id. | Pass `pad_token_id=tokenizer.pad_token_id` or keep `batch_size=1`. |
| Built-in dataset name fails or tries to download | `datasets` package or dataset access is missing. | Use local raw strings or pre-tokenized examples for offline/no-download workflows; install/approve dataset access only when needed. |

## Custom architecture failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `Block pattern could not be match. Pass block_name_to_quantize...` | Automatic block-path patterns did not match the model. | Inspect `model.named_modules()`, find the module list containing Transformer blocks, and set `block_name_to_quantize`. |
| Sequence length silently defaults to `2048` | Model config lacks `max_position_embeddings`, `seq_length`, or `n_positions`. | Set `model_seqlen` explicitly to the model's real context length. |
| Calibration hook fails before the first block | Modules preceding the first block were not moved/run correctly for a custom tree. | Set `module_name_preceding_first_block` to the embedding/norm/projection modules that must execute before the first block. |
| Selective quantization raises a missing-key error or leaves modules unconverted | `modules_in_block_to_quantize` names are wrong or are not relative to each block. | Print `for name, _ in block.named_modules(): ...`, then use exact names such as `self_attn.q_proj` or `mlp.down_proj`. |
| Saved custom quantized model loads fail with block-pattern errors | Default `quantize_config.json` omitted runtime-only custom fields such as `block_name_to_quantize`. | Add recognized constructor keys such as `block_name_to_quantize` to the local `quantize_config.json`, or use an architecture whose block path can be inferred. Keep the edit documented. |

## Save/load and serialization failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `Failed to load quantization config from ...` | `quantize_config.json` is missing, unreadable, or `config.json` lacks `quantization_config`. | Check the save directory contains `quantize_config.json`, `config.json`, and model weight files. Pass `quant_config_name` if the file was renamed. |
| Load points at the wrong checkpoint or shard | `save_folder` or `state_dict_name` does not match the actual saved weights. | Point `save_folder` at the directory produced by `quantizer.save`; use `state_dict_name` only for a deliberate custom weight filename. |
| `AutoModelForCausalLM.from_pretrained(saved_dir)` fails for a quantized directory | Directory has GPTQ weights/config but lacks required Transformers config/tokenizer files, or dependencies are missing. | Ensure `config.json` and weights are present; save tokenizer separately if the task needs tokenizer loading; install GPT-QModel and Accelerate. |
| Loading succeeds but backend/inference fails | Auto-selected kernel is incompatible, or explicit backend was wrong. | Retry `backend="auto"`, verify CUDA/GPT-QModel versions, and avoid explicit backend overrides unless proven. |

## Parameter validation errors

| Symptom | Cause | Fix |
| --- | --- | --- |
| `only support quantize to [2,3,4,8] bits` | Invalid `bits`. | Use `2`, `3`, `4`, or `8`. |
| `group_size must be greater than 0 or equal to -1` | Invalid `group_size`. | Use a positive group size such as `128`, or `-1` for per-column quantization. |
| `damp_percent must between 0 and 1` | Invalid Hessian dampening value. | Use a float strictly between `0` and `1`, commonly `0.1`. |
| Act-order/GAR incompatibility or quality regression | `desc_act` and `act_group_aware` were combined without backend support. | For act-order (`desc_act=True`), prefer `act_group_aware=False`. For the common faster path, use `desc_act=False`, `act_group_aware=True`. |

## When to stop and report a gap

Stop instead of attempting hidden workarounds when:

- The user has not approved optional installs, model/dataset downloads, or GPU time.
- `gptqmodel>=7.0.0` cannot be installed in the target runtime.
- No compatible accelerator is available for a task that requires full quantization or quantized inference validation.
- The requested model is not a text causal language model.
- The saved checkpoint directory is incomplete and cannot be reconstructed from user-provided artifacts.
