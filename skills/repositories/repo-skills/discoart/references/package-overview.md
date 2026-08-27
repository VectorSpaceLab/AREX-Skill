# DiscoArt Package Overview

## Purpose

Read this for the shared package facts behind the DiscoArt sub-skills: public APIs, runtime prerequisites, output artifacts, environment variables, and which workflows are safe to check without starting generation.

## What DiscoArt does

DiscoArt wraps Disco Diffusion into a Python package with:

- a one-line `create(**kwargs)` API that returns a DocArray `DocumentArray`;
- configuration helpers for saving, loading, showing, and exporting generation settings;
- prompt scheduling and CLIP-model guidance controls;
- CLI commands under `python -m discoart`;
- optional Jina Flow serving for `/create`, `/result`, `/skip`, and `/stop` endpoints;
- local persistence of final/intermediate images, GIF progress, and `da.protobuf.lz4` backups.

## Public package surface

Common imports:

```python
from discoart import create, cheatsheet, load_config, save_config, show_config, go_big
from discoart.config import save_config_svg, export_python
```

Verified baseline facts for this generated skill:

| Item | Fact |
| --- | --- |
| Distribution/import name | `discoart` |
| Baseline version | `0.12.2` |
| Main API | `create(**kwargs) -> Optional[DocumentArray]` |
| GoBig API | `go_big(doc, window_size=256, upscale_factor=2, skip_rate=0.8, stride_size=None, **kwargs) -> Document` |
| Default argument count | 49 default keys in the packaged default config |
| CLI root | `python -m discoart [-h] [-v] {create,config,serve} ...` |
| Config command | `python -m discoart config [EXPORT_YAML_FILE]` |
| Create command | `python -m discoart create [YAML_CONFIG_FILE]` |
| Serve command | `python -m discoart serve [FLOW_YAML_FILE]` |

## Runtime prerequisites

Install from PyPI for normal use:

```bash
pip install discoart
```

Use an editable install only when working against a local checkout in a disposable development environment:

```bash
python -m pip install -e .
```

- Python 3.7+ is declared by package metadata.
- Use a conservative Python version supported by ML dependencies when preparing new environments; very new Python releases can break old PyTorch/Jina/DocArray-era packages.
- Actual image generation is CUDA-oriented. CPU import/config checks are valid, but CPU generation is impractically slow.
- First generation may download diffusion model weights, the secondary model, OpenAI CLIP weights, or OpenCLIP weights.
- `jina`, `docarray`, `torch`, `torchvision`, `open_clip_torch`, `openai-clip`, `lpips`, `guided-diffusion-sdk`, `resize-right-sdk`, `pyspellchecker`, `pyyaml`, `wandb`, `numpy`, and related dependencies are part of the runtime install path.
- Legacy import behavior uses `pkg_resources`; if an environment has a very new `setuptools` without `pkg_resources`, pinning `setuptools<81` can be necessary.

## Output artifacts

For a run named `name_docarray`, DiscoArt writes under:

```text
<DISCOART_OUTPUT_DIR or current directory>/<name_docarray>/
```

Common files are:

- `<batch>-done.png` — final image for a completed batch item.
- `<batch>-step-<step>.png` — intermediate images saved according to `save_rate`.
- `<batch>-progress.png` — sprite of intermediate progress.
- `<batch>-progress.gif` — animated progress when `gif_fps > 0`.
- `da.protobuf.lz4` — DocArray binary backup containing config tags and image data.

`create()` also returns a `DocumentArray`. Each `Document` carries generation config in `.tags` and image URI data in `.uri` when available.

## Environment variables

Set these before importing DiscoArt when possible:

| Variable | Use |
| --- | --- |
| `DISCOART_LOG_LEVEL` | Increase or reduce DiscoArt logging verbosity. |
| `DISCOART_OPTOUT_CLOUD_BACKUP` | Opt out of DocArray cloud backup/push behavior. |
| `DISCOART_DISABLE_IPYTHON` | Disable notebook/IPython integration for CLI or headless runs. |
| `DISCOART_DISABLE_RESULT_SUMMARY` | Suppress the final rich/notebook result summary. |
| `DISCOART_DEFAULT_PARAMETERS_YAML` | Override the packaged default generation parameters. |
| `DISCOART_CUT_SCHEDULES_YAML` | Override the packaged cut schedule groups. |
| `DISCOART_MODELS_YAML` | Override the packaged diffusion model catalog. |
| `DISCOART_OUTPUT_DIR` | Choose the parent directory for generated run folders. |
| `DISCOART_CACHE_DIR` | Choose where model downloads and cache files are stored. |
| `DISCOART_DISABLE_REMOTE_MODELS` | Disable remote model-list lookup on import/runtime. |
| `DISCOART_REMOTE_MODELS_URL` | Replace the remote model-list URL. |
| `DISCOART_DISABLE_CHECK_MODEL_SHA` | Skip model file SHA checking. Use only with trusted cache files. |
| `DISCOART_DISABLE_TQDM` | Disable diffusion progress bars. |
| `WANDB_MODE` | Set to `online` to log W&B dashboards; default behavior is disabled/offline-style. |

## Safe checks versus expensive actions

Safe by default:

- Import the package.
- Load/validate default or user configs.
- Validate prompt schedules and prompt planner activity.
- Run CLI `--help` and `config` export.
- Generate a service YAML template without launching Jina.
- Probe `torch.cuda.is_available()` and allocate a tiny CUDA tensor.

Potentially expensive or stateful:

- Calling `create()`.
- Running `python -m discoart create`.
- Launching `python -m discoart serve`.
- Docker builds/runs.
- Downloading model weights or CLIP checkpoints.
- Pulling/pushing `DocumentArray` results from cloud storage.

## Where to go next

- Python artwork generation: `../sub-skills/artwork-generation/SKILL.md`.
- Configs, prompts, schedules, and validation: `../sub-skills/configuration-and-prompts/SKILL.md`.
- CLI, serving, Docker, and endpoint workflows: `../sub-skills/cli-and-serving/SKILL.md`.
- Cross-cutting failures: `troubleshooting.md`.
