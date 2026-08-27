# Template/verbalizer troubleshooting

## Template grammar failures

### `RuntimeError: 'mask' position not found in the template`

Cause: `Template._check_template_format()` found no parsed piece containing `mask`.

Fix:

- Add `{"mask"}` to ordinary classification templates.
- For generation-only flows, confirm the selected OpenPrompt component still expects a mask and that target text is supplied through the dataloader/generation wrapper.
- Run `scripts/validate_prompt_assets.py` to catch no-mask template lines statically.

### `mixed_token_start { at position ... has no corresponding mixed_token_end }`

Cause: unmatched braces in the template string, often from hand-editing dict-like tokens.

Fix:

- Check every OpenPrompt token is a complete Python dict/set fragment: `{"placeholder": "text_a"}`, `{"mask"}`, etc.
- If literal text itself needs braces, avoid raw braces or wrap literal content with `{"text": "..."}` and escape internal quotes.
- Prefer the static validator before running OpenPrompt because source `parse_text` uses `eval` and may terminate the process on syntax errors.

### Unknown or misspelled template keys

Valid prompt-design keys are `placeholder`, `meta`, `mask`, `soft`, `soft_id`, `duplicate`, `same`, `special`, `text`, `shortenable`, `post_processing`, and `add_prefix_space`.

Common mistakes:

- `{"place_holder": "text_a"}` instead of `{"placeholder": "text_a"}`.
- `{"mask": "<mask>"}` instead of `{"mask"}` or `{"mask": None}`.
- `{"shortenable": "False"}` as a string instead of boolean `False`.

### Placeholder or meta key errors at wrap time

Cause: the template references a field that is absent from the `InputExample`.

Fix:

- Use `text_a`/`text_b` through `placeholder`.
- Use task-specific fields through `InputExample(meta={...})` and `{"meta": "field"}`.
- For generation verbalizer rules, remember `{"meta":"choice1"}` reads from the example's `meta`, not the label-name mapping.

## Mask-count and output-shape failures

### Ordinary verbalizer with a multi-mask template

`PromptForClassification.extract_at_mask` returns shape `[batch, vocab]` for one mask and `[batch, num_masks, vocab]` for several masks. Manual/one2one verbalizers are usually designed for one mask.

Fix:

- Use one mask for ordinary `ManualVerbalizer`, `KnowledgeableVerbalizer`, `SoftVerbalizer`, and `ProtoVerbalizer` classification.
- Use `PTRTemplate` + `PTRVerbalizer` for relation extraction with several masks.
- Use `GenerationVerbalizer`/generation workflows when several masks describe generated target text.
- For LM-BFF template generation, multiple masks in `template_for_auto_t.txt` are expected during search; final selected templates still need task-appropriate handling.

### PTR mask mismatch

Cause: the number of label words per class in `PTRVerbalizer` does not equal the number of masks, or classes have inconsistent lengths.

Fix:

- Count masks in `ptr_template.txt`.
- Ensure every JSON mapping value has exactly that many strings.
- Keep class labels aligned with the data processor's `get_labels()` order or pass exact `classes` for dict mapping.

## Verbalizer file-format failures

### `.txt` verbalizer loads as one class instead of several

Cause: OpenPrompt's `.txt` format is one class per non-empty line; commas separate alternative label words for the same class. Whitespace alone does not separate classes.

Fix:

```text
# Good binary verbalizer
Yes
No

# Good with alternatives
bad,terrible
excellent,great
```

Do not write `Yes No` on one line for two labels.

### `.jsonl` is not true JSON Lines in OpenPrompt

Source `Verbalizer.from_file()` calls `json.load(f)` for `.jsonl` and `.json`, so a pretty JSON dict/list works, but line-delimited JSON objects may fail in OpenPrompt itself.

Fix:

- Prefer a full JSON document for OpenPrompt runtime compatibility.
- The bundled validator accepts both full JSON and line-delimited JSONL so it can diagnose either style, but the runtime API is stricter.

### `name of classes in verbalizer are different from those of dataset`

Cause: a dict verbalizer's keys do not exactly equal the provided `classes` list/set.

Fix:

- Read the processor labels (`Processor().get_labels()` or config-provided classes).
- Use dict keys that exactly match those strings, including case and punctuation.
- If class names are unavailable, use list/text format and document label-id order.

### `number of classes in the verbalizer file does not match the predefined num_classes`

Cause: the selected `choice` group has too many/few class lines or dict entries.

Fix:

- Inspect blank-line groups in `.txt` files.
- Pass the intended `choice` explicitly.
- Keep each alternative group at the same class count.

## Label-word and tokenizer issues

### Label word splits into multiple tokens

Manual, one2one, soft, and proto verbalizers can process multi-token label words with `multi_token_handler`, but repo comments warn that label words are intended to be single tokens where possible. Multi-token words can change scores, mask shapes, and calibration behavior.

Fix:

- First run the static validator to catch obvious whitespace label words.
- Then run tokenizer-level validation with the target tokenizer when available:

  ```bash
  python scripts/validate_prompt_assets.py --assets-dir references/prompt-assets/scripts --tokenizer roberta-large
  ```

- Choose a single-token synonym, or set and document `multi_token_handler='first'|'max'|'mean'` deliberately.
- For `KnowledgeableVerbalizer`, consider `max_token_split` to discard overly split candidates.

### RoBERTa/T5 prefix-space surprises

`ManualVerbalizer.add_prefix` prepends a space by default because RoBERTa-like tokenizers distinguish beginning-of-word tokens. Prefixing can make a label word one token or several depending on tokenizer.

Fix:

- Keep default `prefix=' '` for RoBERTa-style masked LMs unless you have checked the tokenizer.
- Use the `<!>` sentinel at the start of a label word to suppress automatic prefixing for special cases, e.g. `<!>'s` in PTR assets.
- Validate with the actual tokenizer whenever the model family changes.

### Duplicate/ambiguous label words

Duplicates across ordinary class verbalizers make labels ambiguous. `KnowledgeableVerbalizer` deletes common words after the first class; PTR uses repeated words as part of multi-mask logic, so duplicates there are warnings rather than automatic failures.

Fix:

- For ordinary manual/one2one verbalizers, remove duplicates or move to class-specific synonyms.
- Use `--strict-duplicates` in the validator for review gates.
- For knowledgeable/PTR assets, inspect duplicate warnings but do not remove expected repeated relation scaffolding blindly.

## Soft, prefix, and P-tuning failures

### Constructor complains about missing model/config

Soft, mixed, P-tuning, prefix-tuning, soft verbalizer, and proto verbalizer components need model embeddings, output heads, hidden size, or config.

Fix:

- Use `ManualTemplate` and `ManualVerbalizer` for static/no-model inspection.
- Use `MixedTemplate`, `SoftTemplate`, `PtuningTemplate`, `PrefixTuningTemplate`, `SoftVerbalizer`, or `ProtoVerbalizer` only after a PLM is loaded.

### Prefix tuning fails under DataParallel or unsupported model

Source `PrefixTuningTemplate` modifies T5/GPT2-style forward behavior and warns that DataParallel can fail.

Fix:

- Prefer a single-device or model-parallel strategy for prefix tuning.
- Confirm model config is T5 or GPT2-like before choosing prefix tuning.
- Fall back to `SoftTemplate` or `PtuningTemplate` for other model families.

### `unknown prompt_enocder_type`

Cause: `PtuningTemplate` only accepts `prompt_encoder_type='lstm'` or `'mlp'`.

Fix: correct the config key or use `PTRTemplate`, which fixes the prompt encoder to MLP.

## Calibration failures

### Calibration shape mismatch

Cause: `calibrate()` returns logits at mask positions. Shape must match the verbalizer's expected projected mask/class/label-word layout.

Fix:

- Use a one-mask template with manual/knowledgeable classification verbalizers.
- Rebuild support dataloader with the same template/tokenizer/wrapper as the target model.
- Register calibration logits only on verbalizers that implement calibration (`ManualVerbalizer`, `One2oneVerbalizer`, and `KnowledgeableVerbalizer` style code paths).

### Knowledgeable verbalizer loses many label words after calibration

Cause: `register_calibrate_logits` filters candidates whose token ids fall in the low-prior fraction controlled by `candidate_frac`.

Fix:

- Log label-word counts before and after registration.
- Tune `candidate_frac` or use a smaller curated label-word file.
- Validate that every class still has at least one candidate.

## Config-loader failures

### `text` and `file_path` both set

`Template.from_config` and `Verbalizer.from_config` reject configs that specify inline text/label words and `file_path` simultaneously.

Fix: choose exactly one source of truth per component.

### Loader key missing from map

`load_template` and `load_verbalizer` use exact keys from `TEMPLATE_CLASS` and `VERBALIZER_CLASS`.

Fix:

- Template keys: `manual_template`, `mixed_template`, `ptuning_template`, `soft_template`, `ptr_template`, `prefix_tuning_template`.
- Verbalizer keys: `manual_verbalizer`, `knowledgeable_verbalizer`, `automatic_verbalizer`, `ptr_verbalizer`, `one2one_verbalizer`, `generation_verbalizer`, `soft_verbalizer`, `proto_verbalizer`.

## Validator-specific diagnostics

- `template token has Python-literal syntax error`: fix dict/set syntax before running OpenPrompt.
- `template line has no {'mask'} token`: add a mask or do not classify the file as a template.
- `label word '...' contains whitespace`: split class lines correctly or replace with a single-token label word.
- `empty verbalizer file`: provide class lines; an empty source file is not usable with `Verbalizer.from_file`.
- duplicate warnings: review ambiguity; use `--strict-duplicates` for ordinary manual-verbalizer publication gates.
