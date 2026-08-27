# Text troubleshooting

- **Unknown cleaner:** the cleaner name is resolved with `getattr`; use one of
  the documented functions or add a real function before using its name.
- **Unexpected pronunciation:** check braces, phone spelling, stress digits,
  and whether `sequence_to_text` is being mistaken for an inverse of the
  cleaner. It only maps ids back to symbols.
- **Letters or punctuation disappear:** symbols not in the configured
  vocabulary are filtered. Choose transliteration or update the character set
  before regenerating data.
- **Numbers sound wrong:** `english_cleaners` invokes the legacy `inflect`
  rules; `basic_cleaners` and `transliteration_cleaners` do not expand numbers.
- **CMUdict missing:** `use_cmudict=True` requires `cmudict-0.7b` next to the
  metadata file. Validate placement and encoding; do not put it only in the
  repository root.
- **Train/eval mismatch:** use the same cleaner names, symbol vocabulary,
  `outputs_per_step`, and relevant hparams at both stages.
