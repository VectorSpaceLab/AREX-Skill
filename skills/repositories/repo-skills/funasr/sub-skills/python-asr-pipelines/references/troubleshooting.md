# Troubleshooting

This page focuses on the common failures for the default Python ASR route.

## Missing PyTorch before `AutoModel`

**Symptom**: `from funasr import AutoModel` raises a `ModuleNotFoundError` for `torch`.

**Fix**: install a matching PyTorch + torchaudio build first, then install FunASR.

**Why**: `import funasr` can succeed without torch, but `AutoModel` needs it.

## Wrong hub or model alias

**Symptom**: the CLI or Python API downloads the wrong checkpoint or fails on a model name.

**Fix**:

- use `--hub ms` for ModelScope or `--hub hf` for Hugging Face
- start with `sensevoice`, `paraformer`, or `paraformer-en`
- only use `fun-asr-nano` when you intentionally want the LLM-based family

## Raw PCM vs container audio

**Symptom**: a byte stream looks like audio but decodes incorrectly, or a raw buffer is misread as MP3/WAV.

**Fix**:

- raw PCM must be signed 16-bit little-endian with no container header
- WAV / MP3 / FLAC / OGG / MP4 / M4A / WebM bytes should be passed as the full container
- if you already have a file, pass the file path and let the loader decode it

**Recovery clue**: `load_bytes()` first checks for known container headers and only falls back to raw PCM when the bytes have no audio container signature.

## Hotword correction does not take effect

**Symptom**: the transcript still contains a misspelled name or keyword.

**Fix**:

- use model-level `hotword` / `hotwords` for decoding bias on a small keyword set
- use `postprocess_hotwords` for fixed-name cleanup after decoding
- explicit mappings like `wrong=>right` work without fuzzy dependencies
- fuzzy matching needs both `pypinyin` and `rapidfuzz`

**Helpful rule**: if you only need exact replacements, keep fuzzy matching off.

## Subtitle fallback when `sentence_info` is missing

**Symptom**: the subtitle helper writes one cue, a blank cue, or no cues at all.

**Fix**:

- make sure the model returns `sentence_info` when you need sentence-level subtitles
- request `sentence_timestamp`, `output_timestamp`, and `return_time_stamps` for subtitle flows
- if sentence information is still unavailable, let the helper fall back to timestamp bounds or audio duration

**Extra note**: if `punc_model` is absent, sentence segmentation may be empty even though the transcript text is correct.

## Speaker / timestamp / punctuation routing mistakes

**Symptom**: speaker labels disappear, timestamps look wrong, or sentence splitting fails.

**Fix**:

- `spk_model` requires `vad_model`
- punctuation-aware speaker routing needs timestamps and punctuation alignment
- if `punc_model` is missing, `punc_segment` may fall back to `vad_segment`
- for transcript-only use, do not request speaker diarization

## Metrics helper and rapidfuzz

**Symptom**: CER/WER helper imports fail or evaluation code crashes on empty references.

**Fix**:

- install `rapidfuzz` for `funasr.metrics.common.ErrorCalculator`
- expect `None` when the reference length is zero
- use this helper only for quick local checks, not as a full evaluation stack

## Quick CLI sanity checks

- `funasr --help`
- `funasr audio.wav -f json`
- `funasr audio.wav -f srt -o ./subs`

If those work but your transcript is empty, check the input file, sample rate, hub, and model choice next.
