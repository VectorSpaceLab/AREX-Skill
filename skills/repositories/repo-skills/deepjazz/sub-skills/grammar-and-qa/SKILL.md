---
name: grammar-and-qa
description: "Understand, validate, and debug deepjazz abstract grammar tokens
  and note-cleanup behavior without training."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# grammar-and-qa

Use this sub-skill when a deepjazz task is about abstract grammar tokens,
`music21` note/chord roundtrips, or QA cleanup of generated notes. This is
legacy deepjazz operating knowledge, not a modern general-purpose music theory
library.

## Route here for

- Explaining `parse_melody(fullMeasureNotes, fullMeasureChords)` and
  `unparse_grammar(m1_grammar, m1_chords)` behavior.
- Diagnosing grammar tokens such as `R,0.125`, `C,0.250`, or
  `S,0.250,<M2,m-3>`.
- Running a no-training `music21` smoke check around parsing, pruning,
  unparsing, and cleanup.
- Debugging zero-length notes, adjacent duplicate notes, missing chords, or
  malformed token fields.

## Route elsewhere

- MIDI file selection, hard-coded part indices, and Metheny measure extraction
  belong to the sibling `midi-preprocessing` sub-skill.
- Corpus slicing, LSTM training, generated grammar sampling, playback, and MIDI
  writing belong to the sibling `lstm-generation` sub-skill.

## Read and run

- Read [references/grammar-reference.md](references/grammar-reference.md) when
  you need token syntax, token classes, interval-field handling, or the
  parse/unparse relationship.
- Read [references/qa-reference.md](references/qa-reference.md) when you need
  the required `prune_grammar -> unparse_grammar -> prune_notes ->
  clean_up_notes` order and structural validation signals.
- Read [references/troubleshooting.md](references/troubleshooting.md) when
  grammar unparsing fails, chords are missing, Python 2 compatibility errors
  appear, or generated notes still contain zero lengths/duplicates.
- Run [scripts/grammar_roundtrip_smoke.py](scripts/grammar_roundtrip_smoke.py)
  for a tiny deterministic-by-seed smoke check that imports only `music21` and
  avoids training, playback, downloads, network, and writes.

## Minimal safe workflow

1. Inspect the token fields with the grammar reference before editing generated
   grammar. The implementation splits tokens by commas; do not rely on compact
   comment-only interval notation.
2. If the runtime only needs a dependency/cleanup sanity check, run:

   ```bash
   python scripts/grammar_roundtrip_smoke.py --seed 7 --json
   ```

3. For generated grammar, keep the legacy order:
   `prune_grammar`, then `unparse_grammar`, then `prune_notes`, then
   `clean_up_notes`.
4. Treat exact pitches as nondeterministic. Prefer structural checks: token
   classes, element counts, valid float durations, at least one generated note,
   no zero-length notes after cleanup, and no adjacent same-offset note chords.
