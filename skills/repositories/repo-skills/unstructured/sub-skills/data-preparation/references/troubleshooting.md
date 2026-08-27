# Data Preparation Troubleshooting

## Cleaning Changes Annotation Offsets

Symptoms:

- NER spans point to the wrong text after cleanup.
- Datasaur entities fail review because `start_idx` and `end_idx` no longer match the cleaned string.
- Label Studio predictions highlight shifted text.

Fix:

1. Clean text before generating labels or offsets whenever possible.
2. Avoid destructive cleaners such as `remove_punctuation()`, `clean_dashes()`, or `clean_ordered_bullets()` after offsets exist.
3. For whitespace-only cleanup, use `clean_extra_whitespace_with_index_run()` to reason about index movement and then re-check spans against the final string.
4. Recompute entity offsets against the exact staged text.

## Invalid Element Categories or Dropped Elements

Symptoms:

- JSON loading returns fewer elements than expected.
- Staging output misses non-text or custom element dictionaries.
- Element dictionaries with unknown `type` values disappear during conversion.

Fix:

- Annotation staging helpers generally expect `Text`-like `Element` objects with a `.text` value. Filter or transform unsupported objects before staging.
- When loading generic element JSON, route schema and deserialization debugging to `elements-and-metadata`.
- If the task starts from raw files, route partitioning to `partitioning`; this sub-skill should not invent element types.

## Prodigy Metadata Errors

Symptoms:

- `ValueError` says metadata length does not match elements length.
- `ValueError` says key `id` is not allowed.

Fix:

- Build one metadata dictionary per element.
- Do not include `id` in metadata; `stage_for_prodigy()` writes element ids into `meta.id`.
- Check CSV field names after `stage_csv_for_prodigy()` because metadata keys are lowercased.

## Label Studio Schema Errors

Symptoms:

- `ValueError` for invalid label type.
- `ValueError` for prediction score outside `0..1`.
- Mismatched annotations or predictions are rejected.
- The resulting task JSON uses unexpected field names.

Fix:

- Use a supported `LabelStudioResult.type`, such as `choices`, `labels`, `textarea`, or another value listed by the module.
- Wrap annotations and predictions as one list per element.
- Keep prediction `score` between `0` and `1`.
- Set `text_field` and `id_field` to match the target Label Studio project config.
- Treat `stage_for_label_studio()` as deprecated package functionality; validate the exported JSON against the Label Studio version in use before production upload.

## Labelbox File and Attachment Errors

Symptoms:

- `FileNotFoundError` for the output directory.
- `ValueError` for invalid attachment type or value.
- Imported Labelbox rows cannot access the staged text.

Fix:

- Pass `create_directory=True` or create the output directory before calling `stage_for_label_box()`.
- Make `external_ids` and attachment lists the same length as elements.
- Use only attachment types `IMAGE`, `VIDEO`, `RAW_TEXT`, `TEXT_URL`, or `HTML`; attachment values must be strings.
- Upload or host the generated text files separately; `url_prefix` must point to where the files will be reachable by Labelbox.

## Datasaur Entity Errors

Symptoms:

- `ValueError` mentions missing entity keys or wrong types.
- Entities appear on the wrong characters in Datasaur.

Fix:

- Provide one entity list per element.
- Each entity dictionary must include `text` as `str`, `type` as `str`, `start_idx` as `int`, and `end_idx` as `int`.
- Verify offsets against the final cleaned text, not the pre-cleaned source.

## Hugging Face or Translation Dependency Failures

Symptoms:

- Import errors for `transformers`, tokenizer classes, or Marian models.
- Translation raises `ValueError` for unsupported language pairs.
- First run stalls or fails while trying to download model data.
- A tokenizer window error says one segment is larger than the maximum token count.

Fix:

- Confirm `transformers` and any required tokenizer/model artifacts are installed before calling `stage_for_transformers()` or `translate_text()`.
- Require explicit approval for network downloads or hosted model access in restricted environments.
- For translation, use two-letter language codes; Chinese variants are normalized to `zh` by the helper.
- If a translation pair is unsupported, use another provider outside this local helper and document the credential/service boundary.
- For tokenizer window errors, split text into smaller segments before chunking or pass a finer `split_function`.

## spaCy Tokenization and Language Behavior

Symptoms:

- Sentence tokenization is slow on first use.
- Tokenization tries to install or load `en_core_web_sm`.
- Very long input is truncated for NLP heuristics.
- Non-English sentence boundaries are poor.

Fix:

- Treat `sent_tokenize()`, `word_tokenize()`, and `pos_tag()` as spaCy-backed helpers, not pure standard-library utilities.
- Pre-install the expected spaCy model in managed environments.
- For non-English or domain-specific text, validate sentence boundaries before using them for annotation spans or transformer chunking.
- For very long text, chunk before tokenization when exact full-document tokenization is required.

## Text Encoding Problems

Symptoms:

- Text contains `\xa0`, `â\x80\x99`, `=E2=80=99`, or other mojibake.
- Cleaner output still contains wrong quote/dash characters.

Fix:

- Use `replace_mime_encodings()` for quoted-printable fragments such as `=E2=80=99`.
- Use `replace_unicode_quotes()` for common quote and dash mojibake sequences.
- Use `bytes_string_to_string()` only when the input is truly a string representation of bytes.
- When the original file encoding is unknown, resolve decoding in the partitioning step rather than repeatedly cleaning already-corrupted text.

## Service and Credential Boundaries

Unstructured staging functions prepare local payloads. They do not authenticate to Prodigy, Label Studio, Labelbox, Datasaur, Baseplate, Hugging Face Hub, or other hosted services. Before upload or model download, confirm:

- the target account/project/schema;
- credentials and secret-handling policy;
- network access and rate limits;
- where local files or hosted URLs will live;
- whether generated text contains sensitive content that should not leave the local environment.
