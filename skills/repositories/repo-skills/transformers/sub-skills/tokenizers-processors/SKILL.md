---
name: tokenizers-processors
description: "Use Transformers tokenizers, processors, image/audio/video
  processors, chat templates, special tokens, BatchEncoding alignment, and
  preprocessing save/load validation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Tokenizers And Processors

Use this sub-skill when an agent needs to prepare model inputs or inspect preprocessing artifacts with Transformers 5.13.0.dev0. Prefer `AutoTokenizer`, `AutoProcessor`, `AutoImageProcessor`, and model-specific processor classes over hand-built preprocessing unless the model docs or local files prove a custom class is required.

## Route Here

Route tokenizer and processor work here when the task asks to:

- Load or validate a tokenizer with `AutoTokenizer.from_pretrained(...)`, including local directories and Hub ids.
- Choose fast vs slow tokenizer behavior, alignment APIs, or optional tokenization backends.
- Configure padding, truncation, special tokens, chat templates, or decode/postprocess behavior.
- Use `AutoProcessor`, `ProcessorMixin`, image processors, feature extractors, video processors, or multimodal processors.
- Validate that `save_pretrained(...)` and `from_pretrained(...)` round-trip preprocessing files.
- Preflight tokenizer/processor inputs before training, generation, pipelines, or serving.

## Route Elsewhere

- Inference pipeline assembly, task selection, `device`, `dtype`, or `device_map`: use `../inference-pipelines/SKILL.md`.
- Decoding strategy, `GenerationConfig`, streamers, or `model.generate(...)`: use `../generation/SKILL.md`.
- `Trainer`, `TrainingArguments`, datasets, collators, or distributed training: use `../training/SKILL.md`.
- Server and CLI behavior, including the `transformers` console script: use `../serving-cli/SKILL.md`.
- Quantization packages, adapters, accelerate, or backend integrations: use `../quantization-integrations/SKILL.md`.
- New model classes, configs, generated modular files, or embedding resize implementation: use `../model-extension/SKILL.md`.

## Canonical APIs

- `AutoTokenizer.from_pretrained(pretrained_model_name_or_path, *inputs, **kwargs)` selects the tokenizer class from local or remote metadata.
- `tokenizer(...)` returns a `BatchEncoding` with model inputs such as `input_ids`, `attention_mask`, and optional masks or offsets.
- `tokenizer.decode(...)` and `tokenizer.batch_decode(...)` convert ids back to text; use `skip_special_tokens=True` for user-visible text.
- `tokenizer.add_special_tokens(...)` and `extra_special_tokens=...` register structural or multimodal tokens.
- `tokenizer.apply_chat_template(...)` formats role/content messages for chat models.
- `AutoProcessor.from_pretrained(...)` loads multimodal processors that wrap tokenizers plus image, audio, or video preprocessing.
- `AutoImageProcessor.from_pretrained(...)` loads image preprocessing configs, optionally with `backend="torchvision"` or `backend="pil"` where supported.
- `processor.apply_chat_template(...)` can format multimodal chat and return text-only or model-ready dictionaries depending on options.
- `save_pretrained(...)` and `from_pretrained(...)` validate portable tokenizer/processor artifacts.

See `references/api-reference.md` for argument choices and object behavior.

## Safe Loading Pattern

Prefer local-first loading during validation so a task does not unexpectedly require network access:

```python
from transformers import AutoTokenizer

tokenizer = AutoTokenizer.from_pretrained(
    model_or_path,
    local_files_only=True,
    use_fast=True,
)
```

If local files are unavailable and network access is explicitly allowed, retry with `local_files_only=False`. Use `trust_remote_code=True` only when the user accepts custom repository code execution and the source is trusted.

## Tokenization Decisions

- Set `padding=True` for dynamic batch padding or `padding="max_length"` with `max_length=...` for fixed-size export/evaluation flows.
- Set `truncation=True` and an explicit `max_length` when overflow must be controlled; inspect `special_tokens_mask` or sequence length when debugging.
- Use `return_tensors="pt"`, `"np"`, or another supported framework only when that dependency is installed.
- Use `return_offsets_mapping=True` and alignment helpers only with fast tokenizers; slow/Python tokenizers may not expose identical mappings.
- Avoid calling the tokenizer again with `add_special_tokens=True` after `apply_chat_template(tokenize=False)` unless you have verified the template lacks BOS/EOS tokens.

## Chat Template Pattern

Chat inputs are a list of dictionaries, usually with `role` and `content` keys:

```python
messages = [
    {"role": "system", "content": "You are concise."},
    {"role": "user", "content": "Summarize tokenization."},
]
encoded = tokenizer.apply_chat_template(
    messages,
    tokenize=True,
    add_generation_prompt=True,
    return_tensors="pt",
)
```

Use `continue_final_message=True` for prefill/continuation workflows instead of `add_generation_prompt=True`; do not set both. For multimodal chat, prefer `processor.apply_chat_template(...)` and pass modality payloads in the schema expected by that processor.

## Special Tokens And Resizing

Adding new tokens changes tokenizer vocabulary. If a model will consume the new token ids, the model embedding matrix must also be resized. This sub-skill helps detect and explain the tokenizer side; route model mutation to `../model-extension/SKILL.md` or the owning generation/training workflow.

Validation signals:

- `added = tokenizer.add_special_tokens({...})` returns the number of newly added tokens.
- `len(tokenizer)` increases when new tokens are added.
- Named multimodal tokens from `extra_special_tokens={"image_token": "<image>"}` become accessible where the tokenizer exposes model-specific token attributes.
- Saved tokenizer directories include tokenizer config, special token metadata, and backend vocabulary files required by that tokenizer class.

## Processor Decisions

Use processors when the model expects non-text inputs or a coupled tokenizer/image/audio/video contract. Common patterns:

- Text plus images: `AutoProcessor.from_pretrained(...)`, then `processor(text=..., images=..., return_tensors=...)`.
- Vision-only preprocessing: `AutoImageProcessor.from_pretrained(...)`, then `image_processor(images=..., return_tensors=...)`.
- Audio/video processors: load with `AutoProcessor` or the model-specific processor and check optional dependencies before tensor conversion.
- Save/load checks: call `processor.save_pretrained(tmp_dir)` and reload with `AutoProcessor.from_pretrained(tmp_dir, local_files_only=True)` when the processor class supports auto loading.

Processor details and modality formats are in `references/data-formats.md` and `references/workflows.md`.

## Bundled Smoke Check

Use the bundled script to inspect tokenizer loading and basic behavior without requiring network by default:

```bash
python scripts/tokenizer_smoke.py --model-or-path ./tokenizer_dir --text "Hello world" --local-files-only
```

Allow Hub resolution only when the user permits network access:

```bash
python scripts/tokenizer_smoke.py --model-or-path bert-base-uncased --text "Hello" --allow-remote
```

The script prints load metadata, special tokens, tokenized keys/lengths, decoded text, and optional chat-template output.

## Expected Checks

Before handing tokenizer/processor work to a sibling workflow, verify:

- `from_pretrained(...)` loads with intended `local_files_only`, `use_fast`, and trust settings.
- Encoded outputs contain the keys the downstream model or pipeline expects.
- Padding/truncation produce rectangular batches when tensors are requested.
- Added special tokens are saved and reloadable.
- Chat templates format the intended role order and do not duplicate BOS/EOS tokens.
- Optional modality dependencies are installed or gracefully skipped.

## Troubleshooting Index

- Backend package errors (`tokenizers`, `sentencepiece`, `tiktoken`, `mistral-common`): `references/troubleshooting.md`.
- Alignment or offset surprises: `references/api-reference.md` and `references/troubleshooting.md`.
- Multimodal processor schemas and image/audio/video inputs: `references/data-formats.md`.
- Save/load and preflight workflows: `references/workflows.md`.
