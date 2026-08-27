# Data formats

## Audio inputs

- **Preferred format:** WAV.
- **Also readable through `audioBasicIO.read_audio_file(...)`:** `.wav`, `.aif`,
  `.aiff`, `.mp3`, `.au`, `.ogg`.
- **Segmentation and diarization workflows:** safest with mono WAV arrays.
- **Stereo handling:** the core APIs call `stereo_to_mono(...)` where needed, so
  you can usually pass a stereo signal array, but a mono WAV is the least risky
  input.

## Segment annotations

The canonical ground-truth file for segmentation and diarization is a
three-column, tab-separated `.segments` file:

```text
0.00	0.64	silence
0.64	1.83	speech
1.83	2.40	music
```

Rules:
- Column 1 = segment start time in seconds.
- Column 2 = segment end time in seconds.
- Column 3 = label string.
- There is no header row.
- Rows that do not have exactly three columns are ignored by the current reader.

This format is used by:
- `train_hmm_from_file`
- `train_hmm_from_directory`
- `hmm_segmentation` when a GT sidecar is provided
- `speaker_diarization` when a GT sidecar is present
- `evaluate_segmentation_classification_dir`
- `speaker_diarization_evaluation`
- the Audacity splitting helpers

## Time units

All segmentation-related timing arguments are in **seconds**:

- `mid_window`, `mid_step`
- `st_win`, `st_step`
- `smooth_window`
- `short_window`, `short_step`
- `thumb_size`
- annotation start and end values in `.segments`

The APIs convert seconds to samples internally when needed.

## HMM model artifacts

`save_hmm(...)` writes a single artifact file containing sequential pickle objects
in this order:

1. the trained HMM model
2. the class-name list
3. `mid_window`
4. `mid_step`

Practical consequences:
- Keep the whole file together; it is not a directory of separate pieces.
- The filename extension is not important, but the contents must stay intact.
- Retrain in the target environment if the pickle format becomes incompatible.

## Segmentation outputs

### `labels_to_segments(...)`

- Input: per-window class labels.
- Output: a segment matrix shaped `N x 2` with start and end times in seconds.
- The parallel `classes` list stores the label for each segment.

### `hmm_segmentation(...)` and `mid_term_file_classification(...)`

- `labels` is a per-window label sequence.
- `class_names` is the list of string class names used for the mapping.
- `accuracy` and `cm` are only meaningful when a matching `.segments` file is
  available.

### `silence_removal(...)`

- Returns a list of `[start_sec, end_sec]` intervals.
- The intervals are intended for later cutting, not for direct plotting.

### `music_thumbnailing(...)`

- Returns four seconds-based endpoints: `A1`, `A2`, `B1`, `B2`.
- Also returns the filtered similarity matrix used to find the match.

### `speaker_diarization(...)`

- Returns a label per mid-term window.
- Class names are synthetic speaker labels such as `speaker0`, `speaker1`, ...
- Purity metrics are only computed when a matching `.segments` file exists.

## Audacity annotation splitting

The legacy splitter uses the same tab-separated annotation format but turns it
into audio clips.

- `annotation2files(...)` writes flat clips whose names encode the source audio
  name, label, and time span.
- `annotation2folders(...)` writes clips into `folderPath/<label>/...`.
- `folderAnnotation2folders(...)` batch-applies the folder layout to a directory
  of `.segments` files.

Keep the destination under a controlled output root so that generated clips do
not overwrite source material.

## Legacy CLI wrapper side effects

The wrapper-level behaviors documented by `audioAnalysis.py` include:

- silence removal writing one derived WAV per detected segment
- thumbnailing writing two thumbnail WAVs next to the source file
- diarization and HMM inference printing results without writing model files

Use the APIs directly if you only need intervals or labels.
