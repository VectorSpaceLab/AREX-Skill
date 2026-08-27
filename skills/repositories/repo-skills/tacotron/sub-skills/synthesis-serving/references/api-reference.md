# Synthesis API and service

## `Synthesizer`

`Synthesizer.load(checkpoint_path, model_name='tacotron')` creates a TensorFlow
graph with integer input placeholders, initializes the model for inference,
constructs TensorFlow Griffin-Lim reconstruction, opens a session, and restores
the checkpoint. `Synthesizer.synthesize(text)` runs the configured cleaners,
feeds the resulting ids, performs inference, inverse-preemphasizes and endpoint-
trims the waveform, and returns WAV bytes in memory.

A `Synthesizer` instance must be loaded before `synthesize`. It is not a stateless
function and should be reused for multiple requests rather than rebuilt per
request.

## Evaluation outputs

`eval.py` contains a fixed list of example sentences. `get_output_base_path`
places outputs beside the checkpoint and names them `eval-<step>-N.wav` when the
checkpoint path contains `.ckpt-<digits>`, otherwise `eval-N.wav`. It writes
one WAV per sentence.

## Falcon demo endpoints

- `GET /` returns a small HTML form.
- `GET /synthesize?text=...` returns `audio/wav` bytes.
- Missing or empty `text` raises a Falcon bad-request response.

The script's WSGI server defaults to port 9000 and listens on all interfaces.
Treat that as a local demo default, not a hardened production service.
