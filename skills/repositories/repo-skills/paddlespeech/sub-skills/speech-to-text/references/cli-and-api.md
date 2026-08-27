# Speech-to-Text CLI and API

## ASR CLI

Common commands:

```bash
paddlespeech asr --input zh_16k.wav
paddlespeech asr --model conformer_aishell --lang zh --input zh_16k.wav
paddlespeech asr --model transformer_librispeech --lang en --input en_16k.wav
paddlespeech asr --model conformer_talcs --lang zh_en --codeswitch True --input zh_en_16k.wav
paddlespeech asr --model conformer_online_wenetspeech --num_decoding_left_chunks 3 --input zh_16k.wav
```

Key ASR options:

- `--model`: choices include `conformer_wenetspeech`, `conformer_online_wenetspeech`, `conformer_u2pp_online_wenetspeech`, `conformer_online_multicn`, `conformer_aishell`, `conformer_online_aishell`, `transformer_librispeech`, `deepspeech2online_wenetspeech`, `deepspeech2offline_aishell`, `deepspeech2online_aishell`, `deepspeech2offline_librispeech`, `conformer_talcs`, and `conformer_online_talcs`.
- `--lang`: common values are `zh`, `en`, and `zh_en`.
- `--sample_rate`: `16000` for most current models; `8000` only when a matching model supports it.
- `--decode_method`: `ctc_greedy_search`, `ctc_prefix_beam_search`, `attention`, or `attention_rescoring` for supported transformer/conformer models.
- `--num_decoding_left_chunks`: online transformer/conformer chunk context; `-1` means full left context.
- `--yes`: accepts automatic sample-rate/format conversion prompts.
- `--rtf`: prints real-time factor for supported executors.

Python executor:

```python
import paddle
from paddlespeech.cli.asr import ASRExecutor

asr = ASRExecutor()
text = asr(audio_file="zh_16k.wav", model="conformer_wenetspeech", lang="zh", sample_rate=16000, device=paddle.get_device())
```

## Speech Translation CLI

```bash
paddlespeech st --input en_16k.wav
paddlespeech st --model fat_st_ted --src_lang en --tgt_lang zh --input en_16k.wav
```

ST uses a `fat_st_ted` model family and downloads Kaldi binaries for feature extraction when default pretrained resources are used. Treat that download/toolchain path as a side effect.

## SSL CLI

```bash
paddlespeech ssl --task asr --model wav2vec2 --lang en --input en_16k.wav
paddlespeech ssl --task vector --model hubert --lang en --input en_16k.wav
paddlespeech ssl --task asr --model wavlm --lang en --input en_16k.wav
```

Supported SSL `--model` values are `wav2vec2`, `hubert`, and `wavlm`. `--task` is `asr` or `vector`. Chinese SSL ASR support is model-specific; the code has English paths for Wav2Vec2/Hubert/WavLM and a Chinese Wav2Vec2 ASR branch.

## Whisper CLI

```bash
paddlespeech whisper --task transcribe --input audio_16k.wav
paddlespeech whisper --task translate --size medium --input audio_16k.wav
paddlespeech whisper --lang en --size base --task transcribe --input en_16k.wav
```

Whisper options:

- `--task`: `transcribe` or `translate`.
- `--size`: `turbo`, `large`, `medium`, `base`, `small`, or `tiny`.
- `--lang en`: chooses English-only model variants when available.
- `--language`: forces decode language; default behavior lets the model infer language.
- `--sample_rate`: only `16000`.

Python executor:

```python
import paddle
from paddlespeech.cli.whisper import WhisperExecutor

whisper = WhisperExecutor()
result = whisper(model="whisper", task="transcribe", size="tiny", sample_rate=16000, audio_file="audio_16k.wav", device=paddle.get_device())
```

## Punctuation Pipeline

A common command-line pipeline is:

```bash
paddlespeech asr --input zh_16k.wav | paddlespeech text --task punc
```

For planned production code, keep ASR and punctuation as separate steps so failures are easier to debug. Use `../text-processing/SKILL.md` for punctuation model options and text cleaning behavior.
