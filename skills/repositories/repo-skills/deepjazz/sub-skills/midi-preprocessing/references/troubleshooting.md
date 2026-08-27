# MIDI Preprocessing Troubleshooting

## `music21` cannot parse the file

**Symptoms**: converter errors, empty score, or no parts reported by the inspector.

**Likely causes**: invalid MIDI file, unsupported encoding, missing `music21`, or running in an incompatible Python environment.

**Recovery**:

1. Run the root environment check first.
2. Use the bundled inspector with the target file.
3. If parse still fails, convert or repair the MIDI in an external MIDI tool before using deepjazz.

## Melody part errors

**Symptoms**: no voice elements, unpacking errors, melody measure list is empty, or the selected melody part has few notes in the window.

**Likely causes**: the file is not arranged like the Metheny fixture; melody is not part `5`; the selected part stores notes directly instead of in two voices.

**Recovery**:

1. Run `inspect_midi_structure.py --midi-file <file> --json` and compare part summaries.
2. Choose a melody part with a meaningful note/rest count and offset coverage.
3. If there are no `Voice` elements, adapt preprocessing to collect notes/rests directly from the part's flattened stream.

## No chords or harmony context

**Symptoms**: grammar parsing fails, generated notes sound arbitrary, or chord lists are empty.

**Likely causes**: wrong accompaniment parts, accompaniment outside the selected offset window, or the MIDI uses note clusters rather than `music21.chord.Chord` objects after parsing.

**Recovery**:

1. Inspect chord-like event counts for each part.
2. Try a wider or shifted offset window.
3. If needed, derive chords from simultaneous notes before calling grammar parsing.

## Measure/chord length assertion failure

**Symptoms**: preprocessing asserts that measure and chord counts differ.

**Likely causes**: the legacy code expects the accompaniment to resolve one measure after the melody and deletes the last chord measure. Other files may not share this shape.

**Recovery**:

1. Inspect min/max offsets for melody and accompaniment.
2. Align the solo window so both melody and chord material start/end together.
3. If mismatch remains, adapt the parser to intersect measure keys instead of assuming one final extra chord measure.

## Corpus too small for LSTM settings

**Symptoms**: sequence slicing produces no training sentences when `max_len=20`, or training fails on empty arrays.

**Likely causes**: short solo window, too few grammar tokens, or too much material filtered out.

**Recovery**:

1. Expand the selected offset window.
2. Use more measures or multiple compatible solos.
3. Lower `max_len` only if you also adjust generation expectations in the LSTM route.
