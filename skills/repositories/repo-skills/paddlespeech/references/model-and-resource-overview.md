# Model and Resource Overview

## Model Tags

PaddleSpeech model resources are keyed by task and tag. The public CLIs construct full tags from command options, for example:

- ASR: `conformer_wenetspeech-zh-16k`, `transformer_librispeech-en-16k`, `conformer_talcs-codeswitch_zh_en-16k`.
- TTS acoustic models: `fastspeech2_csmsc-zh`, `fastspeech2_ljspeech-en`, `fastspeech2_mix-mix`, `fastspeech2_canton-canton`.
- TTS vocoders: `hifigan_csmsc-zh`, `pwgan_ljspeech-en`, `mb_melgan_csmsc-zh`.
- Text punctuation: `ernie_linear_p7_wudao-punc-zh`, `ernie_linear_p3_wudao_fast-punc-zh`.
- Audio classification: `panns_cnn14-32k`, `panns_cnn10-32k`, `panns_cnn6-32k`.
- Speaker vector: `ecapatdnn_voxceleb12-16k`.
- KWS: `mdtc_heysnips-16k`.
- Whisper: `whisper-<size>-16k` or `whisper-<size>-en-16k`.

Use the task sub-skills for exact CLI options and compatibility notes.

## Model Aliases

The resource layer maps model aliases to import classes. Useful examples:

- ASR aliases such as `conformer`, `conformer_online`, `transformer`, and `deepspeech2offline` resolve to speech-to-text model classes.
- TTS aliases such as `fastspeech2`, `speedyspeech`, `tacotron2`, `pwgan`, `mb_melgan`, `hifigan`, and `wavernn` resolve to acoustic/vocoder classes.
- `ernie_linear_p7`, `ernie_linear_p3`, and `ernie_linear_p3_wudao` resolve to punctuation restoration model/tokenizer classes.
- `ecapatdnn` resolves to the speaker-vector model.
- `mdtc` and `mdtc_for_kws` resolve to keyword spotting classes.

If `CommonTaskResource.set_task_model` raises `Can't find ... in resource`, the CLI options probably formed a tag that does not exist. Check `paddlespeech stats --task <task>` when the stats command supports the task, or use the model/tag tables in the owning sub-skill references.

## Resource Downloads

`CommonTaskResource.set_task_model` downloads model archives unless the caller provides complete local config/checkpoint paths or passes a path mode that skips download. Downloads are validated with md5 when metadata provides one and are decompressed under the model cache.

For model-download runs, prepare:

- Enough disk for large archives. Whisper and some ASR models can be hundreds of MB to several GB.
- Stable network access to PaddleSpeech/Baidu BOS URLs.
- A cache root via `PPSPEECH_HOME` when the default user cache is not desired.
- Matching custom config/checkpoint/stat/dict files when bypassing pretrained downloads.

## Static, ONNX, and Runtime Models

PaddleSpeech distinguishes dynamic, static, and ONNX model registries for some tasks. Use dynamic models for ordinary Python executor workflows, static/Paddle Inference configs for inference engine server modes, and ONNX tags for TTS ONNX/streaming flows.

Do not mix a dynamic checkpoint with a static model config or ONNX session setting. Static and ONNX flows require the corresponding exported model files and predictor/session config fields.
