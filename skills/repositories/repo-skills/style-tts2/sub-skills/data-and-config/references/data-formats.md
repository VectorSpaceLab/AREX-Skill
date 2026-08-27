# Data formats

## Training and validation lists

StyleTTS2 training code reads each line with a simple pipe split.
The canonical public row shape is:

```text
filename.wav|IPA transcription|speaker
```

Examples from the shipped lists use the same shape, with a single-speaker dataset typically carrying `speaker=0` and multispeaker data using a stable integer speaker id per talker.

### Rules
- Keep the file name in the first field.
- Keep the IPA transcription in the second field.
- Keep the speaker id in the third field.
- Do not include extra `|` characters inside the transcription.
- Use plain integer-like speaker ids so the dataset can convert them back to integers.

### Loader behavior
- Rows with **3 fields** are used as-is.
- Rows with **2 fields** are accepted by the loader and get speaker id `0` internally.
- Rows with **1 field** or **more than 3 fields** will break the dataset loader.
- The same-speaker reference sampler compares speaker ids as strings, so omitting the speaker column is risky even when the loader can pad it.

### Why speaker ids matter
StyleTTS2 samples a reference utterance from the same speaker during training. That lookup depends on the third column, so multispeaker data should always provide explicit speaker labels.

## OOD text files

The `OOD_data` file feeds the out-of-distribution text sampler used by the SLM-adversarial stage.
The loader accepts either of these forms:

```text
text|placeholder
```

or dataset-style rows where the first field is a wav path and the second field is the text:

```text
wav/path.wav|text|speaker
```

The loader decides which field to use as text like this:

- if the first field contains `.wav`, it uses the second field
- otherwise it uses the first field

### OOD sampler behavior
- The code keeps sampling OOD strings until `len(sampled_text) >= min_length`.
- `min_length` is a string-length threshold, not a token count or frame count.
- If the text file only contains short strings, the sampler can retry for a long time.
- Keep the OOD file large enough that the threshold is reachable without extreme resampling.

## 24 kHz and root-path assumptions

- The shipped configs assume 24 kHz audio.
- The dataset loader joins `root_path` with the first column of each row.
- If the stored sample rate is not 24 kHz, the loader resamples to 24 kHz.
- Public data preparation should still store or convert the wavs to 24 kHz ahead of time so the pipeline stays predictable.
- For LJSpeech-style lists, the first column is usually just the wav name.
- For LibriTTS-style setups, the first column may already include a dataset-relative prefix when `root_path` is empty or minimal.

## Validation split handling

- `train_data` and `val_data` are separate list files.
- The repo does **not** auto-split data.
- Validation loading disables shuffling and `drop_last`.
- Validation also disables data augmentation.
- Keep the validation list aligned with the same speaker labels and path conventions used by the training list.

## Validation checklist

- Every training/validation row parses into 2 or 3 pipe-delimited fields.
- Every public training row includes an explicit speaker label.
- Speaker ids are stable across all utterances for the same speaker.
- First-column paths resolve correctly under `root_path`.
- Wavs are 24 kHz or intentionally resampled to 24 kHz.
- OOD text entries are long enough to satisfy `min_length`.
- Train and validation lists point at the intended split.
- No transcription contains stray `|` characters.
