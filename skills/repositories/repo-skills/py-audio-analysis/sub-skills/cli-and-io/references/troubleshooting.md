# CLI and Audio I/O Troubleshooting

## `ModuleNotFoundError: ShortTermFeatures` from `python -m pyAudioAnalysis.audioAnalysis`

Cause: the legacy CLI imports package siblings with top-level names such as `ShortTermFeatures`, `MidTermFeatures`, `audioTrainTest`, `audioSegmentation`, `audioVisualization`, and `audioBasicIO`. Package-module execution sets `sys.path` differently, so those imports are not found.

Fix:

- Do not run the legacy CLI with `python -m pyAudioAnalysis.audioAnalysis`.
- Use [`../scripts/inspect_cli.py`](../scripts/inspect_cli.py) to locate the installed package and print help safely.
- For direct invocation, run the installed `audioAnalysis.py` script file and prepend that installed package directory to `PYTHONPATH` for only that process. See [`cli-reference.md`](cli-reference.md#legacy-execution-pattern).
- For custom wrappers, insert the installed package directory itself on `sys.path` before importing `pyAudioAnalysis.audioAnalysis` or before executing the legacy script.

## No `pyAudioAnalysis` console command

Cause: package metadata declares only the `pyAudioAnalysis` package and dependencies; it does not register a console script entry point.

Fix: resolve and run installed package scripts programmatically, or call the public APIs from the API-focused sibling sub-skills.

## Missing `aifc`, `ffmpeg`, `avconv`, `pydub`, or `eyed3`

Symptoms:

- MP3/AU/OGG reads print `Error: file not found or other I/O error. (DECODING FAILED)` and return `fs=-1` with an empty signal.
- `dirMp3toWav` prints an `ffmpeg` command but no WAVs appear.
- `dirWavResample` prints an `avconv` command but no resampled WAVs appear.
- Importing `audioBasicIO` fails because `aifc`, `pydub`, or `eyed3` is unavailable.

Fix:

1. Run `python sub-skills/cli-and-io/scripts/audio_io_smoke.py` to check Python import dependencies and executable availability.
2. If `aifc` is missing, use a Python runtime that provides it or a validated compatibility shim; pyAudioAnalysis imports `aifc` before any WAV-specific path can run.
3. Install Python package dependencies in the active environment if `pydub` or `eyed3` is missing.
4. Install a system `ffmpeg` executable for compressed-media decode and MP3/video conversion.
5. If a workflow specifically uses `dirWavResample`, provide `avconv` or replace that conversion step with a controlled external conversion command that you validate separately. pyAudioAnalysis does not substitute `ffmpeg` for `avconv` in that helper.
6. After any decode, check `fs > 0` and `signal.size > 0` before feature extraction or segmentation.

## Conversion outputs are destructive or surprising

Risky side effects:

- `dirWavResample` deletes and recreates the `Fs<RATE>_NC<CHANNELS>` folder under the input directory.
- `dirMp3toWav` writes WAVs beside MP3s; tag-derived output names can collide or contain spaces.
- `convertToWav.py` writes same-basename `.wav` files beside source media and relies on `ffmpeg` overwrite behavior.
- `silenceRemoval` writes many `<input>_<start>-<end>.wav` files beside the input.
- `thumbnail` writes `_thumb1` and `_thumb2` audio files beside the input and then shows a plot.
- `audacityAnnotation2WAVs.py` writes segmented WAV files beside the source audio or into label folders.

Fix:

- Copy inputs to a scratch directory before running conversion, silence-removal, annotation-splitting, or thumbnail commands.
- Preflight output names before running tag-derived MP3 conversion.
- Avoid running these helpers in directories with valuable existing `Fs...` conversion outputs.
- If reproducibility matters, record the exact sample rate, channel count, and external media tool version used for conversion.

## Plotting, display, and browser side effects

Affected commands include `fileSpectrogram`, `fileChromagram`, `featureVisualization`, `regressionFolder`, `segmentClassifyFileHMM`, `speakerDiarization`, `thumbnail`, and `beatExtraction --plot`. Some wrappers call `plt.show()` or Plotly display functions unconditionally.

Fix:

- In headless environments, set a noninteractive matplotlib backend before running a plotting command, for example `MPLBACKEND=Agg`.
- Prefer API calls from the feature, model, or segmentation sibling sub-skills when they expose `plot=False` or `plot_res=False`.
- Expect Plotly paths to create or open browser-oriented files or windows for visualization workflows.
- Do not use a plotting CLI command as a smoke test unless the display behavior is intentional.

## Paths with spaces or shell metacharacters fail

Cause: several maintainer command examples use shell strings, and some conversion helpers internally build shell commands. Unquoted paths break or can change command meaning.

Fix:

- From Python, build commands as argument lists with `subprocess.run([...], check=True)` whenever possible.
- In shell, quote variables: `"$AUDIO"`, `"$MODEL"`, `"$OUT_DIR"`.
- Avoid `eval` for generated command strings.
- Prefer scratch paths with simple names when exercising legacy conversion helpers that call `os.system` internally.

## `classifyFolder` finds no files

Cause: the legacy implementation concatenates the input string and glob suffixes like `input + "*.wav"`. A directory path without a trailing separator may become `folder*.wav` instead of `folder/*.wav`.

Fix: pass a folder prefix that includes the separator, or use an explicit prefix pattern compatible with the legacy glob behavior.

## External dataset shell tests are not runnable smoke checks

Maintainer shell scripts document command shapes, but many assume large external datasets, trained model files, or maintainer-specific data organization. They are not safe publication or runtime verification commands by themselves.

Fix:

- Use them only as evidence for intended CLI arguments and workflows.
- Build bounded synthetic or local-data cases instead.
- For CLI/I/O verification, prefer `inspect_cli.py`, `audio_io_smoke.py`, and tiny generated WAV files.

## Compressed audio decodes silently fail into empty arrays

Cause: `audioBasicIO.read_audio_generic` catches all exceptions and prints a generic decode failure, then returns `fs=-1` and an empty NumPy array.

Fix:

```python
from pyAudioAnalysis import audioBasicIO
fs, signal = audioBasicIO.read_audio_file(audio_path)
if fs <= 0 or getattr(signal, "size", 0) == 0:
    raise RuntimeError("pyAudioAnalysis could not decode the audio file")
```

Probe `pydub` and `ffmpeg`, convert to WAV in a controlled scratch directory, and retry on the WAV if the downstream task does not require native compressed-file handling.

## Model or annotation path not found

Several CLI wrappers check model and annotation files explicitly and raise exceptions such as `Input model_name not found!` or `Input audio file not found!`. Segmentation wrappers may infer a `.segments` path beside the input audio.

Fix:

- Validate model, audio, and `.segments` paths before invoking the CLI.
- Keep model-training and segmentation algorithm details in the appropriate API-focused sibling sub-skill.
- When using CLI examples, replace maintainer dataset names with local bounded fixtures and quote all paths.
