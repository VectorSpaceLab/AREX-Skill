# Troubleshooting

## Import or Version Failures

Symptoms:

- `import mlx_audio` fails
- `import mlx.core` fails
- `mlx_lm` appears in a core import path
- a CLI starts but imports optional speech dependencies too early

Likely causes:

- mismatched `mlx` build or wheel
- missing optional extras for the selected workflow
- stale editable install or incompatible dependency set

Checks:

```bash
python scripts/check_install.py
python scripts/check_optional_deps.py
```

## Playback or Audio Device Errors

Symptoms:

- `sounddevice` cannot open the default device
- PortAudio is missing
- streaming audio works but playback does not

Fixes:

- install PortAudio on the host
- use file output instead of live playback
- keep `--stream` and `--save` separate from playback assumptions when debugging

## Optional Dependency Errors

Symptoms:

- `mistral-common[audio]` missing
- `sentencepiece` missing
- `fastapi`, `uvicorn`, or `python-multipart` missing
- `webrtcvad` complains about `pkg_resources` / setuptools

Fixes:

- install the extra that matches the task
- keep `setuptools<81` for the server and STS extras that depend on `webrtcvad`
- keep `mlx_lm` limited to the optional speech-to-speech responder path
- treat the warning as a dependency mismatch, not as a model bug

## Audio Format and Sample-Rate Errors

Symptoms:

- bad transcription quality
- silent output
- clipped or sped-up audio
- `FileNotFoundError` for reference audio paths

Fixes:

- validate the input path first
- confirm the sample rate expected by the model or server route
- use the audio I/O helper functions for resampling and channel conversion
- prefer WAV fixtures when debugging

## Model Download or Cache Failures

Symptoms:

- Hub download fails
- the model id is wrong
- a long job starts before the model is confirmed available

Fixes:

- verify the model id with the sub-skill references before launching a long run
- preflight with `--help` and the bundled builder scripts
- treat the generated skill as documentation and command planning, not as a guarantee that every weight file is cached locally
