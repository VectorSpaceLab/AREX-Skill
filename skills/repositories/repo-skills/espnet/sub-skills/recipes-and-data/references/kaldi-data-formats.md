# Kaldi-style Data Formats for ESPnet2

ESPnet2 recipes use Kaldi-style data directories. A split such as `data/train`, `data/dev`, or `data/test` normally contains these files:

```text
data/train/
  text       # utterance id followed by transcript or task label text
  wav.scp    # utterance id or recording id followed by audio path/pipe
  utt2spk    # utterance id to speaker id
  spk2utt    # speaker id to utterance ids
  segments   # optional utterance id, recording id, start, end
```

## File contracts

`text`:

```text
utt1 hello world
utt2 another transcript
```

`wav.scp` without `segments` uses utterance ids:

```text
utt1 /data/audio/utt1.wav
utt2 ffmpeg -i video.mp4 -f wav -acodec pcm_s16le - |
```

`wav.scp` with `segments` uses recording ids, not utterance ids:

```text
rec1 /data/audio/long_recording.wav
```

`segments`:

```text
utt1 rec1 0.00 1.50
utt2 rec1 1.50 3.20
```

`utt2spk` and `spk2utt` must be exact inverses. If the corpus has no speaker metadata, either use utterance ids as speaker ids or one stable dummy speaker consistently.

## Validation checklist

- Keys are unique in every file.
- Every `text` key appears in `utt2spk`.
- Without `segments`, every `text`/`utt2spk` key appears in `wav.scp`.
- With `segments`, every `text`/`utt2spk` key appears in `segments`, and every `segments` recording id appears in `wav.scp`.
- Segment times are numeric and `end > start`.
- `spk2utt` exactly matches the inverse mapping from `utt2spk`.
- Pipe commands ending in `|` have their host tools installed (`ffmpeg`, `sph2pipe`, etc.).

Use the bundled validator for structural checks that do not read audio:

```bash
python sub-skills/recipes-and-data/scripts/validate_kaldi_data_dir.py data/train
```

This validator intentionally does not decode audio or run recipe scripts; it catches common layout errors before expensive runs.
