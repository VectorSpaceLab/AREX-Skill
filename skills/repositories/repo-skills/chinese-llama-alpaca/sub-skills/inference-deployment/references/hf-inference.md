# Hugging Face Inference

Use [`scripts/inference_hf.py`](../scripts/inference_hf.py) for local Transformers inference with a merged Hugging Face model or a base model plus LoRA adapter. The script loads `LlamaForCausalLM`, `LlamaTokenizer`, optional `PeftModel`, applies attention/NTK patches, and writes batch predictions as JSON.

## Core Command Patterns

### Batch prompts from a text file

```bash
python scripts/inference_hf.py \
  --base_model /path/to/base_or_merged_hf_model \
  --lora_model /path/to/chinese_alpaca_lora_or_none \
  --tokenizer_path /path/to/matching_tokenizer \
  --data_file /path/to/instructions.txt \
  --with_prompt \
  --predictions_file /path/to/predictions.json \
  --gpus 0
```

### Single-turn interactive instruction mode

```bash
python scripts/inference_hf.py \
  --base_model /path/to/base_or_merged_hf_model \
  --lora_model /path/to/chinese_alpaca_lora_or_none \
  --with_prompt \
  --interactive \
  --gpus 0
```

The interactive mode is single-turn. For multi-turn chat, use Gradio, llama.cpp-style chat, LlamaChat, or an external chat wrapper.

## CLI Flags

| Flag | Required | Meaning |
| --- | --- | --- |
| `--base_model` | yes | HF-format base model or already merged model. |
| `--lora_model` | no | LoRA adapter path/model id. If omitted, inference runs on `--base_model` directly. |
| `--tokenizer_path` | no | Tokenizer path. Defaults to `--lora_model`, then `--base_model`. Set explicitly when debugging tokenizer mismatches. |
| `--data_file` | no | Text file with one instruction per line. If omitted, a built-in Chinese sample prompt is used. |
| `--with_prompt` | no | Wrap input in Alpaca instruction template and split output at `### Response:`. Use for Chinese Alpaca instruction tasks. |
| `--interactive` | no | Start single-turn prompt loop. Empty input exits. |
| `--predictions_file` | no | JSON output path for batch mode. The script also writes `generation_config.json` in the same directory. |
| `--gpus` | no | `CUDA_VISIBLE_DEVICES` value, default `0`. Use comma-separated ids for multi-GPU device maps. |
| `--only_cpu` | no | Clears `CUDA_VISIBLE_DEVICES`; generation may be slow. |
| `--alpha` | no | NTK scaling factor, float or `auto`; default `1.0`. |
| `--load_in_8bit` | no | Loads model in 8-bit mode to reduce VRAM, when the installed stack supports it. |

## Prompt Template

When `--with_prompt` is set, the script wraps the user instruction as:

```text
Below is an instruction that describes a task. Write a response that appropriately completes the request.

### Instruction:

{instruction}

### Response:

```

Use `--with_prompt` for Chinese Alpaca instruction following and QA. For Chinese LLaMA base continuation, omit it unless the user intentionally wants prompt-format experimentation.

## Generation Defaults

The script uses:

```text
temperature=0.2, top_k=40, top_p=0.9, do_sample=True,
num_beams=1, repetition_penalty=1.1, max_new_tokens=400
```

These are reasonable starting points from the repo scripts, not universal best settings. For creative writing/chat, the user may increase temperature; for constrained QA, keep it lower.

## Output Files

Batch mode appends dictionaries like `{"Input": input_text, "Output": response}` to `--predictions_file`. If `--with_prompt` is set, `Input` stores the full prompt template. The sibling `generation_config.json` records decoding defaults.

## Preflight Checks

Before real generation:

1. Check model/tokenizer family. Alpaca tokenizers differ from LLaMA tokenizers.
2. Confirm the model path is a loadable HF model or a base+LoRA pair.
3. Run `python scripts/inference_hf.py --help` in the target environment.
4. If CUDA is expected, run the root environment checker with optional backend output.
5. Keep a tiny input file for first generation; do not start with a large prompt batch.
