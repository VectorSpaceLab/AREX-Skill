# QA pipeline reference

Deepjazz applies grammar and note cleanup after a grammar measure has been
generated and before it is inserted into the output stream. Keep the order below
when reproducing or debugging behavior.

```python
curr_grammar = prune_grammar(curr_grammar)
curr_notes = unparse_grammar(curr_grammar, curr_chords)
curr_notes = prune_notes(curr_notes)
curr_notes = clean_up_notes(curr_notes)
```

## Function effects

| Step | Helper | Effect | Debug signal |
| --- | --- | --- | --- |
| 1 | `prune_grammar(curr_grammar)` | Splits on spaces, then commas; rounds each duration to a multiple of `0.250` using a random up/down choice. | Token count should stay the same; every token should still have a float duration in field 2. |
| 2 | `unparse_grammar(m1_grammar, m1_chords)` | Converts grammar plus chords into a `stream.Voice` of `note.Note` and `note.Rest`. | At least one note should be produced for ordinary generated grammar; exact pitches may vary. |
| 3 | `prune_notes(curr_notes)` | Processes elements in adjacent pairs and removes a repeated note when both pair members are `note.Note` with the same `nameWithOctave`. | Adjacent same-pitch duplicates should not survive this step. |
| 4 | `clean_up_notes(curr_notes)` | Changes zero `quarterLength` elements to `0.250` and removes later adjacent `note.Note` objects with the same offset, preventing accidental note-note chords. | No retained element should have `quarterLength == 0.0`; no adjacent note-note pair should share an offset. |

## Randomness and smoke-test design

Randomness appears in multiple places:

- `prune_grammar` randomly rounds each duration up or down.
- `unparse_grammar` uses random choices when selecting chord tones, scale tones,
  approach tones, and fallback whole-step movement.
- Candidate ordering in the legacy source can depend on set/list order from
  scale derivation.

For this reason, smoke tests should assert structural signals instead of exact
pitch names. Good assertions include:

- The grammar string splits into the expected number of tokens.
- The token type sequence contains the expected classes (`R`, `C`, `S`, `A`,
  `X`) for a synthetic fixture.
- Every token duration field is parseable as a float.
- Unparsing returns `note.Note`/`note.Rest` elements in a `music21` voice or
  list-like sequence.
- Cleanup removes same-offset note-note duplicates and fixes zero-length notes.

Use `--seed` with the bundled smoke script only to make a debugging run
repeatable; do not use seeded pitch names as a model-quality claim.

## Duration rounding caveat

The rounding helper has legacy behavior rather than strict nearest-neighbor
math. When a duration is already an exact multiple of `0.250`, an up-round can
still move it to the next multiple. When a short duration such as `0.125` is
rounded down, the result can be `0.0`. That is why `clean_up_notes` exists and
why post-cleanup structural checks are more robust than checking intermediate
durations.

## Cleanup data structure expectations

- The unparser returns a `music21.stream.Voice`; the cleanup helpers only need a
  list-like/stream-like sequence of `note.Note` and `note.Rest` elements.
- Keep elements sorted by offset before checking same-offset adjacency.
- If you copy notes into a new sequence, preserve each element's `.offset` and
  `.quarterLength`; those fields drive QA behavior.
