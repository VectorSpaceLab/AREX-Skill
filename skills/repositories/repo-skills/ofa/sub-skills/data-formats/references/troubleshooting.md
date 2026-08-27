# Troubleshooting

## Common failure modes

### `FileDataset` or a downstream loader says the row shape is wrong

- Check the selected columns first.
- Make sure the separator is tab.
- Validate the file with `scripts/validate_ofa_tsv.py` before trying again.

### A base64 image cell decodes incorrectly

- Re-encode the source image with `scripts/encode_image_base64.py`.
- Confirm that the payload is URL-safe base64, not a raw file path.
- If the image is part of a TSV family with multiple image columns, verify the column index, not just the payload.

### An integer-code or box field contains text that looks valid to a human

- Double-check that code tokens are integers separated by spaces.
- For RefCOCO, keep the coordinate order consistent with the task's box interpretation.
- For image generation, validate the code length before you launch the GPU job.

### A path field exists in the TSV but the job still fails

- The path may be relative to the wrong working directory.
- For speech workflows, the audio file and fbank config both need to match the same sample rate and feature layout.

### A result JSON file breaks a metric helper

- Re-run the task's output through the bundled JSON validator or the task-specific metric helper.
- Make sure the file contains a list of prediction objects, not a single object or a nested dict.

## Best recovery loop

1. Validate the file with the bundled helper.
2. Fix the selected columns or payload format.
3. Re-run the same validator.
4. Only then hand the file to the workflow sub-skill.
