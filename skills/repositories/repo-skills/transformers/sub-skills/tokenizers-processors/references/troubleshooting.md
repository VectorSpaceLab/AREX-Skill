# Tokenizer And Processor Troubleshooting

Use this guide when tokenizer or processor work fails in Transformers 5.13.0.dev0. Start with the exact failing call, the class selected by `AutoTokenizer` or `AutoProcessor`, and whether the environment has optional dependencies.

## Missing Optional Dependencies

### `tokenizers`

Symptoms:

- Fast tokenizer import or backend load fails.
- `use_fast=True` cannot satisfy the requested tokenizer.
- Alignment APIs are unavailable.

Actions:

- Retry with `use_fast=False` only if the model has a slow/Python tokenizer and exact alignment is not required.
- Install `tokenizers` in the runtime environment when fast behavior or offsets are required.
- Confirm `tokenizer.is_fast` before using `word_ids()`, `tokens()`, or offset mappings.

### `sentencepiece`

Symptoms:

- SentencePiece model tokenizers fail to import or instantiate.
- Errors mention missing `sentencepiece`, `.model` files, or conversion from SentencePiece.

Actions:

- Install `sentencepiece` when the selected tokenizer requires it.
- Check that the saved tokenizer directory includes the SentencePiece model file.
- Do not force `use_fast=True` unless a compatible fast tokenizer exists and loads successfully.

### `tiktoken`

Symptoms:

- Tokenizer conversion or loading errors mention `tiktoken`.
- A model-specific tokenizer expects tiktoken assets.

Actions:

- Install `tiktoken` when the tokenizer class requires it.
- Prefer the saved tokenizer directory that already contains converted tokenizer assets when available.
- Record whether the tokenizer class changed after installing the dependency.

### `mistral-common`

Symptoms:

- Mistral/Pixtral tokenizer loading uses a fallback backend or errors on missing `mistral_common`.
- Chat or special-token behavior differs from expected Mistral tokenizer behavior.

Actions:

- Install `mistral-common` only when the model's tokenizer requires that backend.
- If fallback to a `tokenizers` backend is accepted, validate chat formatting and special token ids explicitly.
- Keep backend class and `tokenizer.is_fast` in the handoff.

### Modality packages

Symptoms:

- Image processor import errors mention PIL, torchvision, or image libraries.
- Audio processor errors mention audio loading, torchaudio, librosa, or sampling utilities.
- Tensor conversion errors mention PyTorch or another framework.

Actions:

- For smoke tests, omit `return_tensors="pt"` if PyTorch is not installed.
- Use `AutoImageProcessor.from_pretrained(..., backend=...)` only with an installed and supported backend.
- For audio, pass explicit `sampling_rate` and install the processor's required audio dependencies.
- For video, verify frame decoding dependencies separately from processor config loading.

## Special Token And Embedding Resize Problems

Symptoms:

- New tokens map to `unk_token_id`.
- Model errors with index out of range after tokenizer vocabulary growth.
- Generated text shows raw placeholder tokens unexpectedly.
- Training loss or generation quality degrades after adding tokens.

Actions:

1. Validate token addition:

   ```python
   added = tokenizer.add_special_tokens({"additional_special_tokens": ["<image>"]})
   assert tokenizer.convert_tokens_to_ids("<image>") != tokenizer.unk_token_id
   ```

2. Check whether `added > 0`. If yes, the tokenizer length changed.
3. If a model will consume those ids, route model embedding resize to the owner workflow:
   - `../model-extension/SKILL.md` for architecture or model code changes.
   - `../training/SKILL.md` for fine-tuning scripts.
   - `../generation/SKILL.md` or `../inference-pipelines/SKILL.md` for inference-time loading.
4. Save and reload the tokenizer; verify special tokens remain registered.
5. Avoid adding duplicate token strings under different special-token fields unless the model contract requires it.

## Padding And Truncation Failures

Symptoms:

- Tensor conversion fails because sequences have different lengths.
- Long examples exceed model maximum length.
- Decoder-only generation gives poor results with right padding.
- Pair truncation removes the wrong side of the input.

Actions:

- Enable `padding=True` for batched tensors.
- Enable `truncation=True` and set `max_length` for length control.
- Use `padding="max_length"` only when a fixed shape is required.
- Check `tokenizer.padding_side`; decoder-only batched generation commonly needs left padding.
- For pair inputs, select `truncation="only_first"`, `"only_second"`, or `"longest_first"` intentionally.
- Request `return_special_tokens_mask=True` to see where model structural tokens were inserted.

## Chat Template Role Or Schema Errors

Symptoms:

- `apply_chat_template` raises an error about missing template.
- Role alternation, role names, or content schemas are rejected.
- `continue_final_message` conflicts with `add_generation_prompt`.
- Model output includes duplicated BOS/EOS or assistant headers.

Actions:

- Confirm `tokenizer.chat_template` or `processor.chat_template` exists.
- Use role/content dictionaries and match model-specific allowed roles.
- Use `add_generation_prompt=True` for a new assistant answer.
- Use `continue_final_message=True` for prefilled assistant continuation; do not combine it with `add_generation_prompt=True`.
- Prefer `apply_chat_template(..., tokenize=True)` to avoid duplicated special tokens.
- If using `tokenize=False`, tokenize the formatted prompt with `add_special_tokens=False` unless verified otherwise.
- For multimodal chat, ensure content chunks match the processor schema, such as image placeholders plus text chunks.

## Processor Modality Errors

Symptoms:

- `AutoProcessor` loads but call fails on `images`, `audio`, or `videos`.
- Returned keys do not match what the downstream model expects.
- Save/load round trip loses tokenizer, image processor, or chat template behavior.

Actions:

- Inspect component attributes with `hasattr(processor, "tokenizer")`, `hasattr(processor, "image_processor")`, and similar checks.
- Build the minimal valid input for each modality and print returned keys.
- Pass `return_tensors` only after confirming the framework is installed.
- For image processors, try supported `backend` values and inspect `processor.backend` when present.
- For audio processors, pass the correct `sampling_rate`.
- Save and reload with `AutoProcessor.from_pretrained(saved_dir, local_files_only=True)` and compare output keys on a tiny input.

## Fast Tokenizer Alignment Differences

Symptoms:

- `return_offsets_mapping=True` works in one tokenizer but not another.
- `word_ids()` or `char_to_token()` is missing.
- Character spans do not match expected whitespace or normalization.
- Slow tokenizer output ids differ from fast tokenizer ids.

Actions:

- Require `tokenizer.is_fast` for span alignment workflows.
- Compare `tokenizer.backend_tokenizer` behavior only when available; do not assume it exists on slow tokenizers.
- Account for normalization: lowercasing, Unicode normalization, pre-tokenization, and special-token insertion can change offsets.
- Validate offsets on examples with spaces, punctuation, and non-ASCII characters.
- If exact legacy ids matter more than offsets, use the tokenizer backend that produced the training data.

## Local Versus Remote Loading

Symptoms:

- Smoke checks unexpectedly try to access the Hub.
- Offline mode changes behavior.
- A local directory loads a different class than expected.

Actions:

- Use `local_files_only=True` for reproducible checks.
- Use explicit `--allow-remote` or equivalent user-approved flag before network access.
- Print `type(tokenizer).__name__`, `tokenizer.name_or_path`, and `tokenizer.init_kwargs` fields relevant to the task.
- Pin `revision` for remote loads when reproducibility matters.
- Avoid `trust_remote_code=True` unless explicitly approved.

## Save/Load Round-Trip Failures

Symptoms:

- Reloaded tokenizer misses added special tokens.
- Reloaded processor lacks chat templates.
- `AutoProcessor` cannot resolve the saved processor class.
- Local-only reload tries to reach the network.

Actions:

- Save with `save_pretrained(save_dir)` from the object that has the final configuration.
- Reload from the saved directory with `local_files_only=True`.
- Compare `special_tokens_map`, `len(tokenizer)`, and a representative encoding.
- Check for chat template files and processor config files in the saved directory.
- If `AutoProcessor` cannot resolve the class, try the model-specific processor class and record that requirement in the downstream project.

## Minimal Debug Report

When handing off a tokenizer/processor issue, include:

- Failing API call and arguments excluding secrets.
- `transformers` version.
- Tokenizer or processor class name.
- `tokenizer.is_fast` when applicable.
- `local_files_only`, `use_fast`, `trust_remote_code`, and `revision` choices.
- Optional dependency presence for `tokenizers`, `sentencepiece`, `tiktoken`, `mistral_common`, PIL/torchvision, audio/video packages, and PyTorch if tensors are requested.
- Representative input and returned keys.
- Whether added special tokens changed `len(tokenizer)`.
