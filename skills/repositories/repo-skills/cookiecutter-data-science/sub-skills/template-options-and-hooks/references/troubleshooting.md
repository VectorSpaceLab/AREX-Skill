# Template Options and Hooks Troubleshooting

## Invalid environment-manager/dependency-file combination

Symptoms:

- A generated Makefile command references a manager that does not match the dependency file.
- `make requirements` or `make create_environment` fails immediately with missing or nonsensical files.
- A noninteractive context bakes but later tests reject the combination.

Recovery:

1. Check the pair against `options-reference.md`.
2. Correct invalid pairs before generation. Examples: use `environment.yml` only with `conda`, `Pipfile` only with `pipenv`, `pixi.toml` only with `pixi`, and `pyproject.toml` for Poetry.
3. Regenerate rather than trying to patch many hook outputs by hand unless the project already contains valuable work.

## Generated files are unexpectedly missing

Likely option causes:

- `testing_framework=none` removes `tests/`.
- `docs=none` leaves only a docs placeholder, not MkDocs starter files.
- `linting_and_formatting=ruff` removes `setup.cfg`.
- `include_code_scaffold=No` removes scaffold modules and empties `__init__.py`.
- `open_source_license=No license file` removes `LICENSE`.

Recovery:

1. Identify selected options from Cookiecutter replay/context, project files, or `Makefile` content.
2. Read `hook-reference.md` and apply post-generation hook order.
3. If output still does not match, inspect whether a custom config overlay replaced or removed files.
4. Use the generated-project validator after the tree is produced.

## Dependency file looks wrong

Symptoms:

- `requirements.txt` lacks expected PyData, scaffold, docs, or test packages.
- `pyproject.toml` has Poetry or Pixi sections when not expected.
- Conda/Pixi files put packages under pip rather than Conda dependencies.

Likely causes:

- Option-dependent package additions were not selected.
- `awscli`, `python-dotenv`, and selected docs packages are treated as pip-only.
- Pixi and Poetry have special `pyproject.toml` handling.
- Hooks were disabled or failed before dependency writing.

Recovery:

1. Confirm option values and valid pairings.
2. Map selected options to package additions in `options-reference.md`.
3. Check `api-reference.md` for writer behavior by dependency file.
4. Re-run generation with hooks enabled if dependency files were produced from raw templates.

## Invalid Python version specifier

Symptom: generation fails with a `ValueError` about Python version format.

Cause: `python_version_number` must have two or three dot-separated components.

Recovery:

- Use `3.11` for a compatible release specifier (`~=3.11.0`).
- Use `3.11.7` for an exact patch specifier (`==3.11.7`).
- Do not use bare `3`, ranges, or text like `latest`.

## Nested cloud-storage context is malformed

Symptoms:

- Cloud sync Makefile rules are missing or use placeholder values.
- `dataset_storage` appears as a string when hook logic expects a nested mapping.

Recovery:

1. For interactive prompts, select the cloud provider and then answer subfields.
2. For noninteractive generation, provide the nested structure expected by CCDS, for example `{"s3": {"bucket": "my-bucket", "aws_profile": "default"}}`.
3. Prefer a JSON context file or the bundled bake helper rather than hand-quoting nested dictionaries in a shell.
4. Validate generated Makefile rules before running any cloud command.

## Optional external CLI missing

Symptoms:

- `make create_environment` cannot find `conda`, `pipenv`, `uv`, `pixi`, `poetry`, or `mkvirtualenv`.
- Cloud sync rules cannot find `aws`, `az`, or `gsutil`.

Cause: CCDS generates commands for selected tools but does not install those external manager/cloud CLIs for the generated project.

Recovery:

- Install or configure the selected external tool intentionally, or regenerate with a tool that exists in the target environment.
- For generated projects, use manager-specific `run` commands (`pixi run`, `poetry run`, `pipenv run`) when not in the environment shell.
- Do not run cloud sync until credentials and destination are confirmed.

## Custom config overlay changed generated output

Symptoms:

- Critical files such as `Makefile`, `pyproject.toml`, `.gitignore`, package modules, or docs differ from normal CCDS output.
- Secrets or large local files appear in the project.

Cause: `write_custom_config` copied a local directory, zip, URL zip, or VCS checkout into the generated project.

Recovery:

1. Inspect overlay contents before using them.
2. Generate into a temporary parent directory and compare output.
3. Remove secrets, `.env`, local data, environments, caches, and unintended critical-file replacements from the overlay.
4. Regenerate and validate.

## Raw Jinja delimiters remain in generated files

Symptoms: files contain `{{`, `}}`, `{%`, or `%}` after generation.

Likely causes:

- Generation stopped before hooks completed.
- Plain Cookiecutter used the wrong context file.
- An overlay copied raw templates into the project after rendering.
- A malformed context prevented rendering.

Recovery:

1. Re-run with `ccds`, not plain `cookiecutter`, for v2.
2. Use `--keep-project-on-failure` only to inspect failure state.
3. Check custom overlays for raw templates.
4. Run the generated-project validator to list files with leftover Jinja delimiters.

## Starter tests fail immediately

This is expected when `testing_framework=pytest` or `unittest` because the starter test intentionally asserts failure until the project writes a real test.

Recovery:

- Replace the starter assertion with a meaningful project test.
- Do not treat a freshly generated starter test failure as proof that CCDS generation failed.
