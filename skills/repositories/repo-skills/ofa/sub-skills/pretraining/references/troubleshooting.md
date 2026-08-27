# Troubleshooting

## Common failure modes

### The pretraining script cannot find one of the TSVs

- Confirm that all four pretraining TSV families exist.
- Check the file path and the working directory.
- Validate the entire workspace with `scripts/validate_pretraining_inputs.py`.

### The negative-sample directory is incomplete

- Make sure `all_captions.txt`, `object.txt`, and `type2ans.json` are present.
- Confirm that `type2ans.json` contains the expected mapping shape.
- Do not start the GPU job until the directory passes validation.

### A TSV row looks fine but the task still crashes

- Re-check the selected columns for the specific pretraining role.
- Image rows should contain integer codes, not a raw caption.
- Detection rows should contain valid box annotations and image payloads.

### You are unsure whether to restore or start from scratch

- Prefer restore when a compatible checkpoint is available.
- Start from scratch only when the checkpoint is absent or intentionally excluded.
- Record that decision in the launch command or notes so it is not guessed later.

## Recovery order

1. Validate the pretraining workspace.
2. Confirm the restore vs scratch choice.
3. Render the command.
4. Launch only after both steps pass.
