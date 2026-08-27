---
name: inference
description: "Operate direct Qwen-VL, Qwen-VL-Chat, and Qwen-VL-Chat-Int4
  multimodal inference, chat, generation, grounding, and quantization-aware
  loading."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NOASSERTION
---

# Qwen-VL Inference

Use this sub-skill when the user wants direct local inference with Qwen-VL-family checkpoints through Transformers or ModelScope: multimodal chat, base-model generation, multi-image prompts, grounding markup, box rendering, generation settings, device placement, or Int4 caveats.

## Fast routing

- For one-off chat/VQA/grounding: follow [references/workflows.md](references/workflows.md) and the helper in [scripts/qwen_vl_chat_example.py](scripts/qwen_vl_chat_example.py).
- For exact API names, model IDs, prompt markup, and box-cleaning snippets: use [references/api-reference.md](references/api-reference.md).
- For model mismatch, CPU-only, package, remote-code, quantization, and bounding-box failures: use [references/troubleshooting.md](references/troubleshooting.md).
- Route server launch, OpenAI-compatible API, Gradio, streaming/service behavior to the `serving` sub-skill.
- Route adapter training, LoRA/Q-LoRA, data preparation, DeepSpeed, and checkpoint merging to the `finetuning` sub-skill.
- Route official benchmark datasets, scoring, and submission files to the `evaluation` sub-skill.

## Non-negotiable inference rules

1. Load Qwen-VL custom code with `trust_remote_code=True` unless the model has already been audited and packaged locally. Without it, the custom tokenizer/model methods used below are unavailable.
2. Use `Qwen/Qwen-VL-Chat` or `Qwen/Qwen-VL-Chat-Int4` for assistant-style `model.chat(...)`. Use `Qwen/Qwen-VL` as a pretrained base model with `model.generate(...)`, not as a chat assistant.
3. Build multimodal inputs with `tokenizer.from_list_format([...])` or explicit `<img>...</img>` tags. Accept user-provided image paths or URLs; do not rely on bundled demo assets.
4. For grounding, preserve the raw response containing `<ref>`, `<box>`, and optional `<quad>` tags if the user needs coordinates. Only clean these tags when the user asks for plain text.
5. Draw boxes with `tokenizer.draw_bbox_on_latest_picture(response, history)` for chat responses, and with `tokenizer.draw_bbox_on_latest_picture(response)` for base-model generated responses.
6. CPU-only loading is a functional fallback but is typically slow for this 7B multimodal model. Prefer CUDA with `device_map="cuda"` or `device_map="auto"` when available.
7. Int4 inference is optional and depends on AutoGPTQ/optimum-compatible installation. If those extras are absent, use the non-quantized chat model or ask the user to prepare the quantization stack.

## Minimal command pattern

```bash
python scripts/qwen_vl_chat_example.py \
  --model-id Qwen/Qwen-VL-Chat \
  --image image.jpg \
  --prompt "Describe the image and return boxes for the main objects" \
  --device-map cuda \
  --output-image boxes.jpg
```

Use `python scripts/qwen_vl_chat_example.py --help` for safe parameter details. The helper does nothing unless invoked explicitly.
