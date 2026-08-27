# Grammar reference

Deepjazz stores one measure of melody as a whitespace-separated abstract grammar
string. The helpers operate on `music21` objects: melody and chord inputs are
`stream.Voice` instances containing `note.Note`/`note.Rest` and `chord.Chord`
elements, and unparsing returns another `stream.Voice` of generated
`note.Note`/`note.Rest` elements.

## Public helper contract

| Helper | Input | Output | What it does |
| --- | --- | --- | --- |
| `parse_melody(fullMeasureNotes, fullMeasureChords)` | A melody `stream.Voice` and a chord `stream.Voice`. Non-note/rest melody elements and non-chord accompaniment elements are ignored. | Grammar string for one measure. | Classifies each note/rest against the last chord at or before its offset and records duration plus optional interval range fields. |
| `unparse_grammar(m1_grammar, m1_chords)` | Grammar string and measure-local chord `stream.Voice`. | Generated `stream.Voice` containing `note.Note` and `note.Rest`. | Regenerates notes/rests from token classes, durations, current chord, and optional interval ranges. |

These helpers are a compact, repo-specific representation for deepjazz's legacy
jazz generation loop. They are not a full music theory abstraction layer.

## Token field shape

A measure grammar is split first on spaces, then each token is split on commas.
Use these runtime-safe forms:

```text
TYPE,DURATION
TYPE,DURATION,<UPPER_INTERVAL,LOWER_INTERVAL>
```

Examples:

```text
R,0.125
C,0.250
S,0.250,<M2,m-3>
A,0.125,<m2,M-2>
X,0.250,<P4,m-2>
```

Important notation quirk: some legacy comments describe compact interval text
such as `C,0.125<M-2,m-6>`. Treat that as explanatory prose only. The runtime
code does `grammarElement.split(',')` and then parses `terms[1]` as a float, so
an interval-bearing token must keep the interval terms in later comma-separated
fields, for example `C,0.125,<M-2,m-6>`.

`DURATION` is a `music21` `quarterLength` value serialized as a decimal string;
it is a duration, not an offset. Malformed strings fail when converted with
`float(terms[1])`.

## Token classes

| Class | Meaning in `parse_melody` | Generation behavior in `unparse_grammar` |
| --- | --- | --- |
| `R` | `note.Rest`. | Inserts a `note.Rest` with the token duration. |
| `C` | The note pitch name is in the current chord, or the element is already a chord. | Chooses a chord tone from the current chord. |
| `S` | The note name is in a chord-derived scale. Major chords use a major scale; non-major chords use a Dorian-style check during parsing. | Chooses a scale tone. Major chords use a major scale; non-major chords use the legacy weighted blues-scale generator. |
| `A` | The note is one semitone above or below a chord tone, including enharmonic spellings. | Chooses an approach tone, constrained by interval fields when present. |
| `X` | Catch-all when the note is neither rest, chord tone, scale tone, nor approach tone. | Treated like the approach-tone branch in the legacy unparser. |

The main generation loop may collapse generated `A` and `X` labels to `C`
before pruning/unparsing. This sub-skill still documents `A` and `X` because
`parse_melody` can emit them and the unparser has fallback behavior for them.

## Parse behavior to remember

1. The melody voice is copied and filtered down to `note.Note` and `note.Rest`.
   The chord voice is copied and filtered down to `chord.Chord`.
2. For each melody element, the current chord is the last chord whose offset is
   at or before the element offset.
3. If no chord is found before the element and the chord voice is non-empty, the
   first chord is shifted to the measure start as a fallback. If the chord voice
   is empty, grammar parsing has no meaningful harmonic context.
4. The first non-rest note stores no interval range. Later non-rest notes store
   an interval range built from the previous non-rest note plus/minus a minor
   third; rests do not update the previous-note memory.
5. The duration stored in the token is the element's `quarterLength`, not the
   computed distance to the next element.

## Unparse behavior to remember

1. Each token must provide a parseable duration in `terms[1]`.
2. `currOffset` is incremented by the token duration before insertion. The first
   returned element can therefore appear at the first accumulated duration
   rather than offset `0.0`; this mirrors the legacy helper.
3. If a non-rest token has no interval fields, the helper chooses from the
   current chord/scale/approach-tone class. Octaves below the legacy floor are
   raised.
4. If interval fields are present, they are parsed as two `music21.interval`
   objects. The helper orders them by cents, constructs a low/high pitch range
   around the previous generated note, then randomly chooses a class-compatible
   note in that range. If no compatible note exists, it falls back to moving the
   previous note by a whole step.
5. Interval-bearing tokens require a previous generated note. A grammar whose
   first non-rest token already has interval fields is malformed for this
   unparser.

## What a roundtrip does and does not prove

A parse/unparse roundtrip checks that the token structure can be interpreted by
`music21` and deepjazz-style chord logic. It does not prove exact melody
reconstruction. Pitch choices are intentionally random in the unparser, and
cleanup can change durations or remove elements. Prefer structural assertions:
valid token fields, token classes present, note/rest counts, positive
quarterLength after cleanup, and absence of same-offset duplicate notes.
