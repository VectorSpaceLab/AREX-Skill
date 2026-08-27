# Troubleshooting grammar and QA failures

Use this reference when a generated grammar string fails to unparse or when the
post-unparse note stream still has cleanup problems. Keep MIDI routing and LSTM
training issues in their sibling sub-skills unless the symptom is specifically
about grammar tokens or note QA.

| Symptom | Likely cause | What to check | Repair or route |
| --- | --- | --- | --- |
| `ValueError` converting a duration to float, or a token such as `C,0.125<M-2,m-6>` fails to unparse. | The token uses compact comment notation or otherwise merges duration and interval text into one field. | Split the token by commas. Runtime-safe tokens are `TYPE,DURATION` or `TYPE,DURATION,<UPPER,LOWER>`, so `terms[1]` must be only a float string. | Normalize to `C,0.125,<M-2,m-6>` style. If many tokens are malformed, locate the upstream grammar generator before cleanup. |
| Interval parse error, or an interval-bearing first token crashes. | The unparser expects interval fields only after a previous generated non-rest note exists. | Check the first non-rest token. It should usually have only two fields, such as `C,0.250`. | Remove interval fields from the first non-rest token or regenerate the measure seed. |
| Missing chord, empty chord voice, or index error near current offset. | The grammar helper looks for the last `chord.Chord` at or before the current note offset. It can shift the first non-empty chord to the measure start, but it cannot recover from an empty chord voice. | Confirm the measure-local chord `stream.Voice` contains at least one `chord.Chord`, ideally at offset `0.0`, and that chord offsets are comparable to note offsets. | Insert/repair the measure chord voice. If the chords are missing because the MIDI parts were selected incorrectly, route to `midi-preprocessing`. |
| The generated grammar starts with `R` or the first token has interval fields. | The deepjazz generation loop tries to prevent the first generated token from being a rest and from having interval fields, retrying before falling back to a corpus first token. | Check whether the grammar came from the LSTM sampling loop or was hand-edited. | For model-loop causes, route to `lstm-generation`; for hand-edited grammar, replace the first token with a two-field non-rest token. |
| `NameError: xrange` or `ImportError: izip_longest` under Python 3. | The legacy source was written for Python 2.7. | Look for `xrange` in interval note generation and `izip_longest` in QA pairing code. | Use the bundled smoke script for Python 2/3-safe structural checks, or run the original legacy helpers only in a Python 2.7-compatible environment. |
| Exact pitches change across runs even when the grammar looks the same. | The unparser and duration pruner use random choices; source candidate lists can also depend on set order. | Compare token classes, counts, offsets, durations, and cleanup invariants rather than pitch names. | Re-run with a seed for debugging, but do not treat exact pitches as stable acceptance criteria. |
| Zero-length notes remain after cleanup. | `clean_up_notes` did not run, ran before unparsing, or the sequence was not the one that later got inserted. | Check the pipeline order: `prune_grammar -> unparse_grammar -> prune_notes -> clean_up_notes`. Inspect every retained element's `quarterLength`. | Re-run cleanup on the final unparsed sequence. If zero durations came from `prune_grammar`, this is expected before cleanup. |
| Adjacent duplicate pitches or same-offset note-note pairs remain. | `prune_notes` only removes adjacent same-pitch pairs; `clean_up_notes` only removes later adjacent notes with identical offsets. Unsorted or interleaved sequences can hide duplicates. | Sort or inspect by offset. Check pairs of consecutive `note.Note` elements after each QA stage. | Run `prune_notes` before `clean_up_notes`; sort/copy the sequence carefully if you constructed it outside the normal unparser. |

## Fast sanity check

Run the bundled helper when you only need to validate `music21` importability and
the grammar/QA control flow:

```bash
python scripts/grammar_roundtrip_smoke.py --seed 7 --json
```

The helper is intentionally tiny: it constructs synthetic `music21` voices,
parses/prunes/unparses them, exercises cleanup fixtures, and prints structural
signals. It does not train, play audio, parse MIDI files, download data, or
write output files.
