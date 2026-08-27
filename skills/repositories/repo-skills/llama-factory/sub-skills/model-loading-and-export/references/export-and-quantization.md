# Export and Quantization

## Export Command

LlamaFactory exports with the CLI export subcommand:

```bash
llamafactory-cli export CONFIG.yaml
# or
lmf export CONFIG.yaml
```

The export flow parses inference-style arguments, loads tokenizer/processor/template, loads the model, optionally merges adapters during model loading, converts dtype, saves model shards, optionally pushes to Hub, saves tokenizer/processor, and writes an Ollama `Modelfile` into `export_dir`.

Do not run export, merge, quantization, or hub push without explicit user approval. These operations can download large models, allocate GPU/CPU memory, overwrite output directories, and push artifacts externally.

## Export Arguments

Key fields:

- `export_dir`: required output directory.
- `export_size`: shard size in GB; default `5`.
- `export_device`: `cpu` or `auto`; `cpu` is safer, `auto` can use available accelerators.
- `export_legacy_format`: when false, uses safe-tensor format where supported; when true, saves legacy `.bin` files.
- `export_hub_model_id`: optional Hugging Face Hub repo id for push.
- `export_quantization_bit`: export-time GPTQ quantization bit; allowed values are `2`, `3`, `4`, or `8`.
- `export_quantization_dataset`: required when `export_quantization_bit` is set.
- `export_quantization_nsamples`: calibration samples; default `128`.
- `export_quantization_maxlen`: calibration sequence length; default `1024`.
- `infer_dtype`: `auto`, `float16`, `bfloat16`, or `float32`; used when exporting non-quantized models.

## Safe Export Patterns

Full or already-merged model export:

```yaml
model_name_or_path: saves/qwen3-4b/full/sft
template: qwen3_nothink
trust_remote_code: true

export_dir: saves/qwen3_sft_merged
export_size: 5
export_device: cpu
export_legacy_format: false
```

LoRA adapter merge/export:

```yaml
model_name_or_path: Qwen/Qwen3-4B-Instruct-2507
adapter_name_or_path: saves/qwen3-4b/lora/sft
template: qwen3_nothink
trust_remote_code: true

export_dir: saves/qwen3_sft_merged
export_size: 5
export_device: cpu
export_legacy_format: false
```

Export-time GPTQ quantization from an unadapted or already-merged model:

```yaml
model_name_or_path: Qwen/Qwen3-4B-Instruct-2507
template: qwen3_nothink
trust_remote_code: true

export_dir: saves/qwen3_gptq
export_quantization_bit: 4
export_quantization_dataset: data/c4_demo.jsonl
export_quantization_nsamples: 128
export_quantization_maxlen: 1024
export_size: 5
export_device: cpu
export_legacy_format: false
```

## Hard Export Rules

The export code enforces these constraints:

- `export_dir` is required.
- `export_quantization_bit` requires `export_quantization_dataset`.
- `adapter_name_or_path` cannot be combined with `export_quantization_bit`; merge adapters first, then quantize the merged model in a separate export.
- If the loaded model is already quantized and `adapter_name_or_path` is set, export aborts because adapters cannot be merged into a quantized model.
- The exported object must be a Transformers `PreTrainedModel`.
- For quantized exports, config `torch_dtype` is set to float16.
- For non-quantized exports, `infer_dtype: auto` chooses an optimized half/bfloat dtype when the config dtype is float32; otherwise explicit `infer_dtype` is used.
- Transformers 5 removes the `safe_serialization` save argument; older versions use `not export_legacy_format`.

Use `scripts/check_export_config.py CONFIG.yaml` for static preflight checks before recommending a run.

## Quantization Modes

LlamaFactory has three distinct quantization situations. Do not mix their config fields.

### PTQ-Quantized Model Loading

Some hub/local models include `quantization_config` in their config. LlamaFactory treats these as pre-quantized models.

Rules and dependency hints:

- `quantization_bit` does not re-quantize PTQ models and is ignored with a warning.
- DeepSpeed ZeRO-3/FSDP are incompatible with most PTQ models; MXFP4 and FP8 have special dequantized load handling.
- GPTQ PTQ requires `gptqmodel>=2.0.0`; LlamaFactory disables exllama for this path.
- AWQ PTQ requires `autoawq`.
- AQLM PTQ requires `aqlm>=1.1.0` and uses 2-bit settings.

### Export-Time GPTQ Quantization

`export_quantization_bit` invokes GPTQModel/Optimum quantization during export.

Rules:

- Allowed bits: `2`, `3`, `4`, `8`.
- Requires `export_quantization_dataset`.
- Requires `optimum>=1.24.0` and `gptqmodel>=2.0.0`.
- Uses a calibration dataset with a `text` field.
- Sets `device_map: auto` and max-memory placement.
- Forces compute dtype to fp16 during quantization.
- ChatGLM export quantization is not supported.

### On-The-Fly Quantization

`quantization_bit` plus `quantization_method` controls model loading for QLoRA-style training or inference.

Supported methods and bits:

- `bnb`: bitsandbytes 4-bit or 8-bit; `bitsandbytes>=0.39.0`, and `bitsandbytes>=0.43.0` for FSDP+QLoRA or auto device map.
- `hqq`: 1, 2, 3, 4, 5, 6, or 8 bits; requires `hqq`; incompatible with DeepSpeed ZeRO-3/FSDP.
- `eetq`: 8-bit only; requires `eetq`; incompatible with DeepSpeed ZeRO-3/FSDP.

Typical QLoRA fields:

```yaml
model_name_or_path: Qwen/Qwen3-4B-Instruct-2507
quantization_bit: 4
quantization_method: bnb
finetuning_type: lora
lora_target: all
trust_remote_code: true
```

## Optional Dependency Selection

Use the error text and desired backend to choose extras:

- bitsandbytes 4/8-bit load: install the bitsandbytes extra; ensure platform support.
- GPTQ export or GPTQ PTQ load: install the GPTQ extra with Optimum and GPTQModel.
- AWQ PTQ model: install AutoAWQ.
- AQLM PTQ model: install AQLM with GPU support.
- HQQ on-the-fly load: install HQQ.
- EETQ on-the-fly load: install EETQ.
- FP8/MXFP4 config handling may require TorchAO or Transformer Engine style stacks depending on the model and hardware.
- vLLM is an inference serving backend, not an export quantization dependency; route serving setup to `inference-and-serving`.

## Hub Push Notes

`export_hub_model_id` pushes model files, tokenizer, and processor to the Hugging Face Hub using `hf_hub_token`. Confirm the target repo, visibility, and token source before running. Avoid storing tokens in config files.
