# Repository maintenance troubleshooting

## Consistency test fails after adding a recipe

- Check the corresponding `tests/recipes/<Dataset>.csv` row.
- Confirm every listed path exists relative to repository root.
- Add debug flags and expected file checks.
- Check README result/HF links exactly match CSV values.

## Doctest or docs build fails

- Run the smallest failing module/page first.
- Check imports, sample paths, and optional dependency guards.
- Avoid executing network/model-download examples as ordinary doctests; mark them skipped or provide local fixtures when editing tests.
- Verify RST toctree paths and notebook names after renames.

## CI import failures

- Compare Torch/Torchaudio versions and Python version with CI's pinned CPU install.
- Run `python -m pip check` and a minimal import script.
- Separate missing optional integrations from base package import failures.

## Lint/pre-commit failures

- Run the project-configured formatter/linter on changed files first.
- Respect the configured 80-character line length and import grouping.
- Do not make broad formatting changes unrelated to the task.

## Recipe/HF/URL check failures

- Recipe tests may need CUDA, sample data, or recipe extras.
- Hugging Face checks may need network access and model caches.
- URL checks may fail transiently; retry only after confirming the failure is external and record it separately.
- Do not mark a source change complete based only on a skipped network check.

## Generated artifacts or stale tables

- Identify whether a file is source-owned or generated before editing.
- Use the repository's generator/helper when one exists.
- Keep generated output changes separate from runtime code changes for review clarity.
