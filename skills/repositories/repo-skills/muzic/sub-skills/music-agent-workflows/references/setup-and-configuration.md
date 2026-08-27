# MusicAgent setup and configuration

## Scope

This reference covers the MusicAgent wrapper only: installation modes, system prerequisites, dependency conflict notes, the local model/download layout, `config.yaml`, and credential handling.

## Installation modes

| Mode | Status | When to use | Notes |
|---|---|---|---|
| Docker | Placeholder | Only if you build your own container | The README mentions Docker, but no maintained image is shipped with the repo. Treat this path as manual container work. |
| Conda / pip | Recommended | Most users | Install into a dedicated environment for MusicAgent rather than sharing a broad Muzic environment. |

### Recommended host prerequisites

Install the Linux packages before or alongside the Python environment:

| Package | Why it is needed |
|---|---|
| `git-lfs` | Pulls large model checkpoints and hosted weights. |
| `libsndfile1-dev` | Audio file I/O used by `soundfile`. |
| `fluidsynth` | MIDI-to-audio synthesis for ROC-style outputs. |
| `ffmpeg` | Audio decoding and conversion for uploads, downloads, and local media handling. |
| `lilypond` | Renders symbolic previews from MIDI in the Gradio flow. |

## Python dependency notes

The MusicAgent stack is intentionally old and conflict-prone. Keep it in an isolated environment.

| Dependency | Role | Conflict note |
|---|---|---|
| `semantic-kernel` | LLM connector used by the CLI and prompt bundle | The repo relies on an older connector API surface. Choose a version that still exposes the OpenAI/Azure text-completion classes used by the wrapper. |
| `gradio==3.26.0` | Gradio UI | Newer Gradio releases may change the UI APIs used by the demo. |
| `librosa==0.8.0` | Audio loading and resampling | Works best with the repo's pinned `numpy==1.23.0`. |
| `numpy==1.23.0` | Compatibility pin | Avoids common breakage in older audio and TensorFlow packages. |
| `protobuf==3.20.3` | Compatibility pin | Prevents protobuf API mismatches in older ML stacks. |
| `tensorflow==2.11.0`, `fairseq==0.12.0`, `diffusers==0.21.2`, `torch`-family packages | Tool backends | These are heavyweight and may conflict with other Muzic subprojects. Do not install the whole monorepo's requirements into one shared environment unless you are ready to resolve conflicts. |

## Working-directory contract

Run MusicAgent from the project directory that contains the config file and scratch directories.

- Relative paths in `config.yaml` are interpreted from the launch directory.
- `src_fold` defaults to `public/audios` and is created at runtime for uploaded or generated media.
- `log_file` defaults to `logs/debug.log`.
- `local_fold` defaults to `models` and is where downloaded model caches live.
- The speech/audio demo also expects `MS Basic.sf3` in the MusicAgent working directory when MIDI synthesis is used.

## Model and download layout

The `local_fold` directory groups the model caches and helper trees used by the wrapper.

| Path under `local_fold` | Used by | Notes |
|---|---|---|
| `cvssp/audioldm-m-full/` | Text-to-audio | AudioLDM cache; GPU-leaning in practice. |
| `lewtun/distilhubert-finetuned-music-genres/` | Music classification | Hugging Face audio-classification cache. |
| `dima806/music_genres_classification/` | Music classification | Hugging Face audio-classification cache. |
| `sander-wood/text-to-music/` | Text-to-sheet-music | Candidate task name exists, but the current plugin loader does not instantiate a pipe for it. Treat as unsupported until extended. |
| `jonatasgrosman/whisper-large-zh-cv11/` | Lyric recognition | Large ASR cache; the wrapper initializes this path with a CUDA-oriented pipeline and then moves the model. |
| `DiffSinger/` | Lyric-to-audio | Needs the DiffSinger checkpoint/config bundle plus its own upstream code layout. |
| `ddsp/violin/` and `ddsp/flute/` | Timbre transfer | Needs the DDSP checkpoint trees, gin config, and stats files. |
| `muzic/roc/` | Lyric-to-melody | Needs the ROC adapter files, checkpoint directory, database, and enough ROC utility code to satisfy its imports. |

### Convenience download helper

The bundled download helper is only a convenience bootstrap.

- It fetches hosted model repos into `local_fold`.
- It clones the Git-based tool repositories used by MusicAgent.
- It copies auxiliary ROC helper files into the model tree.
- It does **not** validate credentials, install system packages, or guarantee that every transitive ROC utility import is present.

If you already manage model caches another way, keep the same directory layout instead of relying on the helper.

## `config.yaml` fields

| Field | Type | Purpose | Notes |
|---|---|---|---|
| `debug` | bool | Controls console log verbosity | File logging still works when `debug` is false. |
| `use_azure_openai` | bool | Selects the CLI's backend connector | CLI only; Gradio does not use the Azure path. |
| `model` | string | OpenAI model name for the wrapper | Used by the LLM connector. |
| `device` | string | Target device for loaded tool backends | Does not override every hardcoded loader assumption. |
| `local_fold` | string | Root for model/download caches | Default: `models`. |
| `log_file` | string | File log destination | Default: `logs/debug.log`. |
| `src_fold` | string | Scratch/output directory | Used for uploads, downloads, generated audio, and symbolic files. |
| `disabled_tools` | string or null | Comma-separated pipe ids to skip | Match the loader keys, not the planner task names. |
| `history_len` | int | Chat history window | Applied after each chat turn. |
| `candidate_tools` | int | Shortlist size for tool selection | Only matters when more than one loaded pipe can satisfy a task. |
| `huggingface.token` | string | Optional token placeholder | Documented in the README, but not read directly by the current wrapper code. |
| `spotify.client_id` / `spotify.client_secret` | strings | Spotify API credentials | Required only when the Spotify tools are enabled. |
| `google.api_key` / `google.custom_search_engine_id` | strings | Google Custom Search credentials | Required only when the Google search tool is enabled. |

## Secret handling

- CLI: populate `.env` with the OpenAI or Azure values expected by the Semantic Kernel helper.
- Gradio: paste only an OpenAI API key in the browser UI; the demo does not use the Azure path.
- Keep Spotify, Google, and Hugging Face secrets out of the generated skill tree.
- Never commit `.env` or other secret-bearing files.

## Launch commands

From the MusicAgent working directory:

```bash
python agent.py --config config.yaml
python gradio_agent.py --config config.yaml
```

The CLI reads secrets from `.env`; the Gradio demo asks for the OpenAI key interactively.
