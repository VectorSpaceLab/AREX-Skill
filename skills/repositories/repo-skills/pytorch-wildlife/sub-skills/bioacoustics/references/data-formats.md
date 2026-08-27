# Audio data and cache formats

## COCO-like annotation JSON

The window builder expects a JSON object with at least:

```json
{
  "info": {},
  "categories": [{"id": 0, "name": "noise"}],
  "sounds": [{
    "id": 0,
    "file_name_path": "recordings/site_a.wav",
    "duration": 30.0,
    "sample_rate": 48000
  }],
  "annotations": [{
    "anno_id": 0,
    "sound_id": 0,
    "category_id": 1,
    "category": "target",
    "t_min": 10.0,
    "t_max": 12.5
  }]
}
```

`build_windows` directly consumes `sounds[].id`, `file_name_path`,
`duration`, and `sample_rate`, plus `annotations[].sound_id`, `t_min`,
`t_max`, and optionally `category_id`. Extra metadata such as latitude,
longitude, date, project, frequency bounds, and category descriptions is
allowed. `file_name_path` is also used for substring matching against each
configured `datasets` name; an unmatched file gets `dataset: null`.
Resolve relative audio paths against the configured data root before reading.

`AnnotationCreator` can emit this general shape. Its category row name follows
the input table's first column, so consumers should ensure the saved categories
have stable integer `id` values and a useful human-readable name/label. An
annotation must reference a real sound, have nonnegative times, and satisfy
`t_max >= t_min`; clip or reject times beyond the recording deliberately.

## Window records

`build_windows(annotation_file, window_size_sec, overlap_sec, sample_rate,
datasets_names, strategy="sliding", negative_proportion=0.5,
multiclass=False, min_overlap_sec=0, custom_builder=None)` returns:

- `window_id`: integer sequence (balanced negatives are assigned ids after
  positive windows);
- `dataset`, `sound_id`, `sample_rate`, `start`, `end`, `label`;
- `ann_overlap` only in multiclass mode, measured in samples.

Sliding scans complete windows across each sound. A window is positive when an
annotation intersects it by more than `min_overlap_sec` (the default zero means
any positive intersection). Balanced centers positives on annotations, then
randomly samples candidate negatives to achieve the requested negative
proportion; selection uses NumPy's random state and is not deterministic unless
that state is controlled. Customized delegates to a callable receiving
`(annotation_file, sample_rate, datasets_names)`.

`build_inference_windows(audios_source, window_size_sec, overlap_sec,
sample_rate)` returns `window_id`, `sound_path`, `start`, and `end` for complete
windows only. A directory scans non-hidden `.wav`, `.flac`, `.mp3`, `.m4a`,
`.aac`, and `.ogg` names (non-recursively); a list uses the supplied order.
`start`/`end` are samples at the target sample rate, while audio duration is
measured by librosa first.

## Spectrogram cache and training CSV

`compute_mel_spectrograms_gpu` saves a 2-D mel array per window, normally
`<audio-basename>_<start>_<end>.npy`, under `spectrograms_dir`. Existing files
are skipped. The default tensor settings are `n_fft=2048`, `hop_length=512`,
`n_mels=224`, `top_db=80`; `center=False`, power mel scaling, and a target
Nyquist of `sample_rate/2` are implementation details. Stereo is reduced by
`left`, `right`, or `mean`; resampling is performed when source and target
rates differ. `float16` or `float32` storage is supported.

Training CSVs need at least `spec_name` and `label` (or the configured `x_col`
and `y_col`). `BioacousticsDataset` resolves a relative `spec_name` under its
`root`, loads `.npy`, converts it to `[C,H,W]`, optionally applies per-sample
normalization, resize, PCEN, and training augmentation, then returns
`(tensor, int(label), path)`. A 2-D array becomes one channel; a channel-last
3-D array with one, two, or three channels is moved to channel-first.
`BioacousticsInferenceDataset` does not require labels.

A safe split should group by `sound_id`, check every referenced `.npy` exists,
and preserve label support in each split. The adapted preparation helper uses
the core default cache naming consistently; do not mix it with a CSV generated
by a different naming convention without rewriting `spec_name`.
