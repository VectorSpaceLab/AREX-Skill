# MIDI Preprocessing Workflow

## Purpose

Read this when you need to explain or adapt how deepjazz turns a MIDI file into chord streams and abstract grammar strings before LSTM training.

## High-level flow

The preprocessing route has two public functions:

1. `get_musical_data(data_fn)`
   - Parses a MIDI file with `music21.converter.parse(data_fn)`.
   - Selects one melody part and a small set of accompaniment parts.
   - Restricts the material to a solo window.
   - Groups melody notes/rests and accompaniment chords into 4-quarter-note measures.
   - Calls the grammar route to convert each melody measure and chord measure into an abstract grammar string.
   - Returns `chords, abstract_grammars`.
2. `get_corpus_data(abstract_grammars)`
   - Splits every grammar string on spaces.
   - Flattens all tokens into `corpus`.
   - Builds `values = set(corpus)`.
   - Builds `val_indices` and `indices_val` dictionaries for one-hot sequence modeling.
   - Returns `corpus, values, val_indices, indices_val`.

## Metheny-specific extraction logic

The legacy implementation is not a general MIDI parser. It is tailored to the bundled Pat Metheny arrangement:

- Melody part index: `5`.
- Accompaniment part indices: `0, 1, 6, 7`.
- Verified chord source: the first accompaniment stream after flattening.
- Solo offset window: from `476` to `548`, with the end boundary included.
- Measure grouping: `int(offset / 4)`.
- Extra annotations inserted into melody: electric guitar instrument and key signature with one sharp/major mode.
- Zero-length melody events are normalized to quarter length `0.25` before grammar extraction.

For a different MIDI file, these indices and offsets are the first values to inspect and change. The bundled inspector helps identify whether candidate parts contain notes, voices, chords, and offsets in the requested window.

## Expected object shapes

| Object | Shape/meaning | Downstream consumer |
| --- | --- | --- |
| `measures` | ordered mapping from measure number to melody notes/rests | grammar parser |
| `chords` | ordered mapping from measure number to chord events | grammar parser and generator |
| `abstract_grammars` | list of space-delimited grammar strings, one per selected measure except the initial setup measure | LSTM corpus builder |
| `corpus` | flattened list of grammar tokens | LSTM sequence slicer |
| `values` | unique grammar tokens | one-hot feature dimension |
| `val_indices` | token to integer index | training matrix construction |
| `indices_val` | integer index to token | model prediction decoding |

## Safe adaptation recipe

1. Parse the candidate file with the bundled inspector.
2. Find the part that has the melody notes you want deepjazz to model.
3. Find accompaniment parts that contain enough chord-like events over the same offset window.
4. Choose a start/end offset that contains a coherent solo section and both melody/chord material.
5. Confirm that grouping by `int(offset / 4)` gives matching measure/chord coverage.
6. Only then adapt the preprocessing code or write a small wrapper that passes the chosen indices/window into a generalized copy of the parser.

If the goal is simply to generate from a Metheny-style fixture, keep the defaults and route to [`../../lstm-generation/`](../../lstm-generation/) after dependency checks.
