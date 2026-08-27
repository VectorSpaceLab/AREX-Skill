# MiniMind-V Conversion Workflows

## Native to Transformers

The conversion flow registers `VLMConfig` and `MiniMindVLM` for Transformers auto classes, creates `MiniMindVLM(lm_config, vision_model_path='../model/siglip2-base-p32-256-ve')`, loads a native `.pth` state dict with `strict=False`, casts to a dtype such as `torch.bfloat16`, deletes `vision_encoder`, saves with `save_pretrained(..., safe_serialization=False)`, saves tokenizer files from `model/`, and patches metadata such as `tie_word_embeddings`.

Transformers major version 5 compatibility edits include setting tokenizer class to `PreTrainedTokenizerFast`, adding `extra_special_tokens: {}`, setting `rope_theta`, nulling `rope_scaling`, and removing stale `rope_parameters`.

## Inputs needed for real conversion

- A native checkpoint such as `out/sft_vlm_768.pth` or `out/sft_vlm_768_moe.pth`.
- Source model classes and compatible torch/transformers.
- Tokenizer files under `model/`.
- SigLIP2 under `model/siglip2-base-p32-256-ve/` for initialization.
- A `VLMConfig` matching the checkpoint architecture, especially `hidden_size`, `num_hidden_layers`, and `use_moe`.

## Dense vs MoE

Default conversion code examples often use `use_moe=True` and `out/sft_vlm_768_moe.pth`. Dense exports should use `use_moe=False` and dense checkpoint names such as `out/sft_vlm_768.pth`. Do not mix dense checkpoint keys with a MoE config.

## Reverse conversion

Reverse conversion loads `AutoModelForCausalLM.from_pretrained(transformers_path, trust_remote_code=True)` and saves `model.state_dict()`. It does not recover optimizer state, resume metadata, training epoch/step, data preprocessing state, or missing SigLIP2 resources.

## Safe workflow

1. Use `inspect_transformers_export.py` for static checks before loading custom code.
2. Ask the user whether they trust the exported custom code before loading.
3. Only run full conversion when weights/resources are present and the user approves the runtime cost.
4. After conversion, route generation validation to `inference-and-serving`.
