# Audio and Music Configuration

## Purpose

Read this when you need to edit the YAML files or understand which paths the audio/music demos consume.

## Audio config fields

The audio demo reads `configs/lumina-text2audio.yaml` and expects the checkpoint paths inside the nested `model.params` structure to be updated.

The important fields are:

- `model.params.first_stage_config.params.ckpt_path`
- `model.params.cond_stage_config.params.weights_path`

The README examples show these fields being set to the local `maa2` and `CLAP` assets under the downloaded checkpoint root.

## Music config fields

The music demo reads `configs/lumina-text2music.yaml` and uses the same `first_stage_config` style path update for the `maa2` checkpoint.

## Structure-caption helper

`n2s_openai.py` contains a placeholder API key and optional proxy base URL.
Treat those fields as user-specific secrets and set them locally before running the audio demo.

## Common checkpoints

- `ckpt`: the model root for `audio_generation/` or `music_generation/`
- `vocoder_ckpt`: the `bigvnat/` folder
- `sample_rate`: documented at `16000`

## Validation intent

The audio/music checker should confirm that the config fields are present and that the referenced folders exist beneath the chosen checkpoint root when a resolved root is supplied.
