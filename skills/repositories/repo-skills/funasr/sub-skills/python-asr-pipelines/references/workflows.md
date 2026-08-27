# Workflows

Use these recipes when the user wants a transcript, subtitles, a first model choice, or a quick local CLI path.

## Choose a first model

| Need | Start with | Why |
|---|---|---|
| CPU-friendly general ASR | `SenseVoiceSmall` | Strong default and good for a quick local smoke. |
| Mandarin production ASR | `paraformer-zh` | Useful for hotwords, timestamps, and punctuation-aware output. |
| English-only ASR | `paraformer-en` | Compact English route. |
| Speaker-aware meeting transcript | `SenseVoiceSmall` or `paraformer-zh` with VAD + CAM++ | Lets the pipeline produce `sentence_info` and speaker labels. |

## One-off Python transcription

```python
from funasr import AutoModel

model = AutoModel(model="iic/SenseVoiceSmall", vad_model="fsmn-vad", device="cpu")
result = model.generate(input="meeting.wav")
print(result[0]["text"])
```

Useful additions:

- add `spk_model="cam++"` for speaker-aware meetings
- add `punc_model="ct-punc"` for punctuation-aware sentence segmentation
- add `hotword` or `hotwords` when a few names or terms need boosting

## Batch transcription

Use the bundled helper for folder scans, explicit output files, and per-file error capture:

```bash
python scripts/batch_transcribe.py --input ./audio --output ./transcripts.txt --model sensevoice
python scripts/batch_transcribe.py --input ./audio --output ./transcripts.jsonl --output-format jsonl --recursive
```

Good batch defaults:

- keep `--output` explicit
- use `--hub hf` when the model card lives on Hugging Face
- use `--vad-model none` only for short clips that do not need segmentation
- use `--postprocess-hotwords` only with explicit mappings when fuzzy deps are unavailable

## Subtitle generation

Use the bundled subtitle helper for SRT or VTT output:

```bash
python scripts/generate_subtitles.py meeting.wav --output meeting.srt --device cpu
python scripts/generate_subtitles.py meeting.wav --format vtt --spk --output meeting.vtt
```

The helper always requests sentence timestamps and speaker-ready fields, then falls back safely when `sentence_info` is missing:

1. use `sentence_info` when present
2. otherwise use known timestamp bounds from the model result
3. otherwise use the file duration when it can be read

## Hotword correction

Model-level boosting is best for a small number of keywords:

```python
result = model.generate(input="a.wav", hotword="FunASR 达摩院")
```

Text-level correction is best for fixed-name cleanup or large vocabularies:

```python
result = model.generate(
    input="a.wav",
    postprocess_hotwords={"科大迅飞": "科大讯飞"},
    return_postprocess_hotword_matches=True,
)
```

If you only have explicit replacements, keep fuzzy matching off unless `pypinyin` and `rapidfuzz` are installed.

## Speaker and punctuation aware transcript

```python
from funasr import AutoModel

model = AutoModel(
    model="paraformer-zh",
    vad_model="fsmn-vad",
    punc_model="ct-punc",
    spk_model="cam++",
    device="cpu",
)
result = model.generate(input="meeting.wav", batch_size_s=300)
```

What to expect:

- `text` is the final transcript
- `sentence_info` contains sentence boundaries and optional `spk`
- `timestamp` / `timestamps` preserve the timing backbone used by subtitle tools

## Standalone speaker verification

```python
from funasr import AutoModel

model = AutoModel(
    model="iic/speech_eres2netv2_sv_zh-cn_16k-common",
    device="cpu",
)
result = model.generate(input="speaker.wav")
embedding = result[0]["spk_embedding"]
```

Use this route when the user wants a speaker embedding or a speaker-similarity workflow rather than full ASR diarization.

## Long audio and memory

For long input, start with VAD and adjust these knobs if memory grows too fast:

- reduce `batch_size_s`
- reduce `batch_size_threshold_s`
- shorten `vad_model`'s `max_single_segment_time`

## Route elsewhere when the task changes

- punctuation cleanup or full ITN/TN → `text-normalization`
- OpenAI server, realtime WS, MCP, or deployment → `serving-and-runtime`
- Fun-ASR-Nano / GLM-ASR / Qwen3-ASR / vLLM → `llm-asr-and-vllm`
- training, manifests, export, or local inference after export → `training-data-and-export`
