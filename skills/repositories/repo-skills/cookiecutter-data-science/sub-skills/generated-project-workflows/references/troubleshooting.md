# Generated Project Troubleshooting

## First diagnostic steps

1. Run `make` or inspect `Makefile` to list available rules.
2. Identify selected options from files: dependency file, `setup.cfg` vs Ruff config, docs starter files, tests directory, scaffold modules, and cloud sync rules.
3. Run the bundled read-only validator before mutating the project:

   ```bash
   python scripts/validate_generated_project.py /path/to/project --module-name <module_name>
   ```

4. Install dependencies only after confirming the intended environment manager and dependency file.

## `make create_environment` fails

Likely causes:

- The selected manager CLI is missing (`conda`, `pipenv`, `uv`, `pixi`, `poetry`, `mkvirtualenv`).
- The generated dependency file is not valid for the selected manager.
- The requested Python version is unavailable to that manager.
- A same-named environment already exists.

Recovery:

- Check valid pairings in `environment-managers.md`.
- Install/configure the selected manager or regenerate with an available manager.
- For Conda and Pipenv, remove or rename conflicting environments only with user approval.
- For `environment_manager=none`, create an environment manually and run dependency installation according to the chosen dependency file.

## `make requirements` fails

Likely causes:

- Dependencies were installed outside the intended environment.
- The manager-specific command was run without the manager CLI installed.
- Network/package resolution failed.
- Pixi/Poetry project setup needs `pixi install` or `poetry install`, not a raw pip command.
- Cloud/docs/scaffold/test package choices added packages that are unavailable in the target platform.

Recovery:

1. Verify the active Python or manager runner: `which python`, `python --version`, `pixi run python --version`, `poetry run python --version`, or `pipenv run python --version`.
2. Use the manager-specific command from `environment-managers.md`.
3. Retry transient network failures after confirming package names.
4. If a dependency choice is wrong, regenerate or edit the dependency file intentionally and document the deviation.

## Generated package imports fail

Symptoms:

- `python -c "import <module_name>"` fails.
- `from <module_name> import config` fails in notebooks or scaffold scripts.
- Typer/loguru/tqdm imports fail in scaffold modules.

Likely causes:

- Dependencies were not installed.
- The project was not installed editable.
- The import name differs from the repo folder name.
- Scaffold dependencies are missing because `include_code_scaffold=Yes` was expected but not selected or dependency installation failed.

Recovery:

1. Confirm the module directory name.
2. Run the selected `make requirements` path in the intended environment.
3. Use manager wrappers when needed: `pipenv run`, `pixi run`, `poetry run`, or activated `.venv`.
4. If scaffold was disabled, only `__init__.py` is expected; add modules deliberately.

## Starter tests fail

Generated pytest and unittest starters intentionally fail:

- pytest starter: `assert False`.
- unittest starter: `self.assertTrue(False)`.

Recovery:

- Replace the starter test with a real assertion before using `make test` as a health signal.
- If the failure is not the starter assertion, inspect imports and dependencies first.

## Linting or formatting fails

Likely causes:

- Dependencies such as Ruff, Black, flake8, or isort are not installed in the active environment.
- The wrong linting mode is assumed.
- The starter or edited code violates generated tool configuration.

Recovery:

1. Identify selected linting mode: Ruff has `[tool.ruff]` in `pyproject.toml` and no `setup.cfg`; flake8+black+isort keeps `setup.cfg`.
2. Install dependencies.
3. Run `make lint` to check and `make format` only when source rewriting is intended.
4. With Pixi or Poetry, use `pixi run make lint` or `poetry run make lint` when not in the shell.

## Cloud sync fails or would be unsafe

Symptoms:

- `aws`, `az`, or `gsutil` command not found.
- Credentials, bucket/container, profile, or account errors.
- Command would upload/download too much data.

Recovery:

- Do not run sync rules as a generic validation step.
- Confirm the selected provider, bucket/container, profile/account, and transfer direction.
- Authenticate with the provider CLI outside the project if needed.
- Dry-run or list remote paths when the provider supports it before large transfers.
- Keep raw data immutable; do not sync processed outputs over raw data locations accidentally.

## Leftover Jinja delimiters in files

Symptoms: generated project files contain `{{`, `}}`, `{%`, or `%}`.

Likely causes:

- Generation failed before completion.
- Hooks were disabled.
- A custom overlay copied raw templates.
- The project is not a generated project but the raw CCDS template tree.

Recovery:

1. Re-generate with hooks enabled in a disposable parent.
2. Check overlays for raw templates.
3. Run `validate_generated_project.py` to list affected files.
4. Do not commit or build from a tree with unresolved Jinja placeholders.

## Docs build fails

Likely causes:

- `docs=none` but the user expects MkDocs files.
- MkDocs dependency was not installed.
- The docs command is run from the wrong directory.
- Project-specific docs edits broke MkDocs config.

Recovery:

- Confirm `docs/mkdocs.yml` exists.
- Install dependencies.
- Run docs build from the right directory or add a project Makefile rule if needed.
- If docs were disabled at generation time, add docs deliberately rather than assuming starter files exist.

## Data workflow confusion

Common mistakes:

- Editing `data/raw` manually or overwriting raw files with processed outputs.
- Keeping large data in git by default.
- Running placeholder `dataset.py` and expecting real data products.
- Leaving reusable notebook code out of the package module.

Recovery:

- Treat analysis as a DAG from raw/external to interim to processed to reports/models.
- Replace scaffold placeholder logic with explicit project-specific code.
- Add tests or validation for reusable transformations.
- Store secrets in `.env` and keep `.env` out of version control.
