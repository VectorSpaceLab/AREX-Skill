# Data formats

## LJ Speech input

```text
<base>/LJSpeech-1.1/metadata.csv
<base>/LJSpeech-1.1/wavs/<utterance-id>.wav
```

Each metadata row is pipe-separated. The implementation uses the first field
to construct `<utterance-id>.wav` and the third field as training text.

## Blizzard input

```text
<base>/Blizzard2012/<Book>/sentence_index.txt
<base>/Blizzard2012/<Book>/wav/<id>.wav
<base>/Blizzard2012/<Book>/lab/<id>.lab
```

The built-in list prioritizes `ATrampAbroad` and
`TheManThatCorruptedHadleyburg`. Rows are filtered by confidence and the
preprocessor trims silence using label timing. Overlong utterances are skipped.

## Generated output

The preprocessor writes a directory such as `<base>/training/` containing:

- linear spectrogram `.npy` files, saved as `float32` with shape
  `[time_frames, num_freq]`;
- mel spectrogram `.npy` files, saved as `float32` with shape
  `[time_frames, num_mels]`;
- `train.txt`, one pipe-separated row:
  `linear_filename|mel_filename|n_frames|text`.

`n_frames` is the time axis length before the source spectrogram is transposed
for saving. The default hparams use `num_freq=1025` and `num_mels=80`.

## Custom preprocessor contract

For each utterance, load and resample audio to the configured sample rate,
compute `audio.spectrogram(wav)` and `audio.melspectrogram(wav)`, cast to
`float32`, save transposed arrays with `allow_pickle=False`, and return the
four fields above. Keep filenames relative to the output directory.
