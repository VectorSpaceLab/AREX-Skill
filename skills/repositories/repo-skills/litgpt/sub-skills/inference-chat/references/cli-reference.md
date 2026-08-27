# LitGPT Inference CLI Reference

This reference distills verified LitGPT CLI help, implementation signatures, and inference tests. Commands assume the first positional checkpoint argument is already a ready LitGPT checkpoint directory unless noted otherwise.

## Common Generation Options

| Option | Applies To | Meaning | Notes |
| --- | --- | --- | --- |
| `checkpoint_dir` | `generate`, `chat`, `generate_full`, adapters, sequential, TP | Local checkpoint directory to load | A ready LitGPT checkpoint normally contains `lit_model.pth`, `model_config.yaml`, and tokenizer files. If the route may download from a model name, validate intent first. |
| `--prompt` | generation commands except `chat` | User prompt text | Default is a llama-food example. Quote shell metacharacters. |
| `--sys_prompt` | generation commands | Optional system prompt used by prompt style | Ignored by some default styles; useful for chat/instruct styles. |
| `--num_samples` | non-chat generation commands | Number of samples to print | Each sample reuses the same prompt and sampling options. |
| `--max_new_tokens` | all generation/chat commands | Maximum generated tokens | Memory grows with prompt length plus this value because KV-cache length must fit the returned sequence. |
| `--top_k` | all generation/chat commands | Restrict sampling to the top K logits | `None` disables top-k filtering. Positive integers are typical; `1` is near-greedy. |
| `--top_p` | all generation/chat commands | Nucleus sampling threshold | Must be in `[0, 1]`. `0` makes generation greedy; `1` uses the full filtered distribution. |
| `--temperature` | all generation/chat commands | Randomness scale | `0` makes generation greedy. Values above `1` are more random; negative values are invalid for practical use. |
| `--quantize` | most inference commands | Inference-time bitsandbytes quantization | Values are `bnb.nf4`, `bnb.nf4-dq`, `bnb.fp4`, `bnb.fp4-dq`, `bnb.int8` where supported by the command. Sequential/TP support the 4-bit variants. |
| `--precision` | all weight-loading generation/chat commands | Lightning Fabric precision | Common true precision values include `32-true`, `16-true`, and `bf16-true`. Do not combine `bnb.*` quantization with mixed precision. |
| `--compile` | `generate`, `chat`, sequential, TP, speculative | Compile token generation | Speeds repeated generation after startup but can increase startup time and KV-cache memory. Some quantized multi-device routes mark compile as untested. |

## `litgpt generate`

Default one-shot generation from a ready LitGPT checkpoint.

```bash
litgpt generate CHECKPOINT_DIR \
  --prompt "Explain why llamas chew cud." \
  --max_new_tokens 80 \
  --top_k 50 \
  --top_p 0.9 \
  --temperature 0.8
```

Use this when the checkpoint already has compatible weights, tokenizer, and config. The command applies a bundled `prompt_style.json` when present; otherwise it chooses a prompt style from `model_config.yaml`.

## `litgpt chat`

Interactive REPL for a local checkpoint or accepted model identifier.

```bash
litgpt chat CHECKPOINT_DIR --max_new_tokens 100 --top_k 50 --top_p 0.95 --temperature 0.8
```

Use `--multiline true` when user turns span multiple lines. In multiline mode, type `!submit` on its own line to submit; use `!quit` or `!exit` to leave. If the checkpoint directory contains `lit_model.pth.lora` but not `lit_model.pth`, the chat implementation can merge LoRA weights once before chatting; for planned merge workflows, route to `../../checkpoint-conversion/`.

## Fine-Tuned Checkpoint Generation Routes

Use the generation command that matches how the checkpoint was produced:

| Command | Use For | Extra Artifact |
| --- | --- | --- |
| `litgpt generate_full` | Full finetuning output | `--finetuned_path` points to the full finetuned `.pth` file; default is `out/full/alpaca/lit_model_finetuned.pth`. |
| `litgpt generate_adapter` | Adapter finetuning output | `--adapter_path` points to `.pth.adapter`; default is `out/finetune/adapter/final/lit_model.pth.adapter`. |
| `litgpt generate_adapter_v2` | Adapter v2 finetuning output | `--adapter_path` points to `.pth.adapter_v2`; default is `out/finetune/adapter-v2/final/lit_model.pth.adapter_v2`. |

These commands still need the base `checkpoint_dir` for config/tokenizer/base weights. They apply an Alpaca-style instruction/input pattern through the active prompt style and often strip text after `### Response:`. If a user has a LoRA output instead of adapter/full artifacts, route to `../../checkpoint-conversion/` for merge or checkpoint handling.

## Multi-Device Generation Routes

### Sequential Layer Placement

```bash
CUDA_VISIBLE_DEVICES=0,1,2,3 litgpt generate_sequentially CHECKPOINT_DIR \
  --prompt "Summarize transformer KV caches." \
  --max_new_tokens 256 \
  --num_samples 2
```

`generate_sequentially` partitions transformer blocks across visible CUDA devices and runs them sequentially. It is useful when a model cannot fit on one GPU. It requires CUDA; CPU and MPS are not valid for this route. The number of model layers must be at least the number of devices. Smaller `--max_new_tokens` and 4-bit `--quantize bnb.nf4-dq` can reduce memory.

### Tensor Parallel

```bash
CUDA_VISIBLE_DEVICES=0,1,2,3 litgpt generate_tp CHECKPOINT_DIR \
  --prompt "Give three sampling tips." \
  --max_new_tokens 128
```

`generate_tp` shards attention and MLP linear layers across CUDA devices. It can be faster than sequential placement but requires model dimensions to divide evenly by the world size. It launches distributed workers and is not appropriate for interactive notebooks. Check divisibility errors such as `n_head`, `n_embd`, `n_query_groups`, linear `out_features`, or `in_features` not evenly divisible by the number of devices.

## Speculative Decoding

```bash
litgpt generate_speculatively DRAFT_CHECKPOINT_DIR TARGET_CHECKPOINT_DIR \
  --prompt "Write a short haiku about GPUs." \
  --speculative_k 3 \
  --max_new_tokens 80
```

Speculative decoding uses a smaller/faster draft model to propose tokens and a larger target model to verify them. Both checkpoint directories must be valid and their tokenizers must have the same vocabulary size. `--speculative_k` must be at least `1`. The command reports acceptance behavior in addition to generated text.

## Quantization Values

Inference commands accept bitsandbytes values with a `bnb.` prefix. LitGPT’s CLI help may display the inner values (`nf4`, `nf4-dq`, `fp4`, `fp4-dq`, `int8`) because of type formatting, but implementation paths check for `bnb.` strings. Prefer the documented full values:

- `bnb.nf4`: normalized 4-bit float; common recommendation.
- `bnb.nf4-dq`: normalized 4-bit float with double quantization for lower memory.
- `bnb.fp4`: 4-bit float.
- `bnb.fp4-dq`: 4-bit float with double quantization.
- `bnb.int8`: 8-bit inference quantization where supported.

Quantization requires `bitsandbytes` and CUDA/Linux-compatible runtime. It rejects mixed precision; use true precision such as `--precision bf16-true`, `--precision 16-true`, or `--precision 32-true`.

## Check Before Running

Use the bundled checker to catch common mistakes without loading weights:

```bash
python sub-skills/inference-chat/scripts/check_inference_inputs.py \
  --checkpoint-dir CHECKPOINT_DIR \
  --prompt "Hello" \
  --top-p 0.9 \
  --temperature 0.8 \
  --quantize bnb.nf4 \
  --precision bf16-true \
  --require-cuda
```

If it reports missing checkpoint files or tokenizer files, route to `../../checkpoint-conversion/` before running inference.
