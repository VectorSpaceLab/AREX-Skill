# Install and Dependencies

`mlx-audio` is a speech package with a small core and several workflow extras. Install only the extras that match the workflow you need.

## Core Package

The base package depends on:

- `huggingface_hub`
- `miniaudio`
- `mlx`
- `numpy`
- `scipy`
- `sounddevice`
- `tqdm`
- `transformers`

Typical package install:

```bash
pip install mlx-audio
```

For repository development or local skill verification, prefer a targeted editable install with only the needed extras.

## Optional Extras

| Extra | Adds | Typical use |
|---|---|---|
| `stt` | `sentencepiece` | speech-to-text models and tokenization-heavy STT flows |
| `tts` | `mistral-common[audio]`, `sentencepiece` | TTS families that need audio tokenization or Mistral speech support |
| `server` | `fastapi`, `uvicorn[standard]`, `python-multipart`, `webrtcvad`, `setuptools<81` | OpenAI-compatible server, uploads, and realtime VAD |
| `sts` | `sentencepiece`, `mlx-lm`, `webrtcvad`, `setuptools<81` | speech enhancement / speech-to-speech workflows with the default responder path |
| `llm` | `mlx-lm` | optional in-process LLM responder for the speech-to-speech pipeline |
| `dev` | `pytest`, `pytest-asyncio`, `black`, `isort`, `pre-commit` | local test and lint workflow |
| `docs` | `mkdocs-material`, `mkdocstrings[python]` | documentation build workflow |

Examples:

```bash
pip install -e '.[server,dev]'
pip install -e '.[tts,dev]'
pip install -e '.[stt,dev]'
```

## Safe Verification

- Run `scripts/check_install.py` first.
- Add `--check-cli` when you want to verify the console entry points with `--help` only.
- Use `scripts/check_optional_deps.py` to see which extras are available before choosing a workflow.

## Backend Notes

- `sounddevice` playback requires a working PortAudio installation on the host.
- `webrtcvad` is pinned behind `setuptools<81` in the server and STS extras because newer setuptools versions remove `pkg_resources`, which this dependency still expects.
- The package is primarily optimized for Apple Silicon/MLX workflows; on other hosts, importability depends on a compatible `mlx` build and the installed wheel set.
- Do not treat a successful import as proof that every model family or hardware-dependent example is available.
