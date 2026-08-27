# Troubleshooting

Use this table when the legacy LSTM generation path fails during environment setup, import, training, generation, playback, or MIDI write.

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| Keras backend mismatch | `KERAS_BACKEND` is not set to Theano before import, or the environment is using a different backend | Set `KERAS_BACKEND=theano` before importing Keras and rerun the safe diagnostic. |
| Missing `keras`, `theano`, `music21`, or `numpy` | Legacy dependencies are not installed in the active environment | Install the legacy stack in an isolated compatible environment before training. |
| Python 3 import or syntax failure | Legacy code uses `xrange`, `itertools.izip_longest`, `nb_epoch`, or `np.bool` | Use Python 2.7 for faithful execution or modernize the code path using the migration notes. |
| Theano GPU/CUDA errors | Old Theano CUDA flags are being used on an unsupported modern stack or on a nonmatching GPU setup | Treat GPU execution as optional and legacy-only; fall back to CPU unless you have a validated old NVIDIA/Theano stack. |
| Realtime playback fails | The environment is headless or lacks an audio/MIDI playback device | Disable playback in the orchestration layer before generation. Keep MIDI writing separate from playback. |
| MIDI file appears in the wrong place | The output path is implicit, relative, or missing the expected extension | Pass an explicit output filename ending in `.midi`. Avoid relying on default relative directories. |
| Training is slow | The model trains on a legacy backend and uses a nontrivial corpus windowing loop | Reduce epochs for inspection, use the safe diagnostic first, and only train when you need a full generation sample. |
| Output varies across runs | Random seed, sampling temperature, and vocabulary-order effects differ between executions | Expect some nondeterminism; if you need reproducibility, fix seeds and preserve the exact corpus/value mapping. |
| Generated grammar starts badly | The first sampled token is a rest or malformed token | This is handled by the legacy retry loop; if failures persist, investigate the grammar/token pipeline in `grammar-and-qa`. |
| Value/index mismatch | `val_indices` does not match the corpus vocabulary used to build tensors | Rebuild the corpus and the mappings together, then retrain. |

## Safety reminders

- Do not use the bundled diagnostic to train or play audio.
- Do not assume the optional GPU command is verified on modern CUDA.
- If a problem is really about MIDI part selection or grammar token meaning, route it to the dedicated sub-skills instead of patching generation first.
