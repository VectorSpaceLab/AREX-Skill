# Reconstruction Workflows

Use these workflows with the bundled scripts in `scripts/`. Replace placeholder paths with user-provided model and output paths. Do not run these commands until the user has confirmed license, assets, disk/RAM budget, and output policy.

## Standard LoRA Merge

Use the standard script when CPU RAM is sufficient for the chosen model size.

```bash
python scripts/merge_llama_with_chinese_lora.py \
  --base_model /path/to/hf_llama_base \
  --lora_model /path/to/chinese_lora \
  --output_type huggingface \
  --output_dir /path/to/output_hf_model
```

Important flags:

| Flag | Meaning |
| --- | --- |
| `--base_model` | Required HF-format original LLaMA-compatible base model path. |
| `--lora_model` | Required comma-separated ordered LoRA paths or model ids. |
| `--offload_dir` | Optional temp folder for CPU offloading in the standard script. Useful on lower-RAM machines. |
| `--output_type {pth,huggingface}` | Choose original shard format or HF directory. |
| `--output_dir` | Destination directory. It will receive tokenizer and model outputs. |

## Low-Memory Merge

Use the low-memory script when standard merging exceeds RAM or when you want a chunked multi-LoRA merge. It preserves the same core arguments except `--offload_dir` is not exposed.

```bash
python scripts/merge_llama_with_chinese_lora_low_mem.py \
  --base_model /path/to/hf_llama_base \
  --lora_model /path/to/chinese_llama_lora,/path/to/chinese_alpaca_lora \
  --output_type huggingface \
  --output_dir /path/to/output_hf_model \
  --verbose
```

The comma-separated `--lora_model` list is ordered. For multi-stage Alpaca variants, apply the base Chinese LLaMA/Plus adapter before the instruction Alpaca adapter unless user evidence says otherwise.

## PTH Output for llama.cpp-Style Conversion

```bash
python scripts/merge_llama_with_chinese_lora_low_mem.py \
  --base_model /path/to/hf_llama_base \
  --lora_model /path/to/chinese_lora \
  --output_type pth \
  --output_dir /path/to/pth_output
```

Expected output includes `consolidated.00.pth` for 7B, two shards for 13B, four shards for 33B, and `params.json`. Tokenizer files are also saved to the output directory.

## Tokenizer Vocabulary Extension

The tokenizer helper merges the bundled Chinese SentencePiece vocabulary into a user-provided LLaMA tokenizer directory. It writes `merged_tokenizer_sp/chinese_llama.model` and `merged_tokenizer_hf/` in the current working directory.

```bash
python scripts/merge_tokenizers.py \
  --llama_tokenizer_dir /path/to/original_llama_tokenizer
```

By default, the script uses bundled `scripts/chinese_sp.model`. Pass `--chinese_sp_model_file /path/to/custom.model` only when intentionally replacing that bundled model.

## Post-Merge Validation

After a merge:

1. Check the output directory exists and contains tokenizer files.
2. For HF output, run a lightweight tokenizer/model metadata inspection before generation:
   ```bash
   python - <<'PY'
from transformers import LlamaTokenizer
p = '/path/to/output_hf_model'
tok = LlamaTokenizer.from_pretrained(p)
print('tokenizer length', len(tok), tok.special_tokens_map)
PY
   ```
3. For PTH output, verify shard count and `params.json` model size.
4. Run SHA256 checks only when the expected digest for that exact output is documented and the PyTorch version matches the checksum reference.
5. Route to inference guidance for a tiny generation test only after the user approves loading the model.

## What Not To Do

- Do not point users to source checkout scripts; use the bundled `scripts/` copies.
- Do not treat a LoRA adapter directory as a full model. It must be merged with or loaded on top of a compatible base model.
- Do not mix LLaMA and Alpaca tokenizers.
- Do not delete or overwrite a user output directory unless explicitly authorized.
