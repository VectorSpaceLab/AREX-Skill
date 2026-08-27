# FunASR data formats

Use this page for a quick reminder of the common inputs and outputs. Detailed workflow-specific validation lives in the relevant sub-skill.

## Audio inputs to `AutoModel`

| Form | Example | Notes |
|---|---|---|
| Local file | `audio.wav` | The most common route. |
| URL | `https://.../sample.wav` | Downloaded first, then decoded. |
| Raw bytes | `audio_bytes` | `load_bytes()` distinguishes raw PCM from container audio. |
| `BytesIO` | `io.BytesIO(...)` | Useful for in-memory uploads. |
| `numpy.ndarray` | `np.ndarray` | Interpreted as audio samples. |
| `torch.Tensor` | `torch.Tensor` | Useful for batched or feature inputs. |
| List or tuple | `['a.wav', 'b.wav']` | Batch inference. |
| `wav.scp` / aligned list file | file path | One item per line, read by the helper. |
| Kaldi archive | `ark` path | Supported by the loader utilities. |

## Common ASR outputs

| Format | Shape | Notes |
|---|---|---|
| Text | plain string | Good for shell pipes. |
| JSON | structured dict | Used by the CLI and smoke helpers. |
| SRT | subtitle cues | Requires sentence timestamps or fallback bounds. |
| TSV | start/end/text rows | Useful for downstream tools. |
| OpenAI `verbose_json` | structured API response | Used by the HTTP server. |

## Training JSONL

A common training line looks like this:

```json
{"key":"utt001","source":"audio/utt001.wav","source_len":320,"target":"hello world","target_len":2}
```

Typical fields:

| Field | Meaning |
|---|---|
| `key` | Unique utterance id. |
| `source` | Audio path or URI. |
| `source_len` | Length used for filtering and sorting. |
| `target` | Transcript or other target text. |
| `target_len` | Target length used by some recipes. |
| `prompt` | Optional task prompt. |

## `wav.scp` plus text alignment

A simple pair of files looks like this:

```text
utt001 audio/utt001.wav
utt002 audio/utt002.wav
```

```text
utt001 hello world
utt002 你好世界
```

Rules:

- The first token is the utterance id.
- The rest of the line is the value.
- Ids should match across files when the recipe expects aligned data.
- Local source paths should exist before training if you want the bundled validator to check them.

## When to switch to a sub-skill

- Manifest creation or validation → `training-data-and-export`
- Subtitle cue generation or raw audio decoding → `python-asr-pipelines`
- Service response shapes → `serving-and-runtime`
