# TTS CLI and API

## Basic CLI

```bash
paddlespeech tts --input "你好，欢迎使用百度飞桨深度学习框架！" --output output.wav
paddlespeech tts --am speedyspeech_csmsc --voc pwgan_csmsc --lang zh --input "你好" --output speedyspeech.wav
paddlespeech tts --am fastspeech2_ljspeech --voc hifigan_ljspeech --lang en --input "Hello world." --output en.wav
paddlespeech tts --am fastspeech2_mix --voc hifigan_csmsc --lang mix --spk_id 174 --input "中文 and English." --output mix.wav
```

Key options:

- `--input`: text to synthesize. Use quotes for spaces.
- `--am`: acoustic model, such as `fastspeech2_csmsc`, `speedyspeech_csmsc`, `fastspeech2_ljspeech`, `fastspeech2_aishell3`, `fastspeech2_vctk`, `fastspeech2_mix`, `fastspeech2_male`, `fastspeech2_canton`, `tacotron2_csmsc`, or `tacotron2_ljspeech`.
- `--voc`: vocoder, such as `hifigan_csmsc`, `pwgan_csmsc`, `mb_melgan_csmsc`, `hifigan_ljspeech`, `pwgan_ljspeech`, `hifigan_aishell3`, `pwgan_aishell3`, `hifigan_vctk`, `pwgan_vctk`, `pwgan_male`, or `hifigan_male`.
- `--lang`: `zh`, `en`, `mix`, or `canton` depending on the model.
- `--spk_id`: speaker id for multi-speaker models.
- `--output`: output audio path, usually `.wav`.
- `--use_onnx`: use ONNXRuntime for supported AM/VOC combinations.
- `--cpu_threads`: ONNX CPU thread count.
- `--am_config`, `--am_ckpt`, `--am_stat`, `--phones_dict`, `--tones_dict`, `--speaker_dict`, `--voc_config`, `--voc_ckpt`, `--voc_stat`: custom model resource files when not using pretrained defaults.

## Python Executor

```python
import paddle
from paddlespeech.cli.tts import TTSExecutor

tts = TTSExecutor()
tts(text="你好", output="output.wav", am="fastspeech2_csmsc", voc="hifigan_csmsc", lang="zh", device=paddle.get_device())
```

Use custom resource paths only when all required files for the AM/vocoder are present. Missing stats or dictionaries are common causes of runtime failures.

## ONNX Notes

The TTS executor has an `ONNX_SUPPORT_SET` for selected FastSpeech2/SpeedySpeech and vocoder combinations. ONNX use needs matching ONNX model files or supported pretrained ONNX resources and `onnxruntime` installed. Use `--fs` for sample rate when custom ONNX model files need it.

## Batch Jobs

The shared job parser expects `id text` with no extra whitespace in the text value. This works for many Chinese strings but not English sentences with spaces.

```bash
python scripts/build_tts_job.py --output zh.job --item utt1:欢迎光临 --item utt2:谢谢惠顾
paddlespeech tts --input zh.job -d
```

For English or mixed text with spaces, prefer direct quoted commands or one item per direct run.
