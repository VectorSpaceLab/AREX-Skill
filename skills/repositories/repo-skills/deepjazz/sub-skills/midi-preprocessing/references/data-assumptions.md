# Data Assumptions

## When to read

Read this before using a MIDI file other than the default Metheny fixture, or when a preprocessing run fails with missing voices, missing chords, or mismatched measure/chord counts.

## Assumptions inherited from deepjazz

| Assumption | Why it matters | How to validate or adapt |
| --- | --- | --- |
| The melody is in part index `5`. | The legacy parser indexes directly into the parsed stream; a different file may put melody elsewhere. | Run `scripts/inspect_midi_structure.py` and compare note counts/offset ranges across parts. |
| The selected melody part has two `stream.Voice` elements. | The parser merges the second voice into the first. A part without voices raises unpacking or indexing failures. | Inspect voice counts; if the file has flat notes instead, adapt the parser to use notes directly. |
| Useful accompaniment is in parts `0,1,6,7`. | Chord extraction only sees the selected accompaniment streams. | Inspect chord-like event counts per part and choose parts with harmonic material. |
| The solo section is between offsets `476` and `548`. | Measure grouping and training corpus are built only from this window. | Pick a window that contains both melody and accompaniment for the new file. |
| Four quarter lengths make a measure. | The parser groups events with `int(offset / 4)`. | Confirm the file is effectively in a compatible meter or adapt grouping. |
| The final chord measure may be one measure longer than melody. | The legacy parser deletes the last chord measure before asserting equal lengths. | If mismatch persists after deleting the last chord measure, inspect window boundaries. |
| `music21` can parse the MIDI consistently. | All downstream objects are `music21` streams, notes, rests, and chords. | Fix file format issues before training; do not treat an LSTM error as a data-parse error. |

## Compatibility decision tree

1. **Parse failure**: fix/install `music21`, validate the MIDI file, or convert it with a MIDI editor before using deepjazz.
2. **No melody voice at part 5**: inspect all parts, choose a new melody part, and adapt the parser.
3. **No chord-like accompaniment**: choose different accompaniment parts or derive chords separately; the grammar unparser depends on chord context.
4. **Measure/chord mismatch**: adjust offsets and measure grouping before training.
5. **Very short corpus**: use a longer solo window; an LSTM sequence length of `20` needs more than 20 grammar tokens.

## What not to assume

- A random MIDI file will work with the original script unchanged.
- The highest note-count part is necessarily the melody.
- CPU/GPU training failures prove MIDI compatibility; validate data first.
- Realtime playback success is required for preprocessing; it belongs to the generation route.
