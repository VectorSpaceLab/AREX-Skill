# Export Workflows

`ms-swift` exposes export operations primarily through the `swift export` route and a shortcut `swift merge-lora` route. The Python API equivalent is `swift.export_main(ExportArguments(...))`; use it when a programmatic workflow already has Python objects, otherwise prefer CLI commands for reproducible handoff.

## Choose the Operation

| Goal | Main route | Required intent flags | Notes |
| --- | --- | --- | --- |
| Merge a trained adapter into base weights | `swift export` or `swift merge-lora` | `--adapters <checkpoint> --merge_lora true` | The checkpoint produced by `swift` usually contains `args.json`, so base model/template information can be recovered. |
| Quantize a model | `swift export` | `--model <model-or-merged-dir> --quant_method <method>` | AWQ/GPTQ/GPTQ v2 require `--quant_bits`; FP8 does not. AWQ/GPTQ also require calibration data. |
| Merge then quantize LoRA | `swift export` | `--adapters <checkpoint> --merge_lora true --quant_method <method>` | The export pipeline merges first, then quantizes. Merging is performed against original unquantized weights. |
| Push checkpoint/model to hub | `swift export` | `--model` or `--adapters`, `--push_to_hub true`, `--hub_model_id <id>` | Default hub is ModelScope. Add `--use_hf true` for Hugging Face. |
| Export tokenized cached dataset | `swift export` | `--to_cached_dataset true` plus dataset/template inputs | Use when later training should reuse pre-tokenized data. Do not combine with streaming or packing. |
| Convert to Ollama | `swift export` | `--to_ollama true` | Keep inference/deployment tuning outside this sub-skill. |

## LoRA Merge Patterns

Minimal CLI pattern:

```bash
swift export \
  --adapters output/run/checkpoint-100 \
  --merge_lora true \
  --output_dir output/run/checkpoint-100-merged
```

Shortcut route pattern:

```bash
swift merge-lora \
  --adapters output/run/checkpoint-100 \
  --output_dir output/run/checkpoint-100-merged
```

Guidance:

- Use `--adapters` for LoRA/LLaMAPro/LongLoRA adapter checkpoints.
- Use `--model` for full model directories, merged model directories, or model IDs.
- If output already exists, `ExportArguments.exist_ok` / `--exist_ok true` allows overwrite behavior; otherwise export raises or skips depending on the internal operation.
- QLoRA-trained adapters cannot be reliably merged into full weights for acceleration workflows. Prefer standard LoRA/full-parameter training when the end goal is merged weights for vLLM/SGLang/LMDeploy, then quantize the merged model.

## Quantization Matrix

| Method | Typical flags | Calibration dataset | Optional packages | Notes |
| --- | --- | --- | --- | --- |
| AWQ | `--quant_method awq --quant_bits 4` | Required | `autoawq` | CUDA/AutoAWQ/torch versions must match. Multimodal support exists but is model-limited. |
| GPTQ | `--quant_method gptq --quant_bits 4` | Required | `auto_gptq optimum` | Set `OMP_NUM_THREADS` if AutoGPTQ CPU threading causes instability. |
| GPTQ v2 | `--quant_method gptq_v2 --quant_bits 4` | Usually required | `gptqmodel optimum` | Use when the newer GPTQ backend is desired. |
| BNB | `--quant_method bnb --quant_bits 4` or `8` | Not required | `bitsandbytes` | BNB export is fastest; BNB multimodal export is not broadly supported. |
| FP8 | `--quant_method fp8` | Not required | Backend/model dependent | Useful for inference acceleration; special MoE cases may need the Megatron route instead. |

AWQ/GPTQ pattern:

```bash
CUDA_VISIBLE_DEVICES=0 swift export \
  --model Qwen/Qwen2.5-1.5B-Instruct \
  --dataset AI-ModelScope/alpaca-gpt4-data-zh#500 AI-ModelScope/alpaca-gpt4-data-en#500 \
  --quant_n_samples 256 \
  --quant_batch_size 1 \
  --max_length 2048 \
  --quant_method gptq \
  --quant_bits 4 \
  --output_dir Qwen2.5-1.5B-Instruct-GPTQ-Int4
```

BNB pattern:

```bash
CUDA_VISIBLE_DEVICES=0 swift export \
  --model Qwen/Qwen2.5-1.5B-Instruct \
  --quant_method bnb \
  --quant_bits 4 \
  --bnb_4bit_quant_type nf4 \
  --bnb_4bit_use_double_quant true \
  --output_dir Qwen2.5-1.5B-Instruct-BNB-NF4
```

FP8 pattern:

```bash
CUDA_VISIBLE_DEVICES=0 swift export \
  --model Qwen/Qwen2.5-3B-Instruct \
  --quant_method fp8 \
  --output_dir Qwen2.5-3B-Instruct-FP8
```

## Hub Push Patterns

ModelScope is the default target:

```bash
swift export \
  --model output/run/checkpoint-100-merged \
  --push_to_hub true \
  --hub_model_id owner-or-org/model-name \
  --hub_token "$MODELSCOPE_TOKEN" \
  --hub_private_repo true
```

Hugging Face target:

```bash
swift export \
  --model output/run/checkpoint-100-merged \
  --push_to_hub true \
  --use_hf true \
  --hub_model_id owner/model-name \
  --hub_token "$HF_TOKEN" \
  --hub_private_repo true
```

Security and selection rules:

- Never paste real hub tokens into shared logs or generated scripts; read them from environment variables or a secret manager.
- `--model <checkpoint-or-model-dir>` and `--adapters <checkpoint-dir>` are equivalent for a pure push of an existing checkpoint directory, but `--adapters` has adapter semantics for merge/export operations.
- For private repositories, set `--hub_private_repo true` at first push because the repository may be auto-created.
- Verify the account behind the token has write permission for the target namespace.

## Cached Dataset Export

Use cached dataset export when the same dataset/template combination will be reused and tokenization cost matters:

```bash
swift export \
  --model Qwen/Qwen2.5-0.5B-Instruct \
  --dataset AI-ModelScope/alpaca-gpt4-data-zh#1000 \
  --template qwen2_5 \
  --to_cached_dataset true \
  --output_dir cached/alpaca-qwen2_5
```

Constraints:

- Cached export tokenizes in advance and disables lazy tokenization.
- Do not use cached export with streaming datasets.
- Do not set packing during cached export; packing belongs to the later training step.
- If the cached dataset was prepared with validation data, use the same split/validation intent in later training.

## Programmatic API

Programmatic merge example:

```python
from swift import ExportArguments, export_main

export_main(ExportArguments(
    adapters="output/run/checkpoint-100",
    merge_lora=True,
    output_dir="output/run/checkpoint-100-merged",
))
```

Programmatic quantization example:

```python
from swift import ExportArguments, export_main

export_main(ExportArguments(
    model="Qwen/Qwen2.5-1.5B-Instruct",
    dataset=["AI-ModelScope/alpaca-gpt4-data-zh#500"],
    quant_method="awq",
    quant_bits=4,
    output_dir="Qwen2.5-1.5B-Instruct-AWQ",
))
```

## Command Builder Helper

Use the bundled helper to avoid forgetting required flags:

```bash
python scripts/build_export_command.py merge-lora \
  --adapters output/run/checkpoint-100 \
  --output-dir output/run/checkpoint-100-merged

python scripts/build_export_command.py quantize \
  --model output/run/checkpoint-100-merged \
  --method awq \
  --bits 4 \
  --dataset AI-ModelScope/alpaca-gpt4-data-zh#500 \
  --output-dir output/run/checkpoint-100-merged-awq
```
