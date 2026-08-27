# Troubleshooting

## Invalid list rows

**Symptom**
- Loader errors while parsing a list file.
- `too many values to unpack` or empty / broken batches.

**Likely cause**
- A row has the wrong number of `|` fields.
- A transcription accidentally contains `|`.
- The speaker column is missing or not integer-like.

**Fix**
- Use `filename.wav|IPA transcription|speaker`.
- Keep speaker ids explicit, even for single-speaker data.
- Avoid extra pipe characters in the transcription.
- Re-run the bundled validator before training.

## Missing audio root

**Symptom**
- `FileNotFoundError` when the loader tries to open a wav.

**Likely cause**
- `data_params.root_path` does not match the layout encoded in the list file.
- The list uses a dataset-relative prefix that the config does not expect.

**Fix**
- Either set `root_path` to the wav directory or update the first column so it resolves correctly under the chosen root.
- If the config leaves `root_path` empty, make sure the first column already has the correct prefix.
- Use `--check-files` in the validator to catch this early.

## Too-short OOD text or retry loops

**Symptom**
- OOD sampling appears to hang or spend a long time retrying.

**Likely cause**
- `data_params.min_length` is higher than the available OOD text lengths.
- The OOD file is too small or too repetitive.

**Fix**
- Lower `min_length`.
- Add longer OOD texts.
- Remember that the loader checks character length, not token count.

## Missing dependencies

**Symptom**
- `ImportError` for `pandas` or TensorBoard utilities.
- Demo notebooks fail around phonemization.

**Likely cause**
- `requirements.txt` omits `pandas` and `tensorboard` even though the code imports them.
- Demo workflows also need `phonemizer` plus an `espeak-ng` backend.

**Fix**
- Install the missing runtime dependencies in the inspection or run environment.
- Use `phonemizer` and `espeak-ng` only for the demo / inference path.

## Bad checkpoint paths

**Symptom**
- Stage-2 or fine-tune startup fails while loading weights.
- The run starts from the wrong checkpoint family.

**Likely cause**
- `pretrained_model` points at the wrong file.
- `second_stage_load_pretrained` is false when a direct pretrained checkpoint was intended.
- `first_stage_path` does not exist under `log_dir`.

**Fix**
- Decide whether the run should load `pretrained_model` directly or fall back to `first_stage_path`.
- Keep `load_only_params=true` for transfer or fine-tune, unless you truly want optimizer state restored.
- Inspect the config with the bundled YAML inspector before launching.

## Non-English PL-BERT note

**Symptom**
- The run loads, but non-English quality is poor or the language setup feels wrong.

**Likely cause**
- The bundled PL-BERT is English-pretrained.

**Fix**
- Swap in a language-appropriate PL-BERT or a multilingual PL-BERT before training on non-English data.
- Treat this as a configuration / asset issue, not a list-format issue.
