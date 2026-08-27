# Cross-cutting pyAudioAnalysis troubleshooting

## When to read

Read this for installation, imports, optional media tools, plotting, filesystem side effects, or legacy CLI behavior that can affect more than one pyAudioAnalysis workflow. Use the sub-skill troubleshooting pages for feature-, model-, segmentation-, or CLI-specific details.

## Install and import failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'pyAudioAnalysis'` | Package is not installed in the active Python environment. | Install `pyAudioAnalysis` and rerun `python scripts/check_pyaudioanalysis_env.py --pretty`. |
| Import fails for `hmmlearn`, `sklearn`, `imblearn`, `pydub`, `eyed3`, `plotly`, or `pandas` | Runtime requirements are incomplete or installed in a different environment. | Install the package's runtime requirements in the same environment that runs the task; verify with the root check script. |
| `ModuleNotFoundError: No module named 'ShortTermFeatures'` when using `python -m pyAudioAnalysis.audioAnalysis` | Legacy CLI modules use top-level sibling imports. | Do not use `python -m pyAudioAnalysis.audioAnalysis` as the default. Use `sub-skills/cli-and-io/scripts/inspect_cli.py`, execute the installed `audioAnalysis.py` script path, or prefer Python APIs. |
| `aifc` import failure on newer Python | Python 3.13 removed/deprecated standard-library AIFF support. | Prefer Python 3.10/3.11/3.12 for pyAudioAnalysis 0.3.14, or use WAV-only helper shims in bundled smoke scripts when you are not exercising AIFF. |
| `pip check` reports version conflicts | A dependency resolver installed incompatible scientific packages. | Recreate a clean environment and install `pyAudioAnalysis` plus runtime requirements together; avoid mixing old conda packages with new pip wheels. |

## Optional media conversion and decoding

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| MP3/OGG/AU read or conversion fails | `pydub` is installed but `ffmpeg`/`avconv` is missing or not on `PATH`. | Check `sub-skills/cli-and-io/scripts/audio_io_smoke.py`; install `ffmpeg` or provide WAV input. |
| Conversion command writes unexpected files | Legacy helpers replace extensions or write output beside input files. | Use an isolated work directory and copy inputs there before conversion; never run conversion helpers on irreplaceable originals. |
| Paths with spaces fail in a shell command | Shell quoting or legacy `os.system` string construction. | Prefer Python APIs where possible. When using CLI commands, quote every user path and test with a copied fixture first. |

## Plotting and headless execution

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Command hangs or opens a GUI window | CLI wrappers call `matplotlib.pyplot.show()` for spectrogram/chromagram/visualization/segmentation plots. | Prefer Python APIs with `plot=False` where available, or set a non-interactive Matplotlib backend such as `MPLBACKEND=Agg` before running a command that only needs to validate. |
| Plotly opens browser output | Evaluation/visualization helpers call Plotly offline output with `auto_open=True` in some paths. | Use `plot=False` evaluation APIs when possible or run in an isolated environment where browser side effects are acceptable. |

## Model artifact safety

- Classifier, regression, and HMM models are pickle artifacts. Only load artifacts from trusted training runs or trusted package data.
- Classifier training overwrites paths derived from `model_name`; always use an explicit output directory and unique prefix.
- Non-kNN classifiers require a companion `MEANS` sidecar. Move/copy/delete it with the model file.
- Regression training can create one artifact set per target CSV; avoid underscores in target CSV stems if the displayed target name matters.

## Data and timing issues

- High-level CLI/API windows are often seconds (`0.050` means 50 ms), while lower-level `ShortTermFeatures.feature_extraction(...)` expects window/step sample counts.
- Very short clips can produce zero or too few frames for mid-term, classifier, or diarization workflows. Increase duration or reduce windows.
- Stereo input should be converted to mono before most feature/model workflows with `audioBasicIO.stereo_to_mono(...)`.
- Silence-only or constant signals can lead to NaNs, low-variance features, or degenerate clustering. Use the feature smoke script to inspect finite values and shapes.

## What to run next

- Installation/import/dependency check: [`scripts/check_pyaudioanalysis_env.py`](../scripts/check_pyaudioanalysis_env.py).
- Feature shape/debug check: [`../sub-skills/feature-extraction/scripts/feature_smoke.py`](../sub-skills/feature-extraction/scripts/feature_smoke.py).
- Classifier smoke: [`../sub-skills/classification-regression/scripts/classification_smoke.py`](../sub-skills/classification-regression/scripts/classification_smoke.py).
- Segmentation/silence smoke: [`../sub-skills/segmentation-diarization/scripts/segmentation_smoke.py`](../sub-skills/segmentation-diarization/scripts/segmentation_smoke.py).
- CLI and media-tool probes: [`../sub-skills/cli-and-io/scripts/inspect_cli.py`](../sub-skills/cli-and-io/scripts/inspect_cli.py) and [`../sub-skills/cli-and-io/scripts/audio_io_smoke.py`](../sub-skills/cli-and-io/scripts/audio_io_smoke.py).
