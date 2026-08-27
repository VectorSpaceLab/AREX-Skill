# Installation and runtime

Use this reference before running any Spleeter workflow. It summarizes package constraints, system dependencies, optional extras, smoke checks, and backend expectations for Spleeter 2.4.2.

## Supported Python/package baseline

Spleeter 2.4.2 package metadata declares:

| Item | Evidence-backed value |
| --- | --- |
| Distribution/import | `spleeter` / `import spleeter` |
| Python | `>=3.8,<3.12` |
| TensorFlow | `tensorflow==2.12.1` |
| TensorFlow IO GCS filesystem | `tensorflow-io-gcs-filesystem==0.32.0` |
| CLI framework | `typer>=0.3.2,<0.4.0` |
| Core audio/data deps | `ffmpeg-python`, `httpx[http2]`, `norbert`, `numpy<2`, `pandas` |
| Optional evaluation extra | `musdb` and `museval` via `spleeter[evaluation]` |
| Console entry point | `spleeter = spleeter.__main__:entrypoint` |

Normal install shape:

```bash
pip install spleeter
```

Install evaluation dependencies when the task needs `spleeter evaluate`:

```bash
pip install 'spleeter[evaluation]'
```

Use a Python version that satisfies Spleeter and TensorFlow together. Avoid Python 3.12+ for Spleeter 2.4.2 unless a downstream fork has changed the package constraints and TensorFlow compatibility.

## System audio dependencies

The default adapter is `spleeter.audio.ffmpeg.FFMPEGProcessAudioAdapter`. It checks that both system binaries are available:

```bash
ffmpeg -version
ffprobe -version
```

If either command is missing, `AudioAdapter.default()` and the default CLI workflows fail before audio is processed. Install ffmpeg/ffprobe using the user's platform package manager or container image, then rerun the checks in the same shell or service environment that will run Spleeter.

The README also notes `libsndfile` as a platform dependency in some install paths. If `musdb`, `museval`, or audio file libraries fail to load or write WAV files, verify the environment's audio-system libraries in addition to ffmpeg.

## Preferred smoke check sequence

Run this sequence before a real separation, training, or evaluation job:

```bash
python -m spleeter --version
python -m spleeter --help
python -m spleeter separate --help
ffmpeg -version
ffprobe -version
python -c "import spleeter; from spleeter.audio.adapter import AudioAdapter; print(type(AudioAdapter.default()).__name__)"
```

Use the bundled root checker for a compact report:

```bash
python scripts/check_install.py
```

When evaluation is needed, add:

```bash
python -c "import musdb, museval; print('evaluation extras OK')"
python -m spleeter evaluate --help
```

For Python API work, verify key imports:

```bash
python - <<'PY'
from spleeter.separator import Separator
from spleeter.audio.adapter import AudioAdapter
from spleeter.utils.configuration import load_configuration
print(load_configuration('spleeter:2stems')['instrument_list'])
print(Separator)
print(AudioAdapter.default())
PY
```

## CPU and GPU expectations

The verified baseline for this skill is TensorFlow CPU execution. Spleeter can benefit from GPU acceleration when the active TensorFlow installation, CUDA/cuDNN libraries, drivers, and hardware are compatible, but GPU is an optional performance backend for the selected workflows.

Do not promise GPU acceleration merely because a machine has an NVIDIA GPU. Verify it in the same environment that runs Spleeter:

```bash
python - <<'PY'
import tensorflow as tf
print(tf.__version__)
print(tf.config.list_physical_devices())
print('GPUs:', tf.config.list_physical_devices('GPU'))
PY
```

If TensorFlow logs missing CUDA, cuDNN, TensorRT, or GPU libraries but still lists a CPU device and the user did not require GPU, continue with CPU guidance. If the user explicitly requires GPU training or separation speed, treat missing TensorFlow GPU devices as an environment issue to solve before claiming that backend.

## Windows and Apple Silicon notes

- On Windows, if the `spleeter` shortcut is unavailable or behaves incorrectly, use `python -m spleeter ...` for the same CLI commands.
- Paths with spaces should be shell-quoted.
- Apple Silicon runtimes may hit TensorFlow compatibility limits. Use a Python/TensorFlow/Spleeter combination known to import successfully, or use a CPU/x86_64/remote runtime. Treat local GPU/MPS acceleration as unverified unless independently proven.

## First-run model cache and network

Pretrained descriptors such as `spleeter:2stems`, `spleeter:4stems`, and `spleeter:5stems` can trigger model download and checksum validation on first use. If network access, release-host access, or cache writes are disallowed, prewarm the cache or use a local trained config/model directory before running a long workflow. Read [models and configuration](models-and-configuration.md) for descriptor and cache behavior.
