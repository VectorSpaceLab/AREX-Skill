# Tokenizers And Processors API Reference

This reference distills the tokenizer and processor APIs inspected for Transformers 5.13.0.dev0. It is written for agents that need practical decisions, expected signals, and safe validation checks.

## Loading APIs

### `AutoTokenizer.from_pretrained(...)`

Use `AutoTokenizer.from_pretrained(pretrained_model_name_or_path, *inputs, **kwargs)` for most tokenizer loading. The first argument can be a local directory, local tokenizer file for supported classes, or Hub id.

High-value options:

- `local_files_only=True`: do not access the network; use for smoke checks and reproducible automation.
- `use_fast=True` or `False`: request Rust/tokenizers-backed behavior or a Python/slow tokenizer when available.
- `trust_remote_code=False`: default safe posture; set `True` only with explicit user approval for custom repo code.
- `revision=...`: pin a Hub branch, tag, or commit when remote access is approved.
- `token=...`: use an access token for gated/private repos; never hard-code tokens in skill content or scripts.
- `extra_special_tokens={"image_token": "<image>"}`: register named multimodal placeholders during load.
- Class-specific options: pass only when the tokenizer documentation or local config proves support.

Expected signals after loading:

```python
print(type(tokenizer).__name__)
print(tokenizer.is_fast)
print(tokenizer.special_tokens_map)
print(len(tokenizer))
```

If the tokenizer cannot load locally, check whether the directory contains tokenizer metadata (`tokenizer_config.json`, `special_tokens_map.json`, backend model files such as `tokenizer.json`, vocab/merges, SentencePiece models, or model-specific files).

### Tokenizer backends

Transformers v5 tokenizers can use multiple backends:

- `tokenizers`: default fast Rust backend for many models.
- `sentencepiece`: required by some model tokenizers.
- Python backend: used by model-specific logic that cannot be represented by a fast backend.
- `mistral-common`: used by Mistral/Pixtral-style tokenizers when installed; otherwise fallback behavior may apply.
- `tiktoken`: used by tokenizers that import or convert tiktoken assets.

Do not assume a backend is installed from a base `transformers` import. Optional dependency errors are normal in minimal environments.

### `AutoProcessor.from_pretrained(...)`

Use `AutoProcessor.from_pretrained(...)` when a model has a coupled preprocessing contract, such as text+image, text+audio, OCR, speech, or video-language models.

Expected attributes vary by model. Common components include:

- `processor.tokenizer`
- `processor.image_processor`
- `processor.feature_extractor`
- `processor.video_processor`
- `processor.chat_template`

Validate with `hasattr(...)` rather than assuming all components exist.

### `AutoImageProcessor.from_pretrained(...)`

Use `AutoImageProcessor.from_pretrained(...)` for vision preprocessing without tokenizer coupling. Important options:

- `backend="torchvision"`: choose torchvision-backed processing where supported.
- `backend="pil"`: choose PIL-backed processing for older models that support it.
- omitted `backend`: chooses an available backend according to model support and installed packages.

Image processors subclass an image processing mixin with `from_pretrained(...)` and `save_pretrained(...)` behavior. Backend availability may depend on optional packages.

## Encoding APIs

### Tokenizer call

`tokenizer(text, text_pair=None, **kwargs)` returns a `BatchEncoding`. Common options:

- `add_special_tokens=True`: include model BOS/EOS/SEP/CLS and other structural tokens.
- `padding=False`, `True`, `"longest"`, or `"max_length"`: control padding strategy.
- `truncation=False`, `True`, `"longest_first"`, `"only_first"`, or `"only_second"`: control truncation strategy.
- `max_length=...`: required for fixed-length truncation/padding decisions.
- `pad_to_multiple_of=...`: useful for accelerator-friendly tensor shapes when padding is active.
- `return_attention_mask=True`: usually required by models with padding.
- `return_special_tokens_mask=True`: debug where special tokens were inserted.
- `return_offsets_mapping=True`: get character offset spans; requires fast-tokenizer support.
- `return_tensors="pt"`, `"np"`, etc.: request framework tensors only when that dependency is installed.
- `padding_side="left"` or `"right"`: override side where supported, especially for decoder-only generation batches.

Expected `BatchEncoding` keys depend on model and options. Text encoders usually include `input_ids`; batched/padded encoders usually include `attention_mask`; paired inputs may include `token_type_ids`; debugging options add masks or offsets.

### `BatchEncoding` behavior

`BatchEncoding` wraps encoded outputs and may expose fast alignment methods when backed by a fast tokenizer.

Common checks:

```python
encoding = tokenizer("Hello world", return_offsets_mapping=True)
print(encoding.keys())
print(encoding["input_ids"])
print(encoding.tokens() if hasattr(encoding, "tokens") else None)
```

Fast-tokenizer alignment helpers can include:

- `tokens()`
- `word_ids()`
- `sequence_ids()`
- `char_to_token(...)`
- `token_to_chars(...)`
- `token_to_word(...)`
- `word_to_tokens(...)`

Slow/Python tokenizers may not support the same offset and word alignment behavior. For exact span tasks, require `tokenizer.is_fast` and assert that `return_offsets_mapping=True` succeeds.

### Decode APIs

Use decoding to validate round trips and postprocessing:

```python
ids = tokenizer("Hello world")["input_ids"]
print(tokenizer.decode(ids, skip_special_tokens=False))
print(tokenizer.decode(ids, skip_special_tokens=True))
```

Decision points:

- `skip_special_tokens=True`: strip structural and registered special tokens for user-facing text.
- `clean_up_tokenization_spaces`: remove tokenization artifacts around punctuation where appropriate.
- `batch_decode(...)`: use for batched model outputs.

## Special Tokens

### Adding special tokens

Use `tokenizer.add_special_tokens(...)` when the tokenizer must recognize new control tokens:

```python
added = tokenizer.add_special_tokens({
    "additional_special_tokens": ["<image>", "<video>"],
})
print(added, len(tokenizer))
```

Use `extra_special_tokens=...` during load to register model-specific named tokens:

```python
tokenizer = AutoTokenizer.from_pretrained(
    model_or_path,
    extra_special_tokens={"image_token": "<image>"},
)
```

Important boundary: if a model will consume newly added token ids, a model-side embedding resize is required. This sub-skill detects and explains that need; route the actual resize to `../model-extension/SKILL.md`, `../training/SKILL.md`, or `../generation/SKILL.md` depending on ownership.

Validation checklist:

- `added > 0` when tokens were not already known.
- `len(tokenizer)` increased by `added`.
- `tokenizer.convert_tokens_to_ids(new_token)` is not the unknown token id.
- `tokenizer.decode(tokenizer(new_token, add_special_tokens=False)["input_ids"])` preserves recognizable structure.
- `save_pretrained(...)` then reload preserves the special token map.

## Chat Template APIs

### `tokenizer.apply_chat_template(...)`

Inputs are usually a list of `{role, content}` dictionaries. Common roles are `system`, `user`, `assistant`, and model-specific tool or observation roles.

Key options:

- `tokenize=True`: return token ids or tensors directly; safest way to avoid duplicate special tokens.
- `tokenize=False`: return formatted text; if tokenizing later, usually pass `add_special_tokens=False`.
- `add_generation_prompt=True`: add the assistant-start marker where the model template supports it.
- `continue_final_message=True` or a string field name: continue the final assistant message/prefill; incompatible with `add_generation_prompt=True`.
- `return_tensors="pt"`: return framework tensors when tokenizing and the framework is installed.
- `return_dict=True`: request a dictionary/encoding form when supported by the tokenizer version and options.
- `tools=[...]` and `documents=[...]`: pass tool/RAG metadata only when the template expects those variables.

Expected failure signals:

- Missing template: tokenizer has no `chat_template`.
- Role/schema mismatch: the template expects roles or message content structures different from the provided list.
- Incompatible options: `continue_final_message` with `add_generation_prompt` raises an error.
- Duplicate BOS/EOS or separators: caused by formatting with `tokenize=False` and tokenizing later with added special tokens.

### `processor.apply_chat_template(...)`

Use processor chat templates for multimodal models. They mirror tokenizer chat template concepts but may also understand image/video/audio placeholders and can return modality data when `return_dict=True`.

Processor chat template checks:

- `processor.chat_template` exists and is a string or a dictionary with a `default` template.
- If multiple templates exist, pass the intended template name or template string.
- The message `content` schema matches model expectations, such as text chunks plus image placeholders.
- If `return_dict=True`, returned keys include the modality fields needed downstream, such as `input_ids` plus `pixel_values`.

## Processor And Image Processor Calls

### Multimodal processor call

A processor call commonly looks like:

```python
inputs = processor(
    text=["Describe this image."],
    images=[image],
    padding=True,
    return_tensors="pt",
)
```

Expected keys vary. Text+vision processors may return `input_ids`, `attention_mask`, and `pixel_values`; speech processors may return `input_features`; video processors may return frame tensors or pixel/video values.

### Image processor call

A vision processor call commonly looks like:

```python
inputs = image_processor(images=image_or_images, return_tensors="pt")
```

Important options are model-specific, but common behavior includes resize, rescale, normalize, crop, pad, and channel format conversion. Validate output shapes and dtypes before passing to a model.

## Save/Load APIs

Use `save_pretrained(save_directory)` and `from_pretrained(save_directory, local_files_only=True)` for portability checks.

Tokenizer round trip:

```python
tokenizer.save_pretrained(save_dir)
reloaded = AutoTokenizer.from_pretrained(save_dir, local_files_only=True)
assert reloaded.special_tokens_map == tokenizer.special_tokens_map
```

Processor round trip:

```python
processor.save_pretrained(save_dir)
reloaded = AutoProcessor.from_pretrained(save_dir, local_files_only=True)
```

Chat templates may be saved as `chat_template.jinja` and, for multiple templates, files under a chat-template directory. Treat the saved directory as the portable runtime artifact rather than relying on source checkout files.
