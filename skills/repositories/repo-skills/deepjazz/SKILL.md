---
name: deepjazz
description: "Use deepjazz for legacy MIDI jazz generation with music21
  preprocessing, abstract grammar tokens, Keras/Theano LSTM training, safe
  diagnostics, and modernization guidance."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# deepjazz Repo Skill

Use this skill when a task involves the deepjazz repository or a deepjazz-style workflow: symbolic MIDI jazz generation, Metheny-style MIDI preprocessing, abstract grammar tokens, note cleanup, Keras/Theano LSTM generation, optional Theano GPU commands, or modernizing the legacy code.

This skill is self-contained. Do not rely on reading original repo scripts at runtime to recover constants, signatures, or workflow boundaries; use the bundled references and scripts below.

## First route by task

| User task | Route |
| --- | --- |
| Inspect whether a MIDI file can work with deepjazz, change melody/accompaniment parts, or debug corpus extraction | [`sub-skills/midi-preprocessing/`](sub-skills/midi-preprocessing/) |
| Explain or validate grammar tokens, run parse/unparse/cleanup smoke checks, or debug malformed generated grammar | [`sub-skills/grammar-and-qa/`](sub-skills/grammar-and-qa/) |
| Run, adapt, or port the LSTM generation path; avoid playback/training hazards; inspect model settings | [`sub-skills/lstm-generation/`](sub-skills/lstm-generation/) |
| Diagnose install/import/backend problems that cut across all workflows | [`references/troubleshooting.md`](references/troubleshooting.md) |
| Check whether this skill matches a checkout/source revision | [`references/repo-provenance.md`](references/repo-provenance.md) |

## Minimal safe start

1. Treat deepjazz as a legacy script collection, not a modern installable package.
2. For faithful execution, use a Python 2.7-era environment with NumPy/SciPy, `music21`, Keras 1.x, and Theano. Read [`references/dependency-environment.md`](references/dependency-environment.md) before installing.
3. Set `KERAS_BACKEND=theano` before importing legacy Keras.
4. Run the bundled no-training environment check:

   ```bash
   python scripts/check_deepjazz_environment.py --expect-theano
   ```

5. Validate MIDI structure before training:

   ```bash
   python sub-skills/midi-preprocessing/scripts/inspect_midi_structure.py --midi-file <input.mid>
   ```

6. Validate grammar/QA behavior without training:

   ```bash
   python sub-skills/grammar-and-qa/scripts/grammar_roundtrip_smoke.py --seed 7
   ```

7. Only run full generation after environment, data, and grammar checks pass. The original generation flow trains an LSTM, attempts realtime MIDI playback, and writes MIDI output.

## Key distilled facts

- Public source modules: `generator`, `grammar`, `preprocess`, `qa`, and `lstm`.
- Verified public signatures: `generate(data_fn, out_fn, N_epochs)`, `build_model(corpus, val_indices, max_len, N_epochs=128)`, `get_musical_data(data_fn)`, `get_corpus_data(abstract_grammars)`, `parse_melody(fullMeasureNotes, fullMeasureChords)`, `unparse_grammar(m1_grammar, m1_chords)`, `prune_grammar(curr_grammar)`, `prune_notes(curr_notes)`, `clean_up_notes(curr_notes)`.
- Default generation settings: `max_len=20`, `max_tries=1000`, `diversity=0.5`, `bpm=130`, default epochs `128`.
- The README documents CPU execution and an optional NVIDIA/Theano GPU command; CPU is the safe baseline for this skill.
- The default MIDI workflow is tailored to a Metheny fixture: melody part `5`, accompaniment parts `0,1,6,7`, and solo window offsets `476..548`.

## Shared references and scripts

- [`references/dependency-environment.md`](references/dependency-environment.md): public legacy dependency guidance and safe command sequence.
- [`references/troubleshooting.md`](references/troubleshooting.md): cross-cutting install, Python compatibility, data, playback, speed, and optional CUDA troubleshooting.
- [`references/repo-provenance.md`](references/repo-provenance.md): source commit, branch, evidence paths, and refresh baseline.
- [`references/repo-routing-metadata.json`](references/repo-routing-metadata.json): structured router metadata used only if this skill is later imported into the managed repo-skills library.
- [`scripts/check_deepjazz_environment.py`](scripts/check_deepjazz_environment.py): safe dependency/backend/module-signature diagnostic; accepts optional `--repo-root` for inspecting a local deepjazz-style source tree without training.

## Non-goals

- Do not treat this as a generic modern music-generation framework.
- Do not claim GPU verification unless a task explicitly verifies the legacy Theano CUDA path.
- Do not run full generation as a quick smoke test; use bundled no-training helpers first.
- Do not expect arbitrary MIDI files to work without adapting part and offset assumptions.
