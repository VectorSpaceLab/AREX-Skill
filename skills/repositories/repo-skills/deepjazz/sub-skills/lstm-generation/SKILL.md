---
name: lstm-generation
description: "Run, adapt, or modernize deepjazz's legacy LSTM generation workflow safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# deepjazz LSTM Generation

Use this sub-skill when the task is to run, adapt, troubleshoot, or modernize the legacy deepjazz LSTM generation path: preprocess grammar corpus, build/train the Keras/Theano model, generate measure grammars, prune/QA, unparse to notes, and write MIDI.

This skill distills the relevant generation and model behavior into the bundled references below. Do not depend on reading legacy source files at runtime to recover constants, APIs, or control flow.

## Route elsewhere

- For MIDI compatibility, melody/accompaniment part selection, and measure-window checks, use [`../midi-preprocessing/`](../midi-preprocessing/).
- For grammar token semantics, grammar pruning details, unparse edge cases, and QA helper behavior, use [`../grammar-and-qa/`](../grammar-and-qa/).

## Start safely

1. Use a legacy environment for faithful execution: Python 2.7, Keras 1.2.x, Theano 0.9.x, NumPy 1.16.x, and music21 3.1.x. Set `KERAS_BACKEND=theano` before importing Keras when using the legacy stack.
2. Before any training or playback-capable command, run the safe diagnostic:

   ```bash
   python scripts/legacy_generation_check.py --check-imports --show-settings --expect-theano
   ```

   To inspect API signatures in a local deepjazz-style working copy without training, playback, or writes:

   ```bash
   python scripts/legacy_generation_check.py --repo-root <deepjazz-style-root> --check-imports --show-settings --expect-theano
   ```

3. Treat full generation as side-effectful: it trains an LSTM, attempts realtime MIDI playback, and writes a MIDI file. On headless servers, use an adapted entrypoint that disables playback before invoking generation.
4. Treat Theano CUDA as a legacy optional acceleration path only. The CPU path is the safe baseline; the CUDA command requires an old NVIDIA/CUDA/Theano stack and is not verified by this skill.

## What to read or run

- Read [`references/generation-workflow.md`](references/generation-workflow.md) for the public end-to-end generation flow, legacy CPU/GPU command shapes, constants, side effects, and headless one-epoch guidance.
- Read [`references/lstm-architecture.md`](references/lstm-architecture.md) for `build_model(corpus, val_indices, max_len, N_epochs=128)`, one-hot shapes, layer stack, compile/fit parameters, and inference sampling shapes.
- Read [`references/modernization-notes.md`](references/modernization-notes.md) when porting the model to Python 3 or `tf.keras` while preserving corpus/value mappings and the grammar pipeline.
- Read [`references/troubleshooting.md`](references/troubleshooting.md) for backend mismatch, missing dependency, Python 3, Theano CUDA, playback, output-path, speed, and nondeterminism failures.
- Run [`scripts/legacy_generation_check.py`](scripts/legacy_generation_check.py) for deterministic, no-training/no-playback dependency, backend, distilled-setting, and optional signature checks.

## Core distilled facts

| Area | Legacy behavior |
| --- | --- |
| Generator API | `generate(data_fn, out_fn, N_epochs)` trains, generates, plays, then writes MIDI. |
| Default CLI epoch count | `128` if the command-line epoch argument is absent or invalid. |
| Default input | Metheny MIDI fixture path under a `midi/` directory. Route compatibility checks to `midi-preprocessing`. |
| Default output naming | `deepjazz_on_metheny...<N>_epoch(s).midi` under a `midi/` directory. Prefer explicit `.midi` output paths in adaptations. |
| Model settings | `max_len=20`, `max_tries=1000`, `diversity=0.5`. |
| Music settings | tempo marker `bpm=130`. |
| Training | Two stacked LSTM(128) layers with dropout, categorical crossentropy, RMSprop, batch size 128, `nb_epoch=N_epochs`. |
| Safety hazards | Full generation can be slow, nondeterministic, playback-dependent, and write output files. The bundled helper avoids all of those side effects. |
