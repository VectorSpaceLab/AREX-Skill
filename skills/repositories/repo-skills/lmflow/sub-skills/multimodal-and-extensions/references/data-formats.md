# Multimodal Data Formats

## Legacy Training Dataset: `custom_multi_modal`

The legacy multimodal training backend loads a JSON array, not the standard LMFlow `{"type": ..., "instances": ...}` wrapper.

Each sample usually looks like:

```json
{
  "image": "000001.jpg",
  "conversations": [
    { "from": "human", "value": "<image>\nDescribe the picture." },
    { "from": "gpt", "value": "A dog on a beach." }
  ]
}
```

### Required Fields

- `conversations`: ordered list of message objects.
- `from`: usually `human` / `gpt`.
- `value`: message text.

### Optional Fields

- `image`: filename relative to `image_folder`.

### Preprocess Notes

- The loader inserts or normalizes `<image>` markers before tokenization.
- `use_image_start_end` wraps `<image>` with `<im_start>` and `<im_end>`.
- `sep_style="plain"` expects a simple two-turn prompt-answer pair.
- `sep_style="v1"` expects an alternating LLaVA-style conversation.

## Inference Payload: `image_text`

The visual chatbot path uses the regular LMFlow dataset API with:

```python
{
    "type": "image_text",
    "instances": [
        {
            "images": <stacked image batch>,
            "text": "Prompt text with image markers"
        }
    ]
}
```

This payload is usually built in code rather than stored as a JSON file.

## Image Handling

- `image_folder` points to the directory that contains the referenced files.
- `image_aspect_ratio="pad"` pads non-square images before preprocessing.
- If a sample has no image, the loader can fall back to a zero image tensor for compatibility.
- If a batch has mixed image shapes, the collator may keep a list rather than stack tensors.
