# Text API reference

## `text.text_to_sequence(text, cleaner_names)`

Returns a list of integer symbol ids. It processes ordinary text with each
named cleaner, recognizes a `{...}` region as space-separated ARPAbet symbols,
filters symbols not in the vocabulary, and appends the EOS symbol `~`.
`cleaner_names` is a list such as `['english_cleaners']`; an unknown name raises
`Exception('Unknown cleaner: ...')`.

## `text.sequence_to_text(sequence)`

Maps ids back to symbols, wraps ARPAbet symbols beginning with `@` in braces,
joins adjacent brace regions with a space, and returns an empty string for an
empty sequence. It does not recover text that was filtered or normalized away.

## Cleaner functions

- `english_cleaners(text)`: ASCII transliteration, lowercase, number expansion,
  abbreviation expansion, whitespace collapse.
- `transliteration_cleaners(text)`: transliteration, lowercase, whitespace
  collapse; numbers remain digits.
- `basic_cleaners(text)`: lowercase and whitespace collapse without
  transliteration.
- Individual helpers include `normalize_numbers`, `expand_abbreviations`,
  `convert_to_ascii`, `lowercase`, and `collapse_whitespace`.

## Symbols and ARPAbet

The default vocabulary starts with `_` padding and `~` EOS, then ASCII
characters and `@`-prefixed CMUDict symbols. Curly-brace content is split on
spaces and converted to `@<phoneme>` symbols. Phonemes must use the valid CMU
symbol spelling, including stress digits such as `AH0`.

## `text.cmudict.CMUDict(file_or_path, keep_ambiguous=True)`

Parses CMUdict lines with two spaces between word and pronunciation. Lookup is
case-insensitive and returns a list of pronunciation strings or `None`. With
`keep_ambiguous=False`, entries having multiple pronunciations are removed.
Words with invalid phoneme tokens are ignored.
