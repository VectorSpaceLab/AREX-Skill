# Document Parsing Troubleshooting

## Missing document-parsing extras

### Symptom
- The parser imports, but `PPStructureV3`, `PaddleOCRVL`, or `doc2md` fails at runtime.
- The error mentions an optional dependency or backend.

### Likely causes
- `paddleocr[doc-parser]` is not installed.
- `paddleocr[doc2md]` is missing for office conversion.
- The selected pipeline needs a backend that is not available in the current environment.

### Recovery
- Install only the extra needed by the chosen workflow.
- Re-run the bundled smoke helper and the sub-skill script before trying a large document again.

## Pipeline version or backend mismatch

### Symptom
- `PaddleOCRVL` rejects the requested pipeline version or backend.
- The result quality is poor because the full pipeline was not used.

### Likely causes
- An unsupported `pipeline_version` or VLM backend was selected.
- The user is running only a VLM component when the full layout-analysis pipeline is required.

### Recovery
- Use the exact version values documented in the workflow reference.
- Confirm whether the task needs full document parsing, page restructuring, or only a VLM helper.
- Prefer the full pipeline when the user wants a complete document result.

## Layout and parameter validation errors

### Symptom
- The pipeline rejects threshold, merge, or toggle parameters.
- A helper such as `PaddleOCRVLOptions` raises a validation error.

### Likely causes
- Numeric values are out of range.
- An option is valid for one pipeline but not another.

### Recovery
- Check the public option dataclass or wrapper signature before retrying.
- Keep the parameter set aligned with the selected workflow family.

## doc2md conversion failures

### Symptom
- `doc2md` says the format is unsupported.
- The converter cannot import `python-docx`, `python-pptx`, `openpyxl`, or `pylatexenc`.

### Likely causes
- The source file is not one of the supported office formats.
- The `doc2md` extra is missing.

### Recovery
- Confirm the input extension first.
- Install the office-conversion extra and rerun the helper script.
- Use `--formats` to confirm the installed converter set.

## Output handling problems

### Symptom
- Markdown or exported files are missing.
- Expected resource files are not saved alongside the result.

### Likely causes
- The destination path is not writable.
- The workflow expects its own save helper rather than manual path reconstruction.

### Recovery
- Use the workflow's save methods or the bundled conversion script.
- Confirm the output directory exists and is writable.
