# Training Data Formats

## When to read

Read this before building a training command or validating a custom dataset.

## LLaVA training JSON schema

The public training shape used by LLaVA is a JSON list of samples. Each sample typically contains:

- `id`: unique sample id
- `image`: image path relative to the chosen image root, or omitted for text-only samples
- `conversations`: a list of turns

A turn is usually an object with:

- `from`: `human` or `gpt`
- `value`: text content

### Multimodal example

```json
[
  {
    "id": "sample-001",
    "image": "images/sample-001.jpg",
    "conversations": [
      {"from": "human", "value": "<image>\nDescribe this image."},
      {"from": "gpt", "value": "..."}
    ]
  }
]
```

## Rules that matter for validation

- Conversations should alternate between human and gpt turns.
- The first meaningful message is usually human.
- Multimodal samples should include `<image>` in the human message where the image should be grounded.
- The `image` path must exist when the workflow expects an image folder.
- For ScienceQA conversion, the output format also uses `id`, `image` when present, and `conversations` with a human prompt that includes `<image>` for image-backed questions.

## ScienceQA conversion notes

The bundled ScienceQA conversion workflow turns the source problems into LLaVA-style conversation JSON. The converted entries may be text-only or multimodal depending on whether the original problem has an image.

Use the converter when you need a dataset that the LLaVA training script can read directly instead of manually editing raw ScienceQA files.

## What the validator should catch

- non-list top-level JSON
- missing `id` or `conversations`
- `conversations` entries that are not objects
- invalid `from` speaker labels
- missing `value`
- image path mismatches when an image folder is expected
- malformed multimodal prompts that omit `<image>` when needed
