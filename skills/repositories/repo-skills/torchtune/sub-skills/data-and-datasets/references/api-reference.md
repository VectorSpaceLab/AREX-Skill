# Data and Dataset API Reference

This reference lists the practical signatures and outputs future agents need when configuring torchtune data pipelines.

## `torchtune.data`

### `Message`

```python
Message(role, content, masked=False, ipython=False, eot=True)
Message.from_dict(d)
```

- `role`: one of `system`, `user`, `assistant`, `ipython`, or `tool`.
- `content`: text string or a list of content dictionaries.
- Text content item: `{"type": "text", "content": "..."}`.
- Image content item after loading: `{"type": "image", "content": PIL.Image.Image}` or model-transform-compatible image object.
- Useful properties: `text_content`, `contains_media`, `get_media()`.
- `ipython=True` is only valid on assistant messages and cannot contain media.
- `eot=False` is used for tool-call turns where control has not returned to the user.

### Validation and Masking

```python
validate_messages(messages)
mask_messages(messages, masking_strategy)
```

`validate_messages` raises `ValueError` for invalid conversation order. `mask_messages` mutates each `Message.masked` flag using one of `train_on_all`, `train_on_assistant`, or `train_on_last`.

### Message Transforms

```python
InputOutputToMessages(
    train_on_input=None,
    column_map=None,
    new_system_prompt=None,
    image_dir=None,
    masking_strategy="train_on_assistant",
)
```

Input row defaults: `input`, `output`, and optional `image`. Returns `{"messages": [...]}`. If `image_dir` is set, `column_map` must include `image`.

```python
ChosenRejectedToMessages(
    train_on_input=None,
    column_map=None,
    new_system_prompt=None,
    masking_strategy="train_on_assistant",
)
```

Input row defaults: `chosen` and `rejected`, each a list of message dictionaries. Returns `{"chosen": [...], "rejected": [...]}`. `new_system_prompt` replaces existing system messages.

```python
ShareGPTToMessages(
    train_on_input=None,
    column_map=None,
    new_system_prompt=None,
    image_dir=None,
    image_tag="<image>",
    masking_strategy="train_on_assistant",
)
```

Input row defaults: `conversations` with `from`/`value`, and optional `image`. Role mapping is `system -> system`, `human -> user`, and `gpt -> assistant`. For multimodal rows, the image is loaded once into the first user message; `image_tag=None` prepends the image.

```python
OpenAIToMessages(
    train_on_input=None,
    column_map=None,
    new_system_prompt=None,
    masking_strategy="train_on_assistant",
)
```

Input row default: `messages` with `role`/`content`. Supports string content and OpenAI content lists containing text and `image_url` items. Handles `tool`/`ipython` turn boundaries.

```python
AlpacaToMessages(
    train_on_input=None,
    column_map=None,
    masking_strategy="train_on_all",
)
```

Input row defaults: `instruction`, optional `input`, and `output`. It embeds the Alpaca prompt wording itself, so do not add a second Alpaca prompt template in the tokenizer.

### Prompt Templates and Utilities

```python
PromptTemplate(template)
ChatMLTemplate()
GrammarErrorCorrectionTemplate()
QuestionAnswerTemplate()
SummarizeTemplate()
load_image(path_or_url)
format_content_with_images(text, image_tag, images)
truncate(tokens, max_seq_len)
```

`PromptTemplate` maps each role to `(prepend_tag, append_tag)`. Model-specific tokenizer constructors often accept a prompt-template component path; ensure it matches the target model tokenizer from [models-and-modules](../../models-and-modules/SKILL.md).

### Collators

```python
padded_collate_sft(batch, padding_idx=0, ignore_idx=-100, pad_to_multiple_of=1, stack_on_new_dim=False, cp_degree=1)
padded_collate_dpo(batch, padding_idx=0, ignore_idx=-100)
padded_collate_packed(batch)
padded_collate_tiled_images_and_mask(batch, padding_idx=0, ignore_idx=-100)
padded_collate(batch, *, pad_direction, keys_to_pad, padding_idx, pad_to_multiple_of=1, stack_on_new_dim=False)
left_pad_sequence(sequences, batch_first=False, padding_value=0)
```

Use `padded_collate_sft` for samples with `tokens` and `labels`. Use `padded_collate_dpo` for preference samples with `chosen_input_ids`, `chosen_labels`, `rejected_input_ids`, and `rejected_labels`. `padded_collate` rejects unsupported `pad_direction`, empty `keys_to_pad`, mismatched key sets, and left padding with `pad_to_multiple_of > 1`.

## `torchtune.datasets`

### Core Classes

```python
SFTDataset(*, source, message_transform, model_transform, filter_fn=None, filter_kwargs=None, **load_dataset_kwargs)
```

Loads data with `datasets.load_dataset`, applies `message_transform`, validates `messages` when present, then applies `model_transform`. The model transform must return `tokens` and `mask`; labels are built by shifting tokens and replacing masked positions with `CROSS_ENTROPY_IGNORE_IDX`.

```python
PreferenceDataset(*, source, message_transform, tokenizer, filter_fn=None, packed=False, **load_dataset_kwargs)
```

Tokenizes chosen and rejected message lists and returns `chosen_input_ids`, `chosen_labels`, `rejected_input_ids`, and `rejected_labels`. `packed=True` raises `ValueError`.

```python
TextCompletionDataset(tokenizer, source, column="text", add_eos=True, filter_fn=None, **load_dataset_kwargs)
```

Encodes free text with BOS and optional EOS, truncates to tokenizer `max_seq_len - 1` when set, and returns `tokens` plus shifted `labels`.

```python
PackedDataset(ds, *, max_seq_len, padding_idx=0, max_packs=None, split_across_pack=False)
ConcatDataset(datasets)
```

`PackedDataset` requires child samples with `tokens` and `labels`. `ConcatDataset` rejects mixing packed and non-packed datasets.

### Builder Functions

```python
alpaca_dataset(tokenizer, *, source="tatsu-lab/alpaca", column_map=None, train_on_input=True, packed=False, split="train", **load_dataset_kwargs)
alpaca_cleaned_dataset(tokenizer, *, source="yahma/alpaca-cleaned", ...)
```

Alpaca-style instruction rows using `AlpacaToMessages`.

```python
instruct_dataset(tokenizer, *, source, column_map=None, train_on_input=False, new_system_prompt=None, packed=False, filter_fn=None, split="train", **load_dataset_kwargs)
```

Input/output SFT rows using `InputOutputToMessages`.

```python
chat_dataset(tokenizer, *, source, conversation_column, conversation_style, train_on_input=False, new_system_prompt=None, packed=False, filter_fn=None, split="train", **load_dataset_kwargs)
```

Conversation SFT rows. `conversation_style` must be `sharegpt` or `openai`.

```python
preference_dataset(tokenizer, *, source, column_map=None, train_on_input=False, new_system_prompt=None, filter_fn=None, split="train", **load_dataset_kwargs)
```

Preference rows using `ChosenRejectedToMessages`; no packing.

```python
text_completion_dataset(tokenizer, source, column="text", add_eos=True, packed=False, split_across_pack=True, split="train", filter_fn=None, **load_dataset_kwargs)
```

Free text rows. When `packed=True`, wraps in `PackedDataset` with `split_across_pack`.

Additional convenience builders include `grammar_dataset`, `samsum_dataset`, `slimorca_dataset`, `hh_rlhf_helpful_dataset`, `stack_exchange_paired_dataset`, `cnn_dailymail_articles_dataset`, and `wikitext_dataset`; inspect their defaults when using a named source-specific dataset.

## `torchtune.datasets.multimodal`

```python
multimodal_chat_dataset(
    model_transform,
    *,
    source,
    column_map=None,
    new_system_prompt=None,
    packed=False,
    image_tag=None,
    image_dir=None,
    filter_fn=None,
    split="train",
    **load_dataset_kwargs,
)
```

ShareGPT-style text+image chat rows. `packed=True` raises `ValueError`.

```python
vqa_dataset(
    model_transform,
    *,
    source,
    image_dir=None,
    column_map=None,
    new_system_prompt=None,
    packed=False,
    filter_fn=None,
    split="train",
    **load_dataset_kwargs,
)
```

Question/image/answer rows using `InputOutputToMessages`. `packed=True` raises `ValueError`.

```python
llava_instruct_dataset(...)
the_cauldron_dataset(...)
the_cauldron_transform(...)
```

Specialized multimodal dataset helpers. Keep the model transform and image preprocessing aligned with the VLM family.

## Recipe Boundary

Dataset config objects are consumed by recipes selected through the `tune` CLI. Recipe modules are intentionally not an importable `recipes` package. For copying, inspecting, validating, or launching recipe configs, use `tune cp`, `tune cat`, `tune validate`, and `tune run` through [cli-and-config](../../cli-and-config/SKILL.md) and recipe guidance through [post-training-recipes](../../post-training-recipes/SKILL.md).
