# API Reference for Chat and Serve

## Verified signatures

These signatures were checked from the installed package and should be treated as the runtime facts for this skill:

```python
load_pretrained_model(model_path, model_base, model_name, load_8bit=False, load_4bit=False, device_map='auto', device='cuda', use_flash_attn=False, **kwargs)
get_model_name_from_path(model_path)
process_images(images, image_processor, model_cfg)
tokenizer_image_token(prompt, tokenizer, image_token_index=-200, return_tensors=None)
run_llava.eval_model(args)
ModelWorker.__init__(self, controller_addr, worker_addr, worker_id, no_register, model_path, model_base, model_name, load_8bit, load_4bit, device, use_flash_attn=False)
```

## What the loader returns

`load_pretrained_model(...)` returns four values:

1. tokenizer
2. model
3. image_processor
4. context length

Use that order in all snippets and command templates in this sub-skill.

## Loading branches to remember

- LLaVA checkpoints with `lora` in the model name usually need `model_base`.
- Some checkpoints are projector-only and still require `model_base` to build the wrapper model before loading `mm_projector.bin`.
- `load_8bit` and `load_4bit` are mutually exclusive boolean flags in the public CLI flow.
- `use_flash_attn=True` requests FlashAttention 2, but only when that optional package is installed and the host backend is compatible.

## Conversation templates

The verified template keys available in `conv_templates` include:

- `llava_v0`
- `llava_v1`
- `llava_llama_2`
- `mistral_instruct`
- `chatml_direct`
- `mpt`
- `v0_mmtag`
- `v1_mmtag`
- `plain`
- plus the non-LLaVA templates used by the package's conversation module

Choose the template from the model family:

| Model family cue | Template |
| --- | --- |
| LLaVA v1 / Vicuna-style | `llava_v1` |
| LLaVA v0 | `llava_v0` |
| LLaMA-2 chat | `llava_llama_2` |
| Mistral instruct | `mistral_instruct` |
| Hermes / v1.6-34B style | `chatml_direct` |
| MPT | `mpt` |

## Image handling facts

- `run_llava` accepts either a local image path or an HTTP/HTTPS URL.
- `run_llava` streams a single answer in an input loop after prepending the image token to the first user message.
- The serving path receives images from the front end and converts them through `process_images` before calling `model.generate`.
- Some prompts use one `<image>` token per image, and the worker checks that the prompt and image list lengths match.
- `process_images` respects `model_cfg.image_aspect_ratio`; when the config is `pad`, the helper pads to square before preprocessing.

## What not to do

- Do not call `model.generate` without the expected image tensor when the prompt includes image tokens.
- Do not assume the same conv mode fits all checkpoints; the model name influences the default selection.
- Do not tell users that a server is available just because the CLI help imported successfully.
