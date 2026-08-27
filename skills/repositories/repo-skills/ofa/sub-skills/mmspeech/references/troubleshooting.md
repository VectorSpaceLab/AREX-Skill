# Troubleshooting

## Common failure modes

### The manifest validator says the audio path is missing

- Check that the audio column really points at a file path, not an ID.
- Confirm the path is relative to the current working directory you plan to use.
- Do not launch the GPU job until every row resolves to a real file.

### The fbank config sample rate does not match the manifest or data

- Make sure the YAML sample rate matches the workflow's expected rate.
- Re-check the audio preprocessing path if the workflow uses a different sample rate.
- If the helper says `missing optional dependency: PyYAML`, install PyYAML before rerunning the manifest check.
- Fix the config before training; sample-rate mismatches are expensive to debug later.

### The speech run fails because a phone dictionary is missing

- Confirm `phone_dict_path` and any `text2phone_path` overrides.
- Make sure the repo is reading the correct dictionary for the current stage.

### WER looks wrong even though decoding finished

- Check text normalization, prompt choice, and stage selection.
- Confirm that the manifest matches the evaluation split you intended.

## Recovery order

1. Validate the manifest.
2. Confirm the fbank config and audio paths.
3. Render the command.
4. Only then launch the speech workflow.
