---
name: midi-preprocessing
description: "Inspect and adapt deepjazz MIDI preprocessing, Metheny part
  assumptions, and grammar corpus extraction before LSTM generation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# deepjazz MIDI Preprocessing

Use this sub-skill when a task is about preparing or diagnosing MIDI input for deepjazz: checking whether a file matches the default Metheny assumptions, changing melody/accompaniment part selection, extracting chords and measures, or producing grammar corpus inputs for the LSTM route.

Do not rely on reading or running the original preprocessing script at runtime. This sub-skill distills the relevant behavior and provides a safe bundled inspection helper.

## Route elsewhere

- For grammar token meanings, `parse_melody`, `unparse_grammar`, pruning, and note cleanup, use [`../grammar-and-qa/`](../grammar-and-qa/).
- For Keras/Theano environment setup, LSTM training, generation constants, playback, and MIDI output writing, use [`../lstm-generation/`](../lstm-generation/).
- For cross-cutting install/import failures that affect all routes, read [`../../references/troubleshooting.md`](../../references/troubleshooting.md).

## Start with a MIDI compatibility pass

1. Make sure `music21` can parse the candidate MIDI file.
2. Run the bundled structure inspector before training or changing generator settings:

   ```bash
   python scripts/inspect_midi_structure.py --midi-file <input.mid> --melody-part 5 --accompaniment-parts 0,1,6,7 --start-offset 476 --end-offset 548
   ```

3. If the report warns that the melody part, accompaniment parts, or offset window do not contain the expected material, adapt the part indices/window before sending the file to the LSTM workflow.
4. Only after the file has plausible melody and chord material should you route to grammar extraction or generation.

## What to read or run

- Read [`references/midi-preprocessing.md`](references/midi-preprocessing.md) for the distilled `get_musical_data(data_fn)` and `get_corpus_data(abstract_grammars)` workflow, including the output objects expected by generation.
- Read [`references/data-assumptions.md`](references/data-assumptions.md) before applying deepjazz to a new MIDI file; it lists the hard-coded Metheny arrangement assumptions and what to change.
- Read [`references/troubleshooting.md`](references/troubleshooting.md) when `music21` cannot parse a file, part indices fail, no chords appear, or measure/chord lengths do not match.
- Run [`scripts/inspect_midi_structure.py`](scripts/inspect_midi_structure.py) for a deterministic, no-training/no-playback report on MIDI parts, voices, offsets, chord-like events, and selected-window warnings.

## Distilled API facts

| Function | Inputs | Returns | Notes |
| --- | --- | --- | --- |
| `get_musical_data(data_fn)` | path to a MIDI file | `(chords, abstract_grammars)` | Internally parses the MIDI, selects hard-coded parts/window, groups measures, and converts melody measures into grammar strings. |
| `get_corpus_data(abstract_grammars)` | list of grammar strings | `(corpus, values, val_indices, indices_val)` | Flattens grammar tokens for LSTM sequence modeling and builds token-index maps. |

## Boundary checklist

- Owns: file parseability, part/window discovery, melody/chord extraction assumptions, corpus inputs.
- Does not own: exact grammar token semantics, note-generation choices, model architecture, training safety, or audio playback.
- Safe validation signal: a MIDI report with parse success, plausible selected melody/accompaniment material, and clear warnings for mismatches.
