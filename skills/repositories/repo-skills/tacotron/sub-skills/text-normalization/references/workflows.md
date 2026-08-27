# Text workflows

## English training and inference

Use `english_cleaners` at both stages. This makes `3`, `$5.01`, abbreviations,
and accented Latin text deterministic before symbol lookup. Do not change the
cleaner only during evaluation: the model learned ids from the training
pipeline.

## Non-English data

For text that can be transliterated to ASCII, use `transliteration_cleaners`.
For a native character set, use `basic_cleaners` and update the character
vocabulary deliberately before preprocessing; otherwise characters may be
silently discarded by `_should_keep_symbol`.

## Native cleaner check

Use the checkout root for native imports; the conceptual check is not a skill
smoke and does not prove synthesis:

```bash
CHECKOUT_ROOT=/path/to/tacotron-checkout
cd "$CHECKOUT_ROOT" && python -c "from text import cleaners; print(cleaners.transliteration_cleaners('Здравствуйте'))"
```

## Forced pronunciation

Put a valid ARPAbet sequence in braces inside ordinary text. Keep the braces
around only the pronunciation segment and separate phones with spaces. This is
an input convention, not a file path or a CMUdict lookup at inference time.

## CMUDict-assisted training

Set `use_cmudict=True` in the hparams override and place the compatible
`cmudict-0.7b` file in the preprocessed data directory. The data feeder loads
only unambiguous entries and randomly replaces some words during training. If
the file is absent, fail early and fix the data directory rather than disabling
pronunciation support silently.
