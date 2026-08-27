# FunASR CLI reference

This reference lists the packaged commands that future agents are most likely to use. For richer workflow notes, read the matching sub-skill.

## Main commands

| Command | Purpose | Route |
|---|---|---|
| `funasr` | Agent-friendly local transcription CLI | `sub-skills/python-asr-pipelines` |
| `funasr-hydra` | Legacy Hydra-based inference CLI | `sub-skills/python-asr-pipelines` or `training-data-and-export` depending on the task |
| `funasr-server` | OpenAI-compatible HTTP API server | `sub-skills/serving-and-runtime` |
| `funasr-realtime-server` | Realtime WebSocket speech server | `sub-skills/serving-and-runtime` |
| `funasr-train` | Training launcher | `sub-skills/training-data-and-export` |
| `funasr-train-ds` | Distributed training launcher | `sub-skills/training-data-and-export` |
| `funasr-export` | Export / packaging launcher | `sub-skills/training-data-and-export` |
| `scp2jsonl` | Convert aligned SCP/text inputs to JSONL | `sub-skills/training-data-and-export` |
| `jsonl2scp` | Reverse JSONL conversion | `sub-skills/training-data-and-export` |
| `sensevoice2jsonl` | SenseVoice-style manifest conversion | `sub-skills/training-data-and-export` |

## `funasr` quick flags

| Flag | Meaning | Notes |
|---|---|---|
| `--model`, `-m` | Model alias | Defaults to `sensevoice`; `paraformer`, `paraformer-en`, and `fun-asr-nano` are also common. |
| `--hub`, `-H` | Model hub | `ms` or `hf`. |
| `--device` | Runtime device | `cpu`, `cuda:0`, or another supported torch device string. |
| `--output-format`, `-f` | Output format | `text`, `json`, `srt`, or `tsv`. |
| `--output-dir`, `-o` | Output directory | Writes one file per input. |
| `--language`, `-l` | Language hint | Common values include `zh`, `en`, `ja`, `ko`, `yue`, and `auto`. |
| `--timestamps` | Request timestamps | Useful with subtitle or alignment work. |
| `--spk` | Enable speaker diarization | Usually paired with VAD and a speaker model. |
| `--hotwords` | Decoder hotwords | Comma-separated list; model-level biasing, not post-processing. |
| `--verbose`, `-v` | Verbose logging | Shows load and runtime timings on stderr. |

## Output expectations

- Plain text mode prints one transcript per input file.
- JSON mode emits a machine-readable object with text and file metadata.
- SRT/TSV modes request sentence timestamps so the helper can write subtitle cues.
- `funasr` falls back to CPU when no CUDA device is visible.

## Helpful usage patterns

```bash
funasr audio.wav
funasr audio.wav --model paraformer --language zh
funasr audio.wav --output-format json
funasr audio.wav --output-format srt --output-dir ./subs
funasr audio.wav --spk --timestamps -f json
funasr *.wav --output-format tsv --output-dir ./output
```

## When to stop and route elsewhere

- If the task is batch transcription, subtitles, audio bytes, or hotwords, continue in `python-asr-pipelines`.
- If the task is OpenAI HTTP, realtime WebSocket, MCP, or runtime deployment, route to `serving-and-runtime`.
- If the task is Nano/GLM/Qwen3 vLLM choice, route to `llm-asr-and-vllm`.
- If the task is training manifests, distributed config, or export, route to `training-data-and-export`.
