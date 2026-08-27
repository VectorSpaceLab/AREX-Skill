# API reference for installed Otter inference

This reference is for future use with an installed `otter-ai` package. It is self-contained: do not depend on the original repository checkout for imports, prompts, or tensor-shape facts.

## Import and load surface

The package top level exports the two generation classes:

```python
from otter_ai import OtterForConditionalGeneration, FlamingoForConditionalGeneration
```

`OtterConfig` is available from the model configuration module, not from the package top level:

```python
from otter_ai.models.otter.configuration_otter import OtterConfig
```

Common Hugging Face loading pattern:

```python
import torch
from otter_ai import OtterForConditionalGeneration

model = OtterForConditionalGeneration.from_pretrained(
    checkpoint_or_model_id,
    device_map="auto",
    torch_dtype=torch.bfloat16,
)
model.eval()
tokenizer = model.text_tokenizer
tokenizer.padding_side = "left"
```

Use the same pattern for `FlamingoForConditionalGeneration` when the checkpoint is a Flamingo-format model. For OtterHD demo-style inference, the model surface is the Hugging Face `FuyuForCausalLM` plus the package's Fuyu processor; see [workflows](workflows.md#otterhd-fuyu-style-inference).

## Installed signatures

These signatures were verified from the installed package inspection environment:

| Object | Signature |
|---|---|
| `OtterConfig.__init__` | `(self, vision_config=None, text_config=None, cross_attn_every_n_layers: int = 4, use_media_placement_augmentation: bool = True, **kwargs)` |
| `OtterForConditionalGeneration.forward` | `(self, vision_x, lang_x, attention_mask=None, labels=None, use_cached_vision_x=False, clear_conditioned_layers=True, past_key_values=None, use_cache=False, **kwargs)` |
| `OtterForConditionalGeneration.generate` | `(self, vision_x, lang_x, attention_mask=None, **generate_kwargs)` |
| `FlamingoForConditionalGeneration.generate` | `(self, vision_x, lang_x, attention_mask=None, num_beams=1, max_new_tokens=None, temperature=1.0, top_k=0, top_p=1.0, no_repeat_ngram_size=0, prefix_allowed_tokens_fn=None, length_penalty=1.0, num_return_sequences=1, do_sample=False, early_stopping=False, **kwargs)` |

### Config notes

Prefer loading `OtterConfig` through `from_pretrained`, `from_json_file`, or a saved checkpoint directory. A bare `OtterConfig()` is not a reliable way to create a usable model because the text configuration must identify a language-model `model_type` or a supported architecture such as `MPTForCausalLM`, `MosaicGPT`, `RWForCausalLM`, or `LlamaForCausalLM` and often needs `_name_or_path` for tokenizer loading.

Important fields:

- `vision_config`: CLIP vision configuration dictionary or saved config content.
- `text_config`: language model configuration dictionary; must contain the architecture/model-type facts needed to instantiate the language encoder and tokenizer.
- `cross_attn_every_n_layers`: how often gated cross-attention layers are attached.
- `use_media_placement_augmentation`: present in config; Otter generation code sets media placement augmentation off internally for Otter.

## Prompt and media tensor contract

### Otter prompt templates

Use the exact image and no-image templates when reproducing the demo behavior:

```text
<image>User:{question} GPT:<answer>
User:{question} GPT:<answer>
```

The first form is for image-conditioned prompts. The second form is for no-image prompts. Otter tokenizer special tokens include `<|endofchunk|>`, `<image>`, and `<answer>`; output decoding commonly takes text after `<answer>` and removes `<|endofchunk|>`.

### Otter tensors

`vision_x` must be a 6-D tensor with shape:

```text
(batch, num_images_or_chunks, frames_per_image, channels, height, width)
```

For single-image inference from a PIL image and CLIP preprocessing, the shape is usually `(1, 1, 1, 3, 224, 224)`:

```python
import torch
from PIL import Image
from transformers import CLIPImageProcessor

image_processor = CLIPImageProcessor()
image = Image.open(image_path).convert("RGB")
vision_x = image_processor.preprocess([image], return_tensors="pt")["pixel_values"]
vision_x = vision_x.unsqueeze(1).unsqueeze(0)  # (1, 1, 1, 3, 224, 224)
vision_x = vision_x.to(dtype=next(model.parameters()).dtype)
```

For a no-image Otter prompt, the demo-compatible placeholder is a zero tensor with the same 6-D image shape:

```python
vision_x = torch.zeros(1, 1, 1, 3, 224, 224, dtype=next(model.parameters()).dtype)
```

Tokenize the formatted prompt and keep the attention mask:

```python
lang_x = tokenizer([formatted_prompt], return_tensors="pt")
input_ids = lang_x["input_ids"].to(model.device)
attention_mask = lang_x["attention_mask"].to(model.device)
```

Then generate:

```python
generated_ids = model.generate(
    vision_x=vision_x.to(model.device),
    lang_x=input_ids,
    attention_mask=attention_mask,
    max_new_tokens=512,
    temperature=0.2,
    do_sample=True,
    pad_token_id=tokenizer.pad_token_id,
)
answer = tokenizer.decode(generated_ids[0]).split("<answer>")[-1].strip()
answer = answer.replace("<|endofchunk|>", "")
```

### Flamingo tensors

Flamingo generation uses the same `vision_x`, `lang_x`, and `attention_mask` layout. If `num_beams > 1`, the model repeats `vision_x` across the beam dimension before conditioning the language model. Flamingo adds `<|endofchunk|>` and `<image>` special tokens; unlike Otter, it does not rely on `<answer>` as the output split marker unless the specific checkpoint/template adds it.

## Forward-pass notes

`forward` and `generate` first encode `vision_x`, condition the language model's gated cross-attention layers, then clear conditioned layers after the call by default. Use `use_cached_vision_x=True` only when the language encoder has already been conditioned and `vision_x` is deliberately omitted; otherwise provide `vision_x` for every call.

`labels` are for supervised loss and belong to training-style use. For inference, use `generate` and route training tasks to [training](../../training/SKILL.md).
