# Troubleshooting

## Purpose

Read this when dataset preparation or config loading fails.

## `addict` or `pathspec` missing

### Symptoms
- `ModuleNotFoundError: No module named 'addict'`
- `ModuleNotFoundError: No module named 'pathspec'`

### Cause
- The runtime stack is incomplete or the repo requirements were not installed.

### Recovery
- Install the missing runtime dependencies.
- Re-run the root smoke helper or the data-layout validator.

## Wrong dataset root

### Symptoms
- `FileNotFoundError` for `train_gt.txt`, `test.txt`, `list/train_gt.txt`, or `list/test_split/...`
- TuSimple conversion runs but does not create the expected files.

### Cause
- `data_root` points at the wrong directory level.
- The dataset was unpacked without the expected folder names.

### Recovery
- Compare the root against `references/data-formats.md`.
- Run `scripts/validate_dataset_layout.py` before any training or evaluation command.

## TuSimple conversion issues

### Symptoms
- Conversion creates no PNG masks.
- The training list is empty or has malformed lane flags.
- The source JSON files are present but the output list files are missing.

### Cause
- The TuSimple JSON files were renamed or moved.
- The converter was pointed at a partial root.
- The user expected the converter to find extra files automatically.

### Recovery
- Provide the dataset root explicitly.
- Confirm the default TuSimple JSON filenames from the install instructions.
- Re-run the bundled converter and inspect its generated file paths.

## CULane path quirks

### Symptoms
- A test list entry looks like it starts with `/` and the loader fails to join it correctly.
- Evaluation cannot find the split lists.

### Cause
- The list files contain the common CULane leading-slash path quirk.

### Recovery
- Use the bundled validator to check the list files.
- Let the loader's existing slash-stripping behavior handle the list files rather than editing them by hand.

## Config override mistakes

### Symptoms
- `use_aux` behaves unexpectedly.
- `griding_num`, `num_lanes`, or `backbone` seem inconsistent with the dataset.

### Cause
- The command-line override changed a field that should stay aligned with the dataset family.
- The user mixed CULane and TuSimple defaults.

### Recovery
- Read `references/configuration.md` and keep the dataset family consistent.
- If the user wants a custom override, state the changed fields explicitly.

## When to stop

Stop and hand the task back to training or evaluation when the remaining issue is not data layout or config parsing.
