# Workflows

## MMSpeech stages

The repo scripts split MMSpeech into stages. The exact stage names can vary between checkpoints, but the broad pattern is:

1. Stage 1: initial speech-text or text-heavy pretraining.
2. Stage 2: mixed speech/audio/text training.
3. Stage 3: later-stage refinement or evaluation setup.

## Manifest layout

The manifest is a three-column TSV of:

- speech ID,
- audio path,
- text.

The repo's evaluation script also uses `speech_text_selected_cols=0,1,2`.

## Feature extraction inputs

- A `config_yaml_path` controls the fbank feature extraction.
- The audio path must exist and should match the expected sample rate.
- If the repo uses a phone dictionary or text-to-phone path, those files must exist too.

## Evaluation

- The evaluation route can compute WER.
- The command may need `train_stage`, `valid_data`, and `eval_wer` overrides.
- The speech helper is most useful when you want to validate the manifest before the GPU run.
