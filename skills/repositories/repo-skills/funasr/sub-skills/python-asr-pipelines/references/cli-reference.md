# CLI reference

`funasr` is the installed, agent-friendly speech-recognition entry point.
It covers single files, batches, JSON output, subtitles, timestamps, hotwords, and speaker labels.

## Basic forms

```bash
funasr audio.wav
funasr audio.wav --model paraformer
funasr audio.wav --output-format json
funasr audio.wav --output-format srt --output-dir ./subs
```

## Flags

| Flag | Default | Meaning |
|---|---|---|
| `audio` | required | One or more audio files. Long-form shell globs are allowed. |
| `--model`, `-m` | `sensevoice` | Model alias. Common aliases are `sensevoice`, `paraformer`, `paraformer-en`, and `fun-asr-nano`. |
| `--hub`, `-H` | `ms` | `ms` for ModelScope, `hf` for Hugging Face. |
| `--language`, `-l` | `auto` | Language hint such as `zh`, `en`, `ja`, `ko`, `yue`, or `auto`. |
| `--device` | auto | Uses CUDA when available, otherwise CPU. |
| `--output-format`, `-f` | `text` | `text`, `json`, `srt`, or `tsv`. |
| `--output-dir`, `-o` | stdout | Write one output file per input. |
| `--timestamps` | off | Keep word-level timestamps in text/json output. |
| `--spk` | off | Enable speaker diarization. |
| `--hotwords` | none | Comma-separated hotwords. |
| `--verbose`, `-v` | off | Show model loading and per-file timing on stderr. |

## Output formats

### `text`
Plain transcript text, one result per input.

### `json`
Structured output for automation. Common fields are `text`, `segments`, `timestamps`, `file`, `model`, `language`, `audio_duration_s`, and `processing_s`.

### `srt`
SubRip subtitles. The CLI requests sentence timestamps automatically and writes one cue per sentence when they are available.
If sentence-level timestamps are missing, it falls back to one valid cue spanning the known timestamp bounds or audio duration.

### `tsv`
Tab-separated cue timing plus text.
Like `srt`, it requests sentence timestamps and falls back safely when they are missing.

## Model notes

| Alias | Typical path | Notes |
|---|---|---|
| `sensevoice` | `iic/SenseVoiceSmall` | Good CPU-friendly first choice. |
| `paraformer` | `paraformer-zh` | Mandarin-oriented route with punctuation support. |
| `paraformer-en` | `paraformer-en` | English-focused route. |
| `fun-asr-nano` | `FunAudioLLM/Fun-ASR-Nano-2512` | Available in the CLI, but the detailed LLM-ASR route belongs to the sibling sub-skill. |

## Practical examples

```bash
# JSON for automation
funasr meeting.wav -f json | jq '.text'

# Subtitle files
funasr meeting.wav -f srt -o ./subs

# Mandarin transcription with hotwords
funasr audio.wav --model paraformer --language zh --hotwords "FunASR,达摩院"

# Speaker-aware transcript
funasr meeting.wav --spk --timestamps -f json
```

## Compatibility note

The legacy Hydra CLI is still available as `funasr-hydra`, but the default user-facing route for this sub-skill is `funasr`.

## See also

- `references/api-reference.md`
- `references/workflows.md`
- `references/troubleshooting.md`
