# Speech Transforms and VAD Troubleshooting

## Audio / Format Errors

Symptoms:

- input file not found
- sample rate mismatch
- output file has the wrong channel count
- non-WAV format cannot be read or written

Fixes:

- validate the path first
- use the audio I/O helpers for resampling and downmixing
- install ffmpeg when you need non-WAV containers

## VAD / Turn Detection Errors

Symptoms:

- no speech is detected
- the turn never ends
- `semantic_vad` is requested
- the output starts too early or too late

Fixes:

- inspect the threshold, prefix padding, and silence duration
- confirm that `server_vad` is the requested mode
- use the probe script with synthetic probabilities before blaming the model

## Dependency Errors

Symptoms:

- `sounddevice` cannot play back audio
- `webrtcvad` complains about `pkg_resources`

Fixes:

- install PortAudio if live playback is needed
- keep `setuptools<81` for the server and STS extras that rely on `webrtcvad`

## Workflow Errors

Symptoms:

- enhancement or separation produces an unexpected path
- the model family is not detected from the repo id

Fixes:

- use the command builder to print the final command first
- confirm the model family against `references/audio-io-and-dsp.md` and the repo README
