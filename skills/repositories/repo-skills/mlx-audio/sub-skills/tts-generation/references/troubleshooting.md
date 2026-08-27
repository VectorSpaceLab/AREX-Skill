# TTS Troubleshooting

## Missing or Wrong Dependency Surface

Symptoms:

- `mistral-common[audio]` missing
- `sentencepiece` missing
- `sounddevice` import or playback errors

Fixes:

- install the `tts` extra for TTS families that depend on audio tokenization
- install PortAudio if live playback is needed
- use `--help` and the command builder before a long run

## Voice Cloning Failures

Symptoms:

- cloned voice sounds wrong
- reference text and reference audio do not match
- `FileNotFoundError` for a reference path

Fixes:

- confirm the transcript matches the actual clip
- keep the clip short, clean, and conversational
- for OmniVoice, transcribe the preprocessed clip rather than the raw recording
- for models that accept a transcript, provide it explicitly instead of relying on auto-transcription

## Streaming / Save Confusion

Symptoms:

- `--save` errors out
- chunked audio is written when a single file was expected
- playback happens when the user expected only files

Fixes:

- `--save` requires `--stream`
- use `--join_audio` when you want one file from multiple segments
- remember that streaming and playback are coupled by the CLI defaults

## Model-Specific Kwarg Errors

Symptoms:

- the model rejects an unfamiliar argument
- a TTS family-specific control is silently ignored

Fixes:

- confirm the model family in `references/model-overview.md`
- compare the requested kwargs against `references/api-reference.md`
- keep unsupported knobs out of the initial command plan
