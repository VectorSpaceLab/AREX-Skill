# Tokenizer And Processor Data Formats

This reference summarizes the input and output shapes agents should expect from Transformers tokenizer and processor workflows.

## Text Inputs

Accepted text forms commonly include:

- Single string: `tokenizer("hello")`.
- Batch of strings: `tokenizer(["hello", "world"], padding=True)`.
- Pair input: `tokenizer("question", "context")`.
- Batch of pairs: `tokenizer(list_a, list_b, padding=True, truncation=True)`.
- Pre-tokenized words: model/tokenizer-specific; pass the tokenizer option required by that class, such as `is_split_into_words=True` where supported.

Outputs are a `BatchEncoding`, usually with:

- `input_ids`: token ids.
- `attention_mask`: 1 for real tokens and 0 for padding when returned.
- `token_type_ids`: segment ids for models that use them.
- `special_tokens_mask`: 1 for inserted special tokens when requested.
- `offset_mapping`: character spans when requested and supported by fast tokenizers.

Batch tensor outputs should have consistent sequence length. If tensor conversion fails with uneven lengths, enable `padding=True` and/or `truncation=True`.

## Padding And Truncation Formats

Common strategies:

| Option | Meaning | Use when |
| --- | --- | --- |
| `padding=False` | no padding | single examples or ragged Python lists |
| `padding=True` or `"longest"` | pad to longest in batch | dynamic batching |
| `padding="max_length"` | pad to `max_length` | fixed-shape evaluation/export |
| `truncation=True` | truncate using default strategy | avoid overlong model inputs |
| `max_length=N` | cap or pad to N tokens | fixed limits or model max length |
| `pad_to_multiple_of=N` | round padded length to multiple | accelerator-friendly shapes |

Check `tokenizer.padding_side` and `tokenizer.truncation_side` when decoder-only generation, packed prompts, or left-padding behavior matters.

## Chat Message Format

Tokenizer chat templates usually accept:

```python
messages = [
    {"role": "system", "content": "You are helpful."},
    {"role": "user", "content": "Write one sentence."},
    {"role": "assistant", "content": "Sure."},
]
```

Common role names are `system`, `user`, and `assistant`, but templates may define additional roles for tools, observations, or model-specific channels. Validate against errors and rendered output rather than assuming universal role support.

Chat template output choices:

- `tokenize=False`: returns formatted text.
- `tokenize=True`: returns ids, tensors, or encoded fields depending on other options.
- `add_generation_prompt=True`: prepares a new assistant response.
- `continue_final_message=True`: continues the final message; incompatible with `add_generation_prompt=True`.
- `return_dict=True`: returns a dictionary-like object where supported.

Avoid special-token duplication by using `tokenize=True` inside `apply_chat_template`, or by passing `add_special_tokens=False` when tokenizing a string returned from `tokenize=False`.

## Multimodal Chat Format

Multimodal processors may accept message content as a list of chunks rather than plain strings. A typical schema is model-specific but often resembles:

```python
messages = [
    {
        "role": "user",
        "content": [
            {"type": "image"},
            {"type": "text", "text": "Describe the image."},
        ],
    }
]
```

Do not assume the exact keys for every model. Inspect the processor's behavior, examples embedded in the model card if available to the user, or error messages. Keep runtime skills self-contained by documenting the schema you use in the downstream project rather than linking to source checkout examples.

## Processor Inputs By Modality

### Text plus image

Typical call:

```python
inputs = processor(
    text=["Describe this image."],
    images=[image],
    padding=True,
    return_tensors="pt",
)
```

Possible output keys:

- `input_ids`
- `attention_mask`
- `pixel_values`
- `pixel_mask`
- image size metadata or model-specific fields

### Vision-only image processor

Typical call:

```python
inputs = image_processor(images=image_or_batch, return_tensors="pt")
```

Possible output keys:

- `pixel_values`
- `pixel_mask`
- `original_sizes`, `reshaped_input_sizes`, or other task-specific metadata for detection/segmentation processors

The image object may be a PIL image, NumPy array, tensor, path-like object, or backend-specific type depending on processor support and installed packages. Validate accepted types in a minimal call.

### Audio processor or feature extractor

Typical call:

```python
inputs = processor(audio_array, sampling_rate=16000, return_tensors="pt")
```

Possible output keys:

- `input_features`
- `input_values`
- `attention_mask`

Always pass the correct `sampling_rate` when the processor requires it. Optional dependencies such as audio loading libraries or PyTorch may be needed for full workflows.

### Video processor

Video processors are model-specific. Typical inputs can be decoded frames, arrays, or video objects. Expected outputs may include video pixel tensors, frame metadata, or masks. Validate returned keys before passing to generation or pipeline workflows.

## Special Token Data

Special tokens are stored in tokenizer configuration and maps. Common attributes include:

- `bos_token`, `bos_token_id`
- `eos_token`, `eos_token_id`
- `unk_token`, `unk_token_id`
- `sep_token`, `sep_token_id`
- `pad_token`, `pad_token_id`
- `cls_token`, `cls_token_id`
- `mask_token`, `mask_token_id`
- `additional_special_tokens`
- model-specific tokens registered through `extra_special_tokens`

Validation snippet:

```python
for name, value in tokenizer.special_tokens_map.items():
    print(name, value)
print(tokenizer.all_special_tokens)
print(tokenizer.all_special_ids)
```

When adding special tokens for multimodal placeholders, record both token strings and ids. If ids are new and a model uses them, the model embedding table must be resized by the owner workflow.

## Saved Artifact Formats

Tokenizer directories can contain several files depending on backend and model:

- `tokenizer_config.json`
- `special_tokens_map.json`
- `tokenizer.json`
- vocabulary files such as `vocab.json`, `vocab.txt`, or `merges.txt`
- SentencePiece models such as `.model`
- added-token metadata
- chat template files such as `chat_template.jinja` or multiple templates in a chat-template directory

Processor directories can contain:

- `preprocessor_config.json`
- tokenizer files when the processor wraps a tokenizer
- feature extractor or image processor configs
- processor config files
- chat template files
- model-specific processor assets

Portability rule: a future agent should be able to reload the saved tokenizer or processor with `from_pretrained(saved_dir, local_files_only=True)` without opening original repository files.

## Handoff Formats To Sibling Skills

When handing off to generation, training, or pipelines, include:

- `model_or_path` or saved preprocessing directory.
- Tokenizer/processor class name and `is_fast` value when relevant.
- Padding/truncation/max-length policy.
- Chat template choice and whether prompts are already tokenized.
- Added special tokens and `added` count.
- Whether model embedding resize is required.
- Output keys from a representative encoded example.
- Optional dependencies that were missing or required.
