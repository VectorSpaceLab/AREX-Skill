# Generation Workflow

This reference distills the legacy deepjazz generation path into a safe, replayable operating summary.

## Public workflow

1. **Prepare a compatible environment**
   - Use the legacy stack for faithful behavior: Python 2.7, Keras 1.2.x, Theano 0.9.x, music21 3.1.x, NumPy 1.16.x, and a backend set to Theano.
   - In a deepjazz-style working copy, the historical entrypoint is the generator module with an epoch argument. Do not use that playback-capable path as a smoke test; run the bundled diagnostics first and adapt playback out before full generation on headless systems.
   - The historical optional GPU mode adds Theano flags equivalent to `mode=FAST_RUN`, `device=gpu`, and `floatX=float32` before launching the generator entrypoint.
   - The GPU path is a legacy optional acceleration path only. It depends on an old NVIDIA/Theano/CUDA stack and should be treated as unverified unless you explicitly test it.

2. **Preprocess the MIDI/corpus**
   - The generation path expects preprocessing to provide:
     - `chords`
     - `abstract_grammars`
     - `corpus`
     - `values`
     - `val_indices`
     - `indices_val`
   - The grammar/corpus construction is part of the preprocessing path. Part selection, measure-window selection, and MIDI compatibility belong in `midi-preprocessing`.

3. **Build the model**
   - Call `build_model(corpus, val_indices, max_len, N_epochs=128)`.
   - The generator uses `max_len=20`.
   - The architecture is a 2-layer stacked LSTM with dropout and a softmax output over the token vocabulary.

4. **Train**
   - Fit the model on one-hot sequence/label data built from the corpus.
   - Legacy `nb_epoch` is used in the original Keras 1.x API.
   - Training is deterministic only in a limited sense; random sampling and backend behavior still affect output.

5. **Generate measure grammars**
   - Start from a random seed window from the corpus.
   - Use the model to predict the next token repeatedly until the approximate measure-length threshold is reached.
   - Legacy generation parameters:
     - `max_len = 20`
     - `max_tries = 1000`
     - `diversity = 0.5`
   - The first generated token must not be a rest and must have the expected token structure; otherwise the code retries up to `max_tries` and falls back to a random first token.

6. **Prune and QA**
   - Replace invalid chord spellings in the grammar stream as needed.
   - Apply grammar pruning, unparse to notes, prune notes, and clean up notes.
   - Grammar token semantics and pruning internals are covered by `grammar-and-qa`.

7. **Write MIDI**
   - Insert notes and chords into a `music21` stream.
   - Add a tempo mark at `bpm=130`.
   - The original flow then attempts realtime playback and writes a MIDI file.

## Shape and side effects

- **Sequence input shape**: `(batch, max_len, vocab_size)`.
- **Label shape**: `(batch, vocab_size)`.
- **Generation input shape**: `(1, max_len, vocab_size)`.
- **Output side effects**:
  - realtime playback attempt
  - MIDI file write
  - console logging of corpus length, value count, sequence count, and pruning counts

## Headless one-epoch guidance

If you need to run a single epoch on a headless server, do not invoke a playback-dependent path unmodified. Use an adapted entrypoint that disables the realtime `StreamPlayer.play()` call before generation, then run the same train/generate/write sequence without audio output.

A safe adaptation pattern is to make playback optional in the orchestration layer, not to change the corpus/value mappings or the grammar pipeline.

## Output naming

- Historical default input: `midi/original_metheny.mid`.
- Historical default output pattern: `midi/deepjazz_on_metheny...<N>_epoch(s).midi`.
- In modernized runs, prefer an explicit output filename ending in `.midi` to avoid accidental writes into an unexpected directory or extension mismatch.

## Verification checkpoints

- Environment imports succeed with the expected legacy backend.
- Corpus/value mappings are present and consistent.
- `build_model` receives the exact vocabulary mapping used to create the training tensors.
- Playback is disabled or intentionally allowed.
- The final output path is explicit and ends with `.midi`.
