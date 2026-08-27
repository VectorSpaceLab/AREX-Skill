# Model customization plan

This reference covers the two source helper flows that modify a checkpoint copy: quantization and tokenizer tag extension.

## Quantization

The source quantization helper creates bitsandbytes-backed 4-bit or 8-bit copies and saves them to new directories. Treat it as a mutation-capable workflow.

### Source behavior distilled from `quantize.py`

- 4-bit path uses NF4 quantization.
- 4-bit path uses bf16 computation.
- 4-bit path enables double quantization by default.
- 8-bit path uses `llm_int8_threshold=6.0`.
- Both paths load the model and tokenizer, then save a new copy.
- The helper writes into `output_dir/4bit` and `output_dir/8bit`.

### Safe planning rule

The bundled planner prints commands only. Do not run the quantization command unless the caller explicitly asks to write a quantized copy and provides the source checkpoint and output directory.

### Command templates

4-bit only:

```bash
python quantize.py --model_path <base_model> --output_dir <output_dir> --quant_type 4bit
```

8-bit only:

```bash
python quantize.py --model_path <base_model> --output_dir <output_dir> --quant_type 8bit
```

Both paths:

```bash
python quantize.py --model_path <base_model> --output_dir <output_dir> --quant_type both
```

Disable double quantization for 4-bit if you need the exact source flag behavior:

```bash
python quantize.py --model_path <base_model> --output_dir <output_dir> --quant_type 4bit --no_double_quant
```

### When to choose each path

- 4-bit: when memory is tight and you want the largest viable context window.
- 8-bit: when you want a lighter step down from the original model but do not need the most aggressive compression.
- Both: when you are preparing multiple deployment profiles from one base checkpoint copy.

### Environment note

The source quantization path depends on a CUDA-capable runtime with the required model libraries. A CPU-only inspection environment is not enough to verify real quantization.

## Tokenizer tag extension

The source tag-extension helper adds the DeepAnalyze control tags and resizes embeddings before saving a new checkpoint copy.

### Add these tags

- `<Analyze>`
- `</Analyze>`
- `<Understand>`
- `</Understand>`
- `<Code>`
- `</Code>`
- `<Execute>`
- `</Execute>`
- `<Answer>`
- `</Answer>`

### Source behavior distilled from `deepanalyze/add_vocab.py`

- Loads a model and tokenizer from a base checkpoint.
- Adds the fixed DeepAnalyze tag list when `--add_tags` is set.
- Resizes token embeddings after the vocabulary changes.
- Saves the tokenizer and model to a new directory.
- Includes a small encoding sanity check for the new tags.

### Use before training

If the base checkpoint is `DeepSeek-R1-0528-Qwen3-8B`, add the tags before any SFT or RL step so the training prompts and the model vocabulary agree.

### Command template

```bash
python deepanalyze/add_vocab.py \
  --model_path <base_model_path> \
  --save_path <extended_model_path> \
  --add_tags
```

### Safety rule

This command writes a new checkpoint directory. Keep the source checkpoint untouched and point downstream training at the new save path.
