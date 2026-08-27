# TTS Model Combinations and Training Recipes

## Acoustic Models

Common acoustic model families:

- `speedyspeech_csmsc`: lightweight Chinese SpeedySpeech.
- `fastspeech2_csmsc`: common Chinese FastSpeech2 default.
- `fastspeech2_ljspeech`: English LJSpeech.
- `fastspeech2_aishell3`: Chinese multi-speaker AISHELL-3, requires `--spk_id`.
- `fastspeech2_vctk`: English multi-speaker VCTK, requires `--spk_id`.
- `fastspeech2_mix`: Chinese/English mixed text; use `--lang mix` for mixed mode.
- `fastspeech2_male`: male voice variants for zh/en/mix.
- `fastspeech2_canton`: Cantonese.
- `tacotron2_csmsc`, `tacotron2_ljspeech`: Tacotron2 variants.

## Vocoders

Common vocoders:

- Chinese: `hifigan_csmsc`, `pwgan_csmsc`, `mb_melgan_csmsc`, `style_melgan_csmsc`, `wavernn_csmsc`.
- English: `hifigan_ljspeech`, `pwgan_ljspeech`, `hifigan_vctk`, `pwgan_vctk`.
- Multi-speaker/other: `hifigan_aishell3`, `pwgan_aishell3`, `hifigan_male`, `pwgan_male`.

Pair AM and VOC by language, dataset, or documented compatibility. A Chinese AM with an English vocoder or incompatible frontend assets can fail or produce poor audio.

## Frontend and Dictionaries

Pretrained defaults download phones, tones, speaker maps, stats, configs, and checkpoints. Custom runs need the same resources:

- `phones_dict`: phone vocabulary.
- `tones_dict`: tone vocabulary for tone-aware Chinese/Cantonese frontends.
- `speaker_dict`: speaker id map for multi-speaker models.
- `am_stat` and `voc_stat`: normalization statistics.
- AM/VOC configs and checkpoints.

Route text normalization, G2P, and MFA preparation to `../text-processing/SKILL.md` when the user needs to build those assets.

## Recipe Structure

Dataset recipes such as CSMSC, LJSpeech, AISHELL-3, VCTK, Cantonese, OpenCPOP, and mixed Chinese-English typically include stages for:

1. Data preparation and metadata generation.
2. Feature extraction and statistics.
3. Acoustic model training.
4. Vocoder training or use of a pretrained vocoder.
5. Waveform synthesis from text or a text file.
6. Static/ONNX/Paddle Lite export for deployment.

Do not run staged recipes by default. They download datasets/models and can require GPUs, external aligners, or long training.

## Advanced Workflows

- **Voice cloning / VC**: examples combine speaker encoders or GE2E with TTS models. Treat as advanced and data/model-download heavy.
- **SVS / singing voice synthesis**: uses specialized datasets and recipe stages; not a simple `paddlespeech tts` invocation.
- **Streaming synthesis**: belongs in `../deployment-serving/SKILL.md` after choosing compatible online/ONNX TTS model settings.
