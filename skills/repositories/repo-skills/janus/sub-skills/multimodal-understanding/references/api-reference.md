# Multimodal Understanding API Reference

## Purpose

Read this when adapting Janus-family understanding code or debugging the processor/model interface.

## Public imports

For Janus and Janus-Pro:

```python
from transformers import AutoModelForCausalLM
from janus.models import MultiModalityCausalLM, VLChatProcessor
from janus.utils.io import load_pil_images
```

For JanusFlow understanding:

```python
from janus.janusflow.models import MultiModalityCausalLM, VLChatProcessor
from janus.utils.io import load_pil_images
```

## Verified signatures

### `VLMImageProcessor`

```python
VLMImageProcessor(
    image_size: int,
    min_size: int = 14,
    image_mean=(0.48145466, 0.4578275, 0.40821073),
    image_std=(0.26862954, 0.26130258, 0.27577711),
    rescale_factor=1 / 255,
    do_normalize=True,
    **kwargs,
)
```

Important behavior:

- Resizes the image while preserving aspect ratio.
- Pads to a square using the configured background color.
- Returns channel-first pixel values with shape `[3, image_size, image_size]` before batching.
- Requires `torchvision` because resizing uses `torchvision.transforms.functional`.

### `VLChatProcessor`

For Janus / Janus-Pro:

```python
VLChatProcessor(
    image_processor,
    tokenizer,
    image_tag="<image_placeholder>",
    image_start_tag="<begin_of_image>",
    image_end_tag="<end_of_image>",
    pad_tag="<｜▁pad▁｜>",
    num_image_tokens=576,
    add_special_token=False,
    sft_format="deepseek",
    mask_prompt=True,
    ignore_id=-100,
    **kwargs,
)
```

For JanusFlow the constructor also has:

```python
image_gen_tag="<｜begin▁of▁generation｜>"
```

The callable interface is:

```python
vl_chat_processor(
    *,
    prompt=None,
    conversations=None,
    images=None,
    force_batchify=True,
    **kwargs,
)
```

Use either `prompt` or `conversations`, not both. The processor asserts if both are provided.

### Processor output

With `force_batchify=True`, the output has dictionary-like attributes:

- `sft_format`: formatted prompt text.
- `input_ids`: padded input token ids.
- `pixel_values`: image tensor batch.
- `attention_mask`: token attention mask.
- `images_seq_mask`: positions where image embeddings replace token embeddings.
- `images_emb_mask`: image embedding mask.

The output has a `.to(device, dtype=...)` method that moves token masks and image tensors. Pass a floating dtype appropriate for the model/device.

### `load_pil_images`

```python
load_pil_images(conversations) -> list[PIL.Image.Image]
```

The helper scans messages for an `images` field and supports:

- Local image file paths.
- `data:image/...;base64,...` URIs.

It converts loaded images to RGB.

### `MultiModalityCausalLM.prepare_inputs_embeds`

```python
prepare_inputs_embeds(
    input_ids,
    pixel_values,
    images_seq_mask,
    images_emb_mask,
    **kwargs,
)
```

The method runs the vision encoder, aligns image embeddings to the language model embedding dimension, and replaces placeholder-token embeddings at positions selected by `images_seq_mask`.

## Generation call pattern

After preparing inputs, run language generation with:

```python
outputs = vl_gpt.language_model.generate(
    inputs_embeds=inputs_embeds,
    attention_mask=prepare_inputs.attention_mask,
    pad_token_id=tokenizer.eos_token_id,
    bos_token_id=tokenizer.bos_token_id,
    eos_token_id=tokenizer.eos_token_id,
    max_new_tokens=512,
    do_sample=False,
    use_cache=True,
)
answer = tokenizer.decode(outputs[0].cpu().tolist(), skip_special_tokens=True)
```

For sampling, use `temperature` and `top_p` together with `do_sample=True`.

## Role and template notes

The repo examples are not fully uniform:

- Janus examples use `"User"` and `"Assistant"` in older snippets.
- Janus-Pro examples use `<|User|>` and `<|Assistant|>`.
- The processor's `sft_format` decides the conversation template.

If output quality is poor or the model echoes the prompt, inspect `prepare_inputs["sft_format"][0]` before changing generation parameters.
