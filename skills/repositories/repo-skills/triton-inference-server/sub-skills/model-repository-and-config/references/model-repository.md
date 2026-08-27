# Model Repository Layout

## Minimal layout

```text
<model-repository>/
  <model-name>/
    [config.pbtxt]
    [configs/]
    <version>/
      <model-definition-file>
```

Important rules:

- Triton sees one or more model repositories via `--model-repository`.
- Each model must have at least one positive numeric version directory, such as `1/`.
- `config.pbtxt` is optional only when Triton can auto-complete the minimal configuration for that backend/model type.
- Custom configs can live under `<model-name>/configs/` and are selected by `--model-config-name`.
- Output label files and backend-specific model files belong in the model directory, not at repository root.
- Remote repositories use `gs://`, `s3://`, or `as://` prefixes, but the generated skill should still prefer local preflight and explicit user approval before network access.

## Validation checklist

- Model directory name matches `config.pbtxt` `name` when `name` is set.
- Version directories are numeric and present.
- Backend-specific files exist in each version directory.
- Configs and label files are staged atomically if a live server is polling the repository.

## Fixture guidance

When validating only the repository structure, copy a small model directory tree into a temporary test fixture rather than mutating the user's repository. The bundled validator checks for missing version directories, missing `config.pbtxt` pieces, and simple layout errors without starting Triton.
