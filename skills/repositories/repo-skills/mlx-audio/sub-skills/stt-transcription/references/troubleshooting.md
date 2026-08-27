# STT Troubleshooting

## Audio Path or Format Errors

Symptoms:

- file not found
- sample rate mismatch
- empty or garbled transcript

Fixes:

- verify the input path first
- use the audio I/O helpers to resample or downmix when needed
- keep a tiny WAV fixture for debugging

## JSON and Kwarg Problems

Symptoms:

- `--gen-kwargs` fails to parse
- a kwarg is ignored by the model
- the model rejects unsupported generation options

Fixes:

- validate the JSON before the run
- compare requested kwargs with the model's accepted signature
- use the command builder to normalize the final CLI call

## Alignment Problems

Symptoms:

- transcript and audio do not match
- forced alignment output is poor or empty

Fixes:

- only use `--text` when you truly have a transcript to align
- compare the transcript against the spoken words, not a rough summary
- if the model family does not support alignment, use ordinary ASR instead

## Hotword / Context Problems

Symptoms:

- hotwords have no effect
- the wrong prompt field is being used

Fixes:

- check the model family's native prompt field in the source tests and docs
- prefer `--context` for supported models and keep the text concise

## Evaluation Problems

Symptoms:

- WER output is empty or inconsistent
- the evaluation CLI tries to do too much at once

Fixes:

- start with the bundled WER helper on a tiny fixture
- then move to the dataset-backed eval CLI once the transcription path is stable
