# Local OCR Troubleshooting

## `No models are available` or unsupported language/version

### Symptom
- `ValueError: No models are available`
- `ValueError` about an unsupported OCR version or language

### Likely causes
- The selected `lang` and `ocr_version` combination is not supported by the wrapper.
- The request asks for a language family that the selected version does not cover.

### Recovery
- Start with the OCR-workflow reference and use the documented fallback families.
- If the task is language-sensitive, choose the closest supported family instead of forcing a mismatched model name.

## Predictor creation fails with a dependency error

### Symptom
- `RuntimeError` during predictor creation mentioning a dependency issue

### Likely causes
- The local environment lacks the backend or optional engine that the chosen model requires.
- The selected engine is not available for the model or device combination.

### Recovery
- Revisit the installation-and-backends reference.
- Use the bundled env inspection helper before retrying a heavier native run.
- Keep CPU-only checks separate from accelerator claims.

## Engine or precision flag problems

### Symptom
- `Invalid engine` or `Invalid precision`
- A CLI invocation accepts the arguments but the model does not accelerate as expected

### Likely causes
- The engine name is not in the supported engine list.
- The requested acceleration path is not supported by the installed backend.

### Recovery
- Use the exact engine names from the model-and-engine reference.
- If the goal is just correctness, prefer the default Paddle engine first.
- Treat acceleration as optional unless the task explicitly requires it.

## Output or save failures

### Symptom
- The model predicts successfully, but `save_to_img()` or `save_to_json()` is missing files or writing unexpected names.

### Likely causes
- The output directory is not writable.
- The user is manually reconstructing output filenames rather than using the result helpers.

### Recovery
- Use the result object's own save helpers.
- Confirm the destination directory exists and is writable before rerunning.

## CLI confusion

### Symptom
- The user sees the wrong subcommand or an `argparse` usage error.

### Likely causes
- The CLI subcommand name differs from the model class name.
- The task is actually a document parser or hosted API request.

### Recovery
- Match the exact CLI subcommand from the model reference.
- If the task needs a full document pipeline, route to the document-parsing sub-skill instead.
