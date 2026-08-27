# pyAudioAnalysis CLI Reference

This reference distills the pyAudioAnalysis 0.3.14 legacy command-line surface. The package exposes command-line behavior through package files, not through a `console_scripts` entry point.

## Evidence basis

Distilled from `setup.py`, `requirements.txt`, `README.md`, `pyAudioAnalysis/audioAnalysis.py`, `pyAudioAnalysis/audacityAnnotation2WAVs.py`, `pyAudioAnalysis/convertToWav.py`, `pyAudioAnalysis/audioBasicIO.py`, `pyAudioAnalysis/audioVisualization.py`, and maintainer test command patterns. The maintainer shell tests are useful for intent and examples, but many assume external datasets and should remain reference-only.

## Legacy execution pattern

There is no installed `pyAudioAnalysis` command. The main CLI is the legacy `audioAnalysis.py` script inside the installed package, and it imports sibling modules with top-level import names. Running it as a package module often fails:

```bash
python -m pyAudioAnalysis.audioAnalysis --help  # likely ModuleNotFoundError: ShortTermFeatures
```

Use one of these safer patterns instead:

```bash
# Print discovered tasks and help without running an analysis task.
python sub-skills/cli-and-io/scripts/inspect_cli.py
python sub-skills/cli-and-io/scripts/inspect_cli.py --task fileSpectrogram
```

For direct legacy invocation, resolve the installed script and prepend its package directory to `PYTHONPATH` for this command only:

```bash
PAA_SCRIPT=$(python - <<'PY'
import importlib.util
from pathlib import Path
spec = importlib.util.find_spec("pyAudioAnalysis")
if spec is None or spec.origin is None:
    raise SystemExit("pyAudioAnalysis is not importable in this Python environment")
print(Path(spec.origin).with_name("audioAnalysis.py"))
PY
)
PAA_DIR=$(dirname "$PAA_SCRIPT")
PYTHONPATH="$PAA_DIR${PYTHONPATH:+:$PYTHONPATH}" \
  python "$PAA_SCRIPT" fileSpectrogram -i "$AUDIO_WAV"
```

Prefer `subprocess.run([...], check=True)` over `shell=True` when building commands from Python, especially for audio paths with spaces.

## `audioAnalysis.py` subcommands

All commands begin with the legacy script path followed by one subcommand. Use `scripts/inspect_cli.py --task TASK` for live help from the installed package.

| Subcommand | Main flags | Behavior and side effects | Route for API depth |
|---|---|---|---|
| `dirMp3toWav` | `-i/--input DIR`, `-r/--rate {8000,16000,32000,44100}`, `-c/--channels {1,2}` | Converts all `.mp3` files in a directory to `.wav` using `audioBasicIO.convert_dir_mp3_to_wav`; uses MP3 tags for output names when available. Requires `ffmpeg`, `eyed3`, and shell-safe paths. Writes WAVs next to MP3 files. | I/O stays here; feature/model work routes onward. |
| `dirWavResample` | `-i/--input DIR`, `-r/--rate {8000,16000,32000,44100}`, `-c/--channels {1,2}` | Converts `.wav` files using `avconv`; creates `Fs<RATE>_NC<CHANNELS>` inside the input directory and removes an existing folder with that exact name before rewriting. | I/O stays here. |
| `featureExtractionFile` | `-i/--input AUDIO`, `-o/--output FILE`, `-mw/--mtwin SEC`, `-ms/--mtstep SEC`, optional `-sw/--stwin SEC` default `0.050`, `-ss/--ststep SEC` default `0.050` | Writes mid-term and short-term feature outputs through `MidTermFeatures.mid_feature_extraction_to_file`. | Feature extraction sibling. |
| `featureExtractionDir` | `-i/--input DIR`, `-mw/--mtwin SEC`, `-ms/--mtstep SEC`, optional `-sw/--stwin`, `-ss/--ststep` | Extracts features for audio files in a folder and writes feature output files. | Feature extraction sibling. |
| `beatExtraction` | `-i/--input AUDIO`, optional `--plot` | Reads audio, computes short-term features, then estimates beat. `--plot` creates matplotlib windows/files depending on backend. | Feature/beat sibling. |
| `featureVisualization` | `-i/--input DIR` | Calls `audioVisualization.visualizeFeaturesFolder(..., "pca", "")`. Reads WAV files, computes features, shows matplotlib and Plotly views; Plotly can open a browser. | Visualization sibling. |
| `fileSpectrogram` | `-i/--input AUDIO` | Reads audio, converts stereo to mono, computes and plots a spectrogram. It calls plotting code unconditionally. | Feature/visualization sibling. |
| `fileChromagram` | `-i/--input AUDIO` | Reads audio, converts stereo to mono, computes and plots a chromagram. It calls plotting code unconditionally. | Feature/visualization sibling. |
| `trainClassifier` | `-i/--input DIR [DIR ...]`, `--method {svm,svm_rbf,knn,randomforest,gradientboosting,extratrees}`, optional `--beat`, `-o/--output MODEL` | Trains a segment classifier from class folders; requires at least two class directories. Writes model output files using the provided base name. | Classification/model-training sibling. |
| `classifyFile` | `-i/--input AUDIO`, `--model {svm,svm_rbf,knn,randomforest,gradientboosting,extratrees}`, `--classifier MODEL_PATH` | Applies an existing classifier and prints class probabilities plus winner. | Classification sibling. |
| `classifyFolder` | `-i/--input DIR_OR_PREFIX`, `--model {svm,svm_rbf,knn,randomforest,gradientboosting,extratrees}`, `--classifier MODEL_PATH`, optional `--details` | Classifies matching WAV/AIFF/MP3 paths and prints distribution; `--details` prints per-file classes. The parser option is `--details` exactly. | Classification sibling. |
| `trainRegression` | `-i/--input DIR`, `--method {svm,randomforest,svm_rbf}`, optional `--beat`, `-o/--output MODEL` | Trains a regression model from a directory plus CSV ground truth. Writes model output files. | Regression/model sibling. |
| `regressionFile` | `-i/--input AUDIO`, `--model {svm,svm_rbf,randomforest}`, `--regression MODEL_PATH` | Applies a trained regression model and prints named outputs. | Regression/model sibling. |
| `regressionFolder` | `-i/--input DIR`, `--model {svm,knn}`, `--regression MODEL_PATH` | Applies regression to WAV files and plots histograms. | Regression/model sibling; plotting risk stays here. |
| `trainHMMsegmenter_fromfile` | `-i/--input AUDIO`, `--ground SEGMENTS`, `-o/--output MODEL`, `-mw/--mtwin SEC`, `-ms/--mtstep SEC` | Trains an HMM segmenter from one audio file and tab-delimited segment labels. Writes model output files. | Segmentation/HMM sibling. |
| `trainHMMsegmenter_fromdir` | `-i/--input DIR`, `-o/--output MODEL`, `-mw/--mtwin SEC`, `-ms/--mtstep SEC` | Trains an HMM from multiple annotated files in a folder. Writes model output files. | Segmentation/HMM sibling. |
| `segmentClassifyFile` | `-i/--input AUDIO`, `--model {svm,svm_rbf,knn,randomforest,gradientboosting,extratrees}`, `--modelName MODEL_PATH` | Applies a fixed-window classifier for segmentation/classification. Looks for a `.segments` file beside WAV/MP3 input for ground-truth plotting/evaluation. | Segmentation/classification sibling. |
| `segmentClassifyFileHMM` | `-i/--input AUDIO`, `--hmm MODEL_PATH` | Applies an HMM segmenter and requests plotted results. Looks for a `.segments` file beside WAV input. | Segmentation/HMM sibling. |
| `segmentationEvaluation` | `-i/--input DIR`, `--model {svm,knn,hmm}`, `--modelName MODEL_PATH` | Evaluates segmentation/classification for WAV files and segment CSV files in a folder. | Segmentation sibling. |
| `silenceRemoval` | `-i/--input AUDIO`, optional `-s/--smoothing SEC` default `1.0`, `-w/--weight FLOAT` default `0.5` | Detects non-silent regions and writes many segment WAVs named from the input plus start/end times. Existing files with identical names can be overwritten. | Segmentation/silence sibling for algorithm details. |
| `speakerDiarization` | `-i/--input AUDIO`, `-n/--num N`, optional `--flsd` | Performs speaker diarization and requests plots. | Segmentation/diarization sibling. |
| `speakerDiarizationScriptEval` | `-i/--input DIR`, `--LDAs INT [INT ...]` | Evaluation helper for diarization experiments; maintainer usage assumes an external dataset. | Reference-only unless a local bounded dataset is prepared. |
| `thumbnail` | `-i/--input AUDIO`, optional `-s/--size SEC` default `10.0` | Computes music thumbnail regions, writes two thumbnail audio files beside the input, and shows a self-similarity plot. | Segmentation/thumbnail sibling. |

## Other legacy scripts

### `audacityAnnotation2WAVs.py`

This helper has no argparse help. It uses top-level `audioBasicIO` imports and writes segmented WAV clips based on tab-delimited annotations.

- Single file pattern: `-f <audiofilepath> <annotationfilepath>`.
- Directory pattern: `-d <annotationfolderpath>`; searches `.txt` and `.csv` annotations and expects matching `.wav` or `.mp3` audio basenames.
- Annotation rows are `<startTime>\t<endTime>\t<classLabel>`.
- Outputs are written beside the source audio for `annotation2files`, with spaces replaced by underscores.

Use the same package-directory `PYTHONPATH` pattern as `audioAnalysis.py` if invoking this helper. Prefer scratch copies because outputs are produced next to the source audio.

### `convertToWav.py`

This helper scans a folder for `.webm`, `.avi`, `.mkv`, `.mp4`, `.mp3`, `.flac`, and `.ogg`, then calls `ffmpeg` to create same-basename `.wav` files with the requested sample rate and channel count.

Pattern:

```bash
python <installed-convertToWav.py> <folder> <sampling-rate> <channels>
```

It uses shell command strings. Use controlled scratch folders, quote paths when shelling, and expect existing same-basename `.wav` outputs to be overwritten by `ffmpeg` behavior unless guarded externally.

## Minimal safe command-building checklist

- Resolve the installed legacy script programmatically; do not assume a console command exists.
- Put the installed package directory on `PYTHONPATH` only for the legacy-script process.
- Pass subprocess arguments as a list from Python. In shell, quote every variable: `"$AUDIO_WAV"`, `"$MODEL"`, `"$OUT"`.
- Use scratch copies for any command that converts, segments, thumbnails, or writes model/feature outputs.
- Decide display behavior before calling plot-heavy commands; for headless runs use a noninteractive matplotlib backend or prefer API calls that expose plot flags.
- Treat large external-dataset maintainer scripts as examples of intended command shapes, not as mandatory verification steps.
