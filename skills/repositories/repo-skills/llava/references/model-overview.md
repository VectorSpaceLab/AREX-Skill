# Model and Checkpoint Overview

## When to read

Read this before choosing a LLaVA checkpoint, explaining merged versus adapter weights, or deciding which sub-skill owns a model-related task.

## Main checkpoint families

LLaVA provides public vision-language assistant checkpoints and related projector or delta artifacts. Common user-facing families include:

- LLaVA v1.6 merged checkpoints such as Vicuna 7B/13B, Mistral 7B, and 34B variants.
- LLaVA v1.5 merged checkpoints such as `liuhaotian/llava-v1.5-7b` and `liuhaotian/llava-v1.5-13b`.
- LLaVA v1.5 LoRA checkpoints such as `liuhaotian/llava-v1.5-7b-lora` and `liuhaotian/llava-v1.5-13b-lora`.
- Older LLaVA-v1, LLaMA-2, MPT, ScienceQA, projector, and delta-weight artifacts.

Checkpoint licenses follow their base language model and data terms. Always remind users to check the model card and base model license when downloading, training, merging, or redistributing weights.

## Merged, LoRA, projector, and delta artifacts

| Artifact type | What it means | Owning route |
| --- | --- | --- |
| Merged LLaVA checkpoint | Tokenizer, language model, vision tower/projector state packaged for direct loading | `chat-and-serve` for inference; `evaluate-and-benchmark` for benchmark runs |
| LoRA adapter | Adapter weights that usually require a matching `--model-base` for loading or merging | `train-and-finetune` for merge/troubleshooting; `chat-and-serve` for serving with `--model-base` |
| Projector weights | Multimodal projector weights used in pretraining or model construction | `train-and-finetune` |
| Delta weights | Difference from a base LLaMA/Vicuna-style model used to reconstruct target weights | `train-and-finetune` checkpoint utilities |

## Loading behavior to remember

The verified `load_pretrained_model` API returns `(tokenizer, model, image_processor, context_len)` and branches by model name and `model_base`:

- If `model_name` contains `llava` and `lora`, pass `model_base` for adapter loading and merge-unload behavior.
- If `model_base` is present but the model is not LoRA, the path may be a projector-only checkpoint; the loader reads `mm_projector.bin`.
- If the model name contains `mpt`, `mistral`, or LLaVA/Llama variants, the loader selects the corresponding LLaVA language-model wrapper.
- `load_4bit` and `load_8bit` control quantized loading; `use_flash_attn` requests FlashAttention 2 when installed and compatible.
- Non-LLaVA language model paths can still be loaded through the fallback, but this skill is not a generic Transformers skill.

## Routing examples

- "Run `liuhaotian/llava-v1.5-13b` on a local image" -> `chat-and-serve`.
- "Merge my LLaVA LoRA adapter into a base model" -> `train-and-finetune`.
- "Evaluate LLaVA v1.5 on MMBench and create upload file" -> `evaluate-and-benchmark`.
- "Apply LLaVA delta weights to a base LLaMA checkpoint" -> `train-and-finetune`.
- "Why does a LoRA path warn about missing `model_base`?" -> `chat-and-serve` for the symptom, then `train-and-finetune` for merge/base details.
