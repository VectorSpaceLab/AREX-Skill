# Troubleshooting ASRT pinyin language-model decoding

## `dict.txt` is missing or output changes with working directory

Symptom: `load_model()` fails to find `dict.txt`, or the same code works only from one directory.

Cause: ASRT's original `load_model()` loads `dict.txt` by bare filename, so the caller's current working directory matters. Use the bundled script's defaults, pass `--dict`, or instantiate the bundled helper with `dict_path="dict.txt"` from this sub-skill directory.

## `language_model1.txt` or `language_model2.txt` is missing

Symptom: file-not-found during `load_model()`.

Cause: `model_path` must contain both count files. The bundled layout is `language_model/language_model1.txt` and `language_model/language_model2.txt`.

Recovery:

```bash
python scripts/decode_pinyin.py --model-dir language_model --dict dict.txt ni3 hao3 ya5
```

## Unknown pinyin returns an empty decode

Symptom: a token produces no candidates, or a sequence silently drops an unknown token.

Cause: `pinyin_stream_decode` returns `[]` when `item_pinyin` is absent from `dict.txt`. The dictionary uses tone-number pinyin such as `ni3`, `hao3`, and neutral-tone `ya5`; it does not accept tone marks like `nǐ`, untuned syllables like `ni`, or arbitrary labels.

Recovery:

```bash
python scripts/decode_pinyin.py --diagnose ni3 unknown9 hao3
```

Normalize upstream pinyin to ASRT's tone-number vocabulary before decoding.

## Empty intermediate state after a known token

Symptom: a known pinyin token starts a new segment, or stream output flushes the previous text unexpectedly.

Cause: transitions require a bigram entry for `previous_character + current_character`. If none of the candidate pairs exists in `language_model2.txt`, the intermediate state becomes empty even though the pinyin token is known.

Recovery: inspect whether the previous and current candidate characters form bigrams in `language_model2.txt`, then decide whether segmentation is acceptable or whether the upstream pinyin sequence is wrong.

## Streaming client indexes an empty state

Symptom: a stream implementation crashes after an unknown token or after a chunk with no valid pinyin continuation.

Cause: ASRT's stream pattern assumes a non-empty decode state before reading the first candidate. Robust clients should check `len(tmp_result) > 0` before using `tmp_result[0][0]`, and should commit only non-empty previous states.

Use the bundled script's `--stream` mode to inspect state transitions safely.

## Beam size hides a later valid path

Symptom: a lower-ranked early candidate would have produced a better sentence later, but it disappears.

Cause: after each non-initial extension, candidates are sorted by score and truncated to `beam_size`. A smaller beam is faster but can prune useful paths. The default `100` matches ASRT server usage.

Recovery: increase `--beam-size` during diagnosis, then compare output and runtime.

## Count file parse or encoding errors

Symptom: `ValueError`, bad counts, or garbled characters during model loading.

Expected format:

- UTF-8 text files;
- tab-separated key/count rows after the first total-count line;
- integer-like count values;
- no CSV commas or JSON wrappers.

Do not edit the files with tools that convert tabs to spaces or change the encoding.

## Unigram/bigram mismatch

Symptom: `KeyError` for a previous character during transition scoring.

Cause: the decoder divides a bigram count by the unigram count for the previous character. A custom or edited bigram file can reference a previous character that is absent from the unigram file.

Recovery: keep `language_model1.txt` and `language_model2.txt` from the same model build, or regenerate both together.
