# Troubleshooting

## Config and paths

- **Empty or unexpected paths:** `load_config` expands `${VAR}` but an unset
  variable can remain literal. Print the resolved config, use absolute or
  deliberately rooted paths, and verify `annotations_path` and
  `spectrograms_dir` before running a step.
- **Invalid window geometry:** a zero/negative hop causes division or endless
  windowing behavior. Enforce `sample_rate > 0`, `window_size_sec > 0`, and
  `0 <= overlap_sec < window_size_sec`; remember that 5 seconds with 4 seconds
  overlap means a 1-second hop.
- **Balanced strategy errors:** `negative_proportion=1` divides by zero; values
  outside `[0,1)` are invalid. Too few negative candidates is normal when
  annotations cover most of a recording; report the achieved, not requested,
  proportion.
- **Multiclass mismatch:** `num_classes` must be 2 or greater, labels must be
  contiguous integer ids starting at 0, and class names must align with output
  columns. A config claiming four classes with two names is incomplete; fix
  config/CSV metadata before constructing a model.

## Annotations and windows

- **No windows:** check that sound durations exceed the window size, audio
  annotations reference the exact `sounds[].id`, and `file_name_path` values
  are resolvable. Inference directory scanning is non-recursive and ignores
  hidden files.
- **Unexpected labels:** sliding binary mode labels any qualifying overlap as
  `1`; multiclass uses the first qualifying annotation's `category_id` and adds
  `ann_overlap` in samples. Check category ids and overlap threshold units.
- **Missing annotation keys:** the builder needs `sounds`, `annotations`,
  `duration`, `file_name_path`, `sound_id`, `t_min`, and `t_max`; metadata-only
  category records are not enough.

## Spectrogram cache and CSVs

- **Missing `.npy` files:** rerun the spectrogram step with the same
  `sample_rate`, window boundaries, and output directory. The cache name is
  based on the audio basename/start/end. Check the CSV's `spec_name` against
  the actual directory; do not silently train on a filtered empty dataframe.
- **Source-name mismatch:** companion versions may produce `sid...` CSV names
  while the core spectrogram writer defaults to audio-basename names. Use one
  naming function consistently; the bundled preparation helper uses the core
  default and records the path explicitly.
- **Bad shape or corrupted cache:** `.npy` should be 2-D or a supported 3-D
  channel layout. Delete only the bad cache after confirming the audio and
  parameters, then regenerate. Do not treat an `EOFError` as a class-label
  issue.
- **Split failure:** grouped stratification needs enough distinct `sound_id`
  groups and class support. Reduce split complexity only with an explicit
  validation decision; never split overlapping windows randomly by row.

## Device and model

- **CPU-only host:** the spectrogram function selects CPU when CUDA is absent;
  expect slower processing. The training companion configures a GPU trainer,
  so do not start it as if CPU training were supported by this route.
- **CUDA requested but unavailable:** use `--device cpu`, verify tensors and
  checkpoint placement, and report that acceleration was not tested. A CUDA
  smoke check is not evidence of model-quality or training performance.
- **Checkpoint load triggers a weight download:** constructors use ImageNet
  backbone weights. Stop, provision the required weights through an approved
  offline/cache process, or use a compatible checkpoint/environment; never
  hide the network action in a helper.
- **Eager package import fails around legacy YOLOv5:** the root package imports
  many model families eagerly, and older YOLOv5 dependencies can conflict with
  modern Python/Torch environments. Classify this as an environment
  compatibility issue, use a supported isolated environment, and do not expose
  private compatibility shims in runtime guidance.

## Result interpretation

- **Binary confidence:** `probability` is sigmoid output and
  `confidence=abs(probability-0.5)*2`; `prediction` is thresholded at 0.5 by
  the companion inference writer. A high confidence can mean a confident
  negative.
- **Multiclass confidence:** the companion CSV writer emits per-class
  probabilities but does not add a generic confidence column. Use the maximum
  class probability only if your downstream contract explicitly defines it.
- **Per-second aggregation:** it averages overlapping binary predictions,
  probabilities, and confidences by overlap duration. `prediction` is 1 when
  averaged prediction is at least 0.5. Missing required binary columns means
  the reducer is not applicable.
