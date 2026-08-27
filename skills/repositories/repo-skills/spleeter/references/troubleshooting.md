# Root troubleshooting

Use this page for cross-cutting Spleeter install, import, CLI, ffmpeg, TensorFlow, optional dependency, and model-cache problems. For workflow-specific failures, use:

- [separation troubleshooting](../sub-skills/separation/references/troubleshooting.md)
- [training troubleshooting](../sub-skills/training/references/troubleshooting.md)
- [evaluation troubleshooting](../sub-skills/evaluation/references/troubleshooting.md)

## Triage checklist

```bash
python -m spleeter --version
python -m spleeter --help
python -m spleeter separate --help
ffmpeg -version
ffprobe -version
python scripts/check_install.py
```

If evaluation is involved:

```bash
python -c "import musdb, museval"
python -m spleeter evaluate --help
```

If Python APIs are involved:

```bash
python - <<'PY'
from spleeter.separator import Separator
from spleeter.audio.adapter import AudioAdapter
from spleeter.utils.configuration import load_configuration
print(load_configuration('spleeter:2stems')['instrument_list'])
print(type(AudioAdapter.default()).__name__)
print(Separator)
PY
```

## Common root-level failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'spleeter'` | Spleeter is not installed in the Python environment that is running the command. | Install Spleeter into that environment and rerun `python -m spleeter --version`. Avoid mixing system Python, notebooks, and virtual environments. |
| TensorFlow import fails on Python 3.12+ | Spleeter 2.4.2 requires Python `<3.12` and pins TensorFlow 2.12.1. | Use Python 3.8-3.11 with compatible TensorFlow wheels. |
| `spleeter` command is not found | Console entry point is absent from `PATH` or the wrong environment is active. | Use `python -m spleeter ...` from the intended Python environment, or fix the environment's script path. |
| `ffmpeg binary not found` or `ffprobe binary not found` | Default audio adapter cannot locate system binaries. | Install ffmpeg/ffprobe and ensure both are on `PATH` in the same shell/service. |
| `Extra dependencies musdb and museval not found` and exit code `10` | Evaluation extra is missing. | Install `spleeter[evaluation]` or compatible `musdb` and `museval` into the same environment. |
| TensorFlow logs missing CUDA/cuDNN/TensorRT or lists no GPU | Active TensorFlow runtime cannot use GPU acceleration. | Continue on CPU unless GPU was required. If GPU is required, install/verify a TensorFlow GPU-compatible environment before claiming backend support. |
| First pretrained run downloads slowly or fails before outputs | Spleeter is fetching model archives, validating checksums, or writing cache files. | Allow network/cache writes, prewarm the model cache, or provide a local config/checkpoint. See [models and configuration](models-and-configuration.md). |
| `Downloaded file is corrupted, please retry` | Checksum mismatch after model download. | Delete the incomplete model directory/cache entry, stabilize network/proxy, and retry. |
| `No embedded configuration ... found` | Bad `spleeter:` descriptor name. | Use a valid descriptor such as `spleeter:2stems`, `spleeter:4stems`, `spleeter:5stems`, or a filesystem JSON path. |
| `Configuration file ... not found` | Filesystem config path is wrong or relative to an unexpected working directory. | Use an absolute config path or launch from the directory where the relative path resolves. |
| Apple Silicon runtime issues | TensorFlow compatibility can block Spleeter on that platform. | Use a supported Python/TensorFlow build or a known-good CPU/x86_64/remote runtime. |
| Non-WAV output fails | The installed ffmpeg build lacks the requested encoder or rejects the container/bitrate combination. | Retry with `--codec wav`, then solve ffmpeg encoder support separately. |

## Separate package problems from workflow problems

- If `python -m spleeter --help` fails, solve install/import/CLI first.
- If help works but `AudioAdapter.default()` fails, solve ffmpeg/ffprobe first.
- If a short `--duration 10 --codec wav` separation fails before loading audio, inspect model descriptor/cache/network.
- If short separation works but training fails, validate training CSV/config and cache settings.
- If separation works but evaluation fails, inspect `spleeter[evaluation]`, `--mus_dir`, ground-truth source files, and metric output.

## Privacy and reproducibility notes

When writing commands or reports for users, keep local virtualenv names, machine-specific cache paths, proxies, and private download hosts out of reusable instructions unless the user provided them for a one-off task. Prefer generic placeholders such as `MODEL_PATH`, `DATA_ROOT`, `CONFIG.json`, and `OUTPUT`.
