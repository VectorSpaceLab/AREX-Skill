# Transformers Export Layout

## Expected input layout

```text
model/
  siglip2-base-p32-256-ve/
    config.json
    model.safetensors
    preprocessor_config.json
  tokenizer.json
  tokenizer_config.json
out/
  sft_vlm_768_moe.pth
```

Dense checkpoints normally omit `_moe`; MoE checkpoints include it. Match checkpoint names to `VLMConfig.use_moe`.

## Expected output directory

A MiniMind-V Transformers export normally contains:

```text
minimind-3v-moe/
  config.json
  tokenizer.json
  tokenizer_config.json
  special_tokens_map.json
  generation_config.json
  modeling_*.py / configuration_*.py or auto_map metadata
  pytorch_model.bin or shard index
```

The native conversion passes `safe_serialization=False`, so `.bin` weights are expected by default, although later exports may use safetensors.

## Config fields to inspect

- `model_type`: expected `minimind-v`.
- `tie_word_embeddings`: expected `true`.
- `auto_map`: helpful for custom-code loading.
- `image_special_token`: expected `<|image_pad|>`.
- `image_ids`: expected to include `12` for the native default.
- `image_hidden_size`: expected `768` for SigLIP2-base features.
- `image_token_len`: expected `64`.
- `use_moe`: should match checkpoint/export naming.
- Transformers 5 compatibility should avoid stale `rope_parameters` and include appropriate `rope_theta`/`rope_scaling` fields.

## Tokenizer fields

A usable export should include `tokenizer.json` and `tokenizer_config.json`. For Transformers 5 compatibility, `tokenizer_config.json` should include `tokenizer_class: PreTrainedTokenizerFast` and `extra_special_tokens: {}`.

## SigLIP2 expectation

The conversion initializes the VLM with SigLIP2, then deletes `vision_encoder` before saving. A Transformers directory can be loadable as a causal LM and still be incomplete for image-conditioned VLM inference unless SigLIP2 is available at runtime.

## Static inspection

Run the bundled helper:

```bash
python path/to/inspect_transformers_export.py --export-dir minimind-3v-moe
```

The helper reads small JSON files and filenames only. It does not import Transformers, execute custom code, download resources, or load weights.
