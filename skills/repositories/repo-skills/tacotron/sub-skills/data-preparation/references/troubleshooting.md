# Data-preparation troubleshooting

- **`metadata.csv` not found:** the base directory is wrong or the archive has
  an extra nesting level. Check the exact `LJSpeech-1.1` name.
- **WAV not found:** the first metadata field must match a file in `wavs/`.
  Do not infer a path from the human-readable text field.
- **Empty or malformed `train.txt`:** rerun the validator and inspect the
  number of pipe-separated fields. A zero-row output often means every Blizzard
  row failed confidence/label filters.
- **Array shape mismatch:** saved arrays must be time-major and have the
  configured 80/1025 feature dimensions. Compare both arrays' frame counts.
- **Audio decoder failure:** verify WAV encoding and readable permissions; test
  a single utterance before launching a multi-process conversion.
- **Too-long utterance errors in training:** compare the maximum frame count to
  `max_iters * outputs_per_step`; segment/filter examples or increase max_iters
  consistently for training and evaluation.
