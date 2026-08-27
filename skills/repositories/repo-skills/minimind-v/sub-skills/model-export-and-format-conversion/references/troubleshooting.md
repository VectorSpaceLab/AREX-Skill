# Export and Conversion Troubleshooting

## Missing state dict

Symptoms: conversion cannot find `.pth`, dense/MoE path mismatch, or `torch.load` fails.

Recovery: confirm checkpoint prefix, hidden size, and `_moe` suffix; route missing weights to `data-and-resources` or `training`.

## `strict=False` surprises

The conversion loads state dicts with `strict=False`; this can hide architecture mismatch. If export loads but behaves poorly, compare key families with expected dense/MoE, projector, and tied embedding keys.

## Missing tokenizer

Ensure `model/tokenizer.json` and `model/tokenizer_config.json` exist before conversion and are copied into the export. For Transformers 5, inspect tokenizer class and `extra_special_tokens` metadata.

## Missing vision encoder

`MiniMindVLM.get_vision_model()` can return `(None, None)` when SigLIP2 is missing or incompatible. The exported Transformers directory may still lack a usable image encoder because conversion deletes `vision_encoder` before saving. Route runtime image failures to `inference-and-serving` and resource setup to `data-and-resources`.

## Transformers metadata issues

Warnings around RoPE, tokenizer class, or custom code usually mean the post-save JSON edits were not applied or the export was manually repackaged. Use `inspect_transformers_export.py` first; it does not load weights.

## Reverse conversion limits

Reverse conversion saves only model parameters. It does not restore optimizer, scaler, epoch, step, checkpoint-resume metadata, or missing SigLIP2 resources. Do not use it as a training-resume recovery path.
