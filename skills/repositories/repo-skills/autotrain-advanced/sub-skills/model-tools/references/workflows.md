# Model tool workflows

## Merge LLM adapter

Package CLI:

```bash
autotrain tools merge-llm-adapter \
  --base-model-path base/model-or-path \
  --adapter-path adapter/model-or-path \
  --output-folder merged-model \
  --token "$HF_TOKEN" \
  --pad-to-multiple-of 8
```

Standalone helper:

```bash
python skills/disco/autotrain-advanced/sub-skills/model-tools/scripts/merge_llm_adapter.py \
  --base-model-path base/model-or-path \
  --adapter-path adapter/model-or-path \
  --output-folder merged-model \
  --token "$HF_TOKEN"
```

Inputs:

- `base_model_path` — local path or Hub id for the base causal LM.
- `adapter_path` — local path or Hub id for the PEFT adapter and tokenizer.
- `token` — optional token for private artifacts.
- `pad_to_multiple_of` — optional tokenizer/model embedding padding multiple.
- `output_folder` — local save target.
- `push_to_hub` — pushes model/tokenizer to the adapter path repo.

Output:

- merged model and tokenizer saved to `output_folder` and/or pushed to Hub.

## Convert to Kohya

Package CLI:

```bash
autotrain tools convert_to_kohya \
  --input-path adapter_model.safetensors \
  --output-path adapter_kohya.safetensors
```

Standalone helper:

```bash
python skills/disco/autotrain-advanced/sub-skills/model-tools/scripts/convert_to_kohya.py \
  --input-path adapter_model.safetensors \
  --output-path adapter_kohya.safetensors
```

Inputs:

- `input_path` — safetensors LoRA state dict.
- `output_path` — destination safetensors path.

Output:

- Kohya-formatted safetensors state dict.

## Inspect tool help

```bash
python skills/disco/autotrain-advanced/scripts/inspect_cli.py tools --help
python skills/disco/autotrain-advanced/scripts/inspect_cli.py tools merge-llm-adapter --help
python skills/disco/autotrain-advanced/scripts/inspect_cli.py tools convert_to_kohya --help
```

## Route boundaries

- For LLM training configs and `--merge-adapter` as a training parameter, use `llm-training` first.
- For standalone artifact merge/conversion, stay in `model-tools`.
- For diffusion/LoRA training outside AutoTrain's utility command, use a more specific diffusion skill if available.
