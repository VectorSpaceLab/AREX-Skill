# pyAudioAnalysis package overview

## When to read

Read this after the root router when you need the package module map, dependency assumptions, workflow boundaries, or the relationship between Python APIs and the legacy CLI.

## Public package identity

- Distribution name: `pyAudioAnalysis`.
- Import root: `pyAudioAnalysis`.
- Version distilled for this skill: `0.3.14`.
- Core dependencies from package metadata: `matplotlib`, `simplejson`, `scipy`, `numpy`, `hmmlearn`, `eyeD3`, `pydub`, `scikit-learn`, `tqdm`, `plotly`, `pandas`, and `imblearn`/`imbalanced-learn`.
- Required compute backend: CPU.
- Optional system tools: `ffmpeg` or `avconv` for MP3/media conversion and pydub-backed generic decoding.

## Module map

| Module | Main responsibility | Best route |
| --- | --- | --- |
| `audioBasicIO` | Read WAV/AIFF/MP3/AU/OGG, convert stereo to mono, convert directories between media/WAV formats. | `cli-and-io` for formats/conversion; `feature-extraction` for analysis inputs. |
| `ShortTermFeatures` | Short-term features, MFCC/chroma/spectral helpers, spectrogram, chromagram. | `feature-extraction`. |
| `MidTermFeatures` | Mid-term feature statistics, directory feature extraction, beat extraction, feature export. | `feature-extraction`. |
| `audioTrainTest` | Classifier/regression training, model loading, file/folder classification/regression, evaluation helpers. | `classification-regression`. |
| `audioSegmentation` | HMM segmentation, mid-term file classification, silence removal, diarization, thumbnails. | `segmentation-diarization`. |
| `audioAnalysis.py` | Legacy argparse command dispatcher. | `cli-and-io`; route task-specific details to sibling sub-skills. |
| `audioVisualization` | Folder feature visualization through dimensionality reduction and plotting. | `cli-and-io` for command/plot behavior; `feature-extraction` for data preparation. |
| `audacityAnnotation2WAVs.py` | Split Audacity-style annotations into labeled WAV snippets. | `segmentation-diarization` data formats. |
| `convertToWav.py` | Shells out to `ffmpeg` to convert media files to WAV. | `cli-and-io` audio formats and conversion troubleshooting. |

## Workflow map

| User goal | Primary sub-skill | Key inputs | Key outputs / validation |
| --- | --- | --- | --- |
| Extract short-term features | `feature-extraction` | mono signal array, sample rate, short window/step in samples | feature matrix rows align with feature names. |
| Extract mid-term or directory features | `feature-extraction` | WAV path/folder, mid/short windows and steps in seconds or samples depending on API | mid feature matrix, short feature matrix, optional NPY/CSV outputs. |
| Train clip classifier | `classification-regression` | one folder per class, model type, model prefix | pickle model files; held-out classification or model artifact checks. |
| Classify a file or folder | `classification-regression` | trusted model files, audio path/folder, model type | class id/probabilities/names or folder counts. |
| Train/apply audio regression | `classification-regression` | audio folder plus target CSVs, model type, output prefix | one model artifact set per target; numeric regression outputs. |
| Segment an audio file | `segmentation-diarization` | classifier/HMM model, audio file, optional segment ground truth | time labels, accuracy/confusion matrix when ground truth exists. |
| Remove silence | `segmentation-diarization` | signal array, sample rate, short window/step, smoothing/weight | list of `[start, end]` spans; CLI wrapper can write snippets. |
| Run diarization | `segmentation-diarization` | WAV, number of speakers, optional LDA dimension | cluster labels; optional purity metrics when ground truth segments exist. |
| Inspect CLI / build command | `cli-and-io` | desired task and input/model paths | command template, flag list, side-effect warnings. |
| Verify install or media support | `cli-and-io` plus root script | Python environment and optional media tools | JSON/status report, feature smoke, ffmpeg/avconv availability. |

## Legacy CLI relationship

The package does not declare a console-script entry point. The public command surface is the legacy `audioAnalysis.py` script. In version 0.3.14 that file imports sibling modules by top-level names such as `ShortTermFeatures`, so direct package-module execution can fail. Use the `cli-and-io` helper `scripts/inspect_cli.py` to inspect installed CLI tasks safely, or call Python APIs directly.

## Data and model assets

The source package includes sample WAV files, `.segments` annotation files, HMM/classifier model pickles, and speech-emotion target CSVs. They are evidence for formats and native verification but this generated skill does not bundle the binary sample/model assets. Bundled scripts synthesize tiny WAV fixtures or accept explicit user-provided paths instead.

## Verification anchors

The skill was checked against:

- live signatures for important APIs in `audioBasicIO`, `ShortTermFeatures`, `MidTermFeatures`, `audioTrainTest`, `audioSegmentation`, and `audioVisualization`;
- package import and dependency smoke checks;
- synthetic feature extraction, audio I/O, classification, and silence-removal helpers;
- CLI parser inspection; and
- native repository pytest candidates recorded in the review artifacts.
