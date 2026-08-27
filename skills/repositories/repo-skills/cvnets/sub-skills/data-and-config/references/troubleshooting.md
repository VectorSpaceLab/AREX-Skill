# Data and Config Troubleshooting

## Purpose

Read this when config loading, dataset roots, sampler selection, tokenizer setup, or modality-specific input layout fails.

## Bad YAML key or override spelling

### Symptom
- Unrecognized YAML key warnings.
- A config file parses, but the expected option never changes.

### Cause
- The key spelling does not match the parser's dotted option name.

### Recovery
- Use `../../../scripts/inspect_config.py` to print the resolved values.
- Compare the spelling against `references/data-formats.md` and `../../../references/configuration.md`.
- Remember that CLI flags use hyphenated names while `opts` keys are dotted.

## Missing dataset roots

### Symptom
- The loader cannot find the training or validation set.
- A recipe fails before any batches are produced.

### Cause
- `dataset.root_train`, `dataset.root_val`, or `dataset.root_test` still points at a placeholder path.

### Recovery
- Fix the root path in the config or use a targeted override.
- Re-run the config inspection script before retrying the full workflow.

## CLIP tokenization failures

### Symptom
- CLIP or zero-shot image-text loading fails before the model builds.

### Cause
- The tokenizer configuration is missing the BPE merge file, encoder JSON file, or the required text-tokenizer package.

### Recovery
- Confirm `text_tokenizer.clip.merges_path` and `text_tokenizer.clip.encoder_json_path`.
- Install the text-tokenizer dependency if it is missing.
- Recheck the image-text dataset format if the prompt lists are malformed.

## Audio and ByteFormer failures

### Symptom
- Audio loading, byte saving, or byte collate functions fail.
- The batch shape changes unexpectedly after augmentation.

### Cause
- The audio backend, byte-saving settings, or padding index does not match the recipe.

### Recovery
- Verify the audio-augmentation and byte-saving keys in the config.
- Make sure the collate function selected in the config matches the modality.
- If the workflow uses torchaudio or MP3/WAV support, confirm the optional dependency is present.

## Video-reader failures

### Symptom
- A video test or recipe fails when reading clips.
- Decord-specific paths fail while PyAV paths work.

### Cause
- The video backend is missing or the frame-stack format does not match the expected tensor layout.

### Recovery
- Check whether the workflow expects PyAV or decord.
- Confirm the `video_reader.frame_stack_format` setting.
- Treat decord as optional; if it is absent, use the PyAV path instead.

## When to stop and switch

- If the dataset layout is correct but the model name is wrong, switch to `models-and-architectures`.
- If the dataset layout is correct but the run fails during training, switch to `training-and-evaluation`.
- If the dataset layout is correct but the export path fails, switch to `conversion-and-profiling`.
