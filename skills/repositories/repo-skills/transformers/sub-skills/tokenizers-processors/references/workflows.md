# Tokenizer And Processor Workflows

Use these workflows when implementing preprocessing tasks with Transformers 5.13.0.dev0. They assume runtime safety: local-first loading, explicit network opt-in, and optional dependency checks before tensor or modality work.

## Workflow: Local Tokenizer Smoke Check

Goal: verify that a tokenizer directory or approved Hub id loads, tokenizes, decodes, and exposes expected special-token metadata.

1. Load locally first:

   ```python
   tokenizer = AutoTokenizer.from_pretrained(path_or_id, local_files_only=True, use_fast=True)
   ```

2. Print or assert basic metadata:

   ```python
   assert tokenizer.vocab_size is not None
   print(type(tokenizer).__name__, tokenizer.is_fast, len(tokenizer))
   print(tokenizer.special_tokens_map)
   ```

3. Encode representative text:

   ```python
   encoding = tokenizer(
       "The quick brown fox.",
       padding=False,
       truncation=False,
       return_special_tokens_mask=True,
   )
   assert "input_ids" in encoding
   ```

4. Decode with and without special tokens:

   ```python
   raw = tokenizer.decode(encoding["input_ids"], skip_special_tokens=False)
   clean = tokenizer.decode(encoding["input_ids"], skip_special_tokens=True)
   ```

5. If the downstream flow needs fixed tensors, rerun with `padding=True`, `truncation=True`, `max_length=...`, and `return_tensors=...`.

Use `scripts/tokenizer_smoke.py` for this workflow from a shell.

## Workflow: Choose Fast Or Slow Tokenizer

Use fast tokenizers by default for speed and alignment unless model behavior or missing dependencies force a slow/Python backend.

Decision table:

| Need | Prefer | Required check |
| --- | --- | --- |
| High-throughput encoding | `use_fast=True` | load succeeds and `tokenizer.is_fast` is true |
| Character/word offsets | fast tokenizer | `return_offsets_mapping=True` succeeds |
| Exact legacy behavior | model-specific slow class or `use_fast=False` | compare known tokens/ids |
| Backend-specific model tokenizer | default auto selection | optional package installed or fallback accepted |
| Debug mismatch between training and inference | same class/backend as original artifact | compare `type(tokenizer).__name__`, `is_fast`, and saved files |

Alignment validation snippet:

```python
encoding = tokenizer("New York", return_offsets_mapping=True)
if not tokenizer.is_fast:
    raise ValueError("Offset alignment requires a fast tokenizer for this workflow")
print(encoding.tokens())
print(encoding.word_ids())
print(encoding["offset_mapping"])
```

## Workflow: Add Multimodal Or Chat Special Tokens

Goal: add image/audio/video/chat placeholders on the tokenizer side and explain who owns model resizing.

1. Load the tokenizer.
2. Add tokens with either `extra_special_tokens` at load time or `add_special_tokens(...)` after load.
3. Record the number of added tokens and new tokenizer length.
4. Validate ids for each token.
5. Save and reload the tokenizer.
6. If `added > 0` and a model will consume the tokenizer, route model embedding resize to the model owner.

Example:

```python
added = tokenizer.add_special_tokens({
    "additional_special_tokens": ["<image>", "<audio>", "<video>"],
})
ids = tokenizer.convert_tokens_to_ids(["<image>", "<audio>", "<video>"])
assert all(token_id != tokenizer.unk_token_id for token_id in ids)
```

Owner route:

- Model architecture or embedding mutation: `../model-extension/SKILL.md`.
- Resize inside a training script before fine-tuning: `../training/SKILL.md`.
- Resize before generation/inference loading: `../generation/SKILL.md` or `../inference-pipelines/SKILL.md` depending on caller.

## Workflow: Validate Chat Template Formatting

Goal: ensure chat messages become the exact prompt format expected by the tokenizer or processor.

1. Confirm template exists:

   ```python
   if getattr(tokenizer, "chat_template", None) is None:
       raise ValueError("Tokenizer has no chat template")
   ```

2. Use canonical role/content messages:

   ```python
   messages = [
       {"role": "system", "content": "You are helpful."},
       {"role": "user", "content": "Say hi."},
   ]
   ```

3. Prefer tokenizing inside `apply_chat_template`:

   ```python
   input_ids = tokenizer.apply_chat_template(
       messages,
       tokenize=True,
       add_generation_prompt=True,
   )
   ```

4. If you need plain text, avoid duplicate special tokens later:

   ```python
   prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
   encoding = tokenizer(prompt, add_special_tokens=False)
   ```

5. For prefilled assistant continuation, use `continue_final_message=True` and omit `add_generation_prompt`.

6. For multimodal chat, use `processor.apply_chat_template(...)` and validate the message content schema.

Expected signals:

- Formatted prompt contains model-specific role separators or control tokens.
- Tokenized output is a list, tensor, or dict depending on `tokenize`, `return_tensors`, and `return_dict`.
- Incompatible option combinations raise `ValueError` rather than silently choosing behavior.

## Workflow: Processor Preflight For Multimodal Inputs

Goal: validate processor outputs before sending data to a model, pipeline, trainer, or generation script.

1. Load with `AutoProcessor.from_pretrained(model_or_path, local_files_only=True)` when possible.
2. Inspect available components:

   ```python
   for name in ["tokenizer", "image_processor", "feature_extractor", "video_processor"]:
       print(name, hasattr(processor, name))
   ```

3. Construct a minimal modality input matching the model contract.
4. Call the processor with explicit `return_tensors` only when the framework dependency is installed.
5. Assert required keys and first-dimension batch size.
6. If the processor has a chat template, validate formatting separately from modality tensor generation.

Common output keys by modality:

- Text: `input_ids`, `attention_mask`, sometimes `token_type_ids`.
- Image: `pixel_values`, sometimes `pixel_mask` or image size metadata.
- Audio: `input_features`, `attention_mask`, sampling-rate-dependent features.
- Video: model-specific frame or pixel fields; inspect returned keys rather than guessing.

## Workflow: Save/Load Portability Check

Goal: prove tokenizer or processor files are self-contained after local customization.

Tokenizer:

```python
tokenizer.save_pretrained(save_dir)
reloaded = AutoTokenizer.from_pretrained(save_dir, local_files_only=True)
assert reloaded.special_tokens_map == tokenizer.special_tokens_map
assert len(reloaded) == len(tokenizer)
```

Processor:

```python
processor.save_pretrained(save_dir)
reloaded = AutoProcessor.from_pretrained(save_dir, local_files_only=True)
print(type(reloaded).__name__)
```

Additional checks:

- Chat template files reload into `chat_template`.
- Added special tokens remain special after reload.
- Backend files required by the tokenizer class are present.
- The workflow does not rely on the original source repository or temporary directories.

## Workflow: Preflight Before Trainer Or Generation

This sub-skill often feeds sibling workflows. Run the following before handing off:

1. Load tokenizer/processor using the exact local artifact or pinned model id intended downstream.
2. Encode two short examples with the same `padding`, `truncation`, and `max_length` policy the downstream workflow will use.
3. Validate rectangular tensor shapes if batching.
4. Decode a sample to confirm no unexpected special-token duplication.
5. If chat, validate `apply_chat_template` with the downstream role order.
6. If special tokens were added, report `added`, `len(tokenizer)`, and the need for model embedding resize.
7. Hand off to:
   - `../training/SKILL.md` for `Trainer`, collators, dataset maps, or embedding resize during fine-tuning.
   - `../generation/SKILL.md` for prompt construction and `model.generate(...)`.
   - `../inference-pipelines/SKILL.md` for `pipeline(..., tokenizer=..., processor=...)` integration.

## Workflow: Safe Optional Dependency Probe

When a tokenizer or processor may require optional dependencies, probe imports without failing the whole task unless the dependency is essential:

```python
import importlib.util

for package in ["tokenizers", "sentencepiece", "tiktoken", "mistral_common", "PIL"]:
    print(package, importlib.util.find_spec(package) is not None)
```

If a dependency is missing:

- For text-only fallback, retry a different tokenizer backend only when the model supports it.
- For modality processing, skip tensor conversion or ask the user to install the required package.
- For PyTorch tensors in minimal environments, omit `return_tensors="pt"` or route setup to an environment/install step.
