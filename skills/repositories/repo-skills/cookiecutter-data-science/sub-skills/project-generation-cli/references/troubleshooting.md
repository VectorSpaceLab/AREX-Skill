# Project Generation Troubleshooting

## `ccds: command not found`

Likely causes:

- `cookiecutter-data-science` is not installed in the active tool environment.
- It was installed with `pip` into a different Python.
- `pipx` installed it but the pipx bin directory is not on `PATH`.

Recovery:

1. Run `python -m pip show cookiecutter-data-science` in the environment you expect to use.
2. Prefer `pipx install cookiecutter-data-science` for a user-level CLI install.
3. If using an existing Python environment, install with `python -m pip install cookiecutter-data-science` and re-check `ccds --help`.
4. Run the root environment checker if available: `python scripts/check_ccds_environment.py`.

## Plain `cookiecutter` produced the wrong behavior

Symptom: the template uses old prompts, `ccds.json` is ignored, nested cloud-storage prompts do not work, or v2 hooks do not behave as expected.

Likely cause: plain Cookiecutter was used for a CCDS v2 workflow.

Recovery:

- Use `ccds` for v2.
- Use plain `cookiecutter ... -c v1` only when the user explicitly wants the deprecated v1 template.

## Generated project used the wrong template version

Symptom: new options such as `pixi` or `poetry` are missing, or generated files reflect a different release.

Likely causes:

- The installed `cookiecutter-data-science` package defaults `--checkout` to its own version tag.
- A cached/replayed Cookiecutter run or explicit `-c` selected another branch/tag.

Recovery:

1. Check `ccds --version` and package metadata if the installed package version matters.
2. Pin explicitly when required: `ccds -c master`, `ccds -c v2.3.0`, or `ccds -c <commit>`.
3. Avoid `--replay` for fresh option decisions.
4. Use `--default-config` when user-level Cookiecutter config may be affecting behavior.

## Output directory already exists

Symptom: Cookiecutter refuses to generate because the target project directory exists.

Recovery:

- Confirm `--output-dir` points to the parent directory, not the project directory.
- Choose a new `repo_name` or empty parent directory.
- Use `--overwrite-if-exists` only with explicit approval to replace that exact generated project.
- Use `--skip-if-file-exists` only when merging into an existing tree is intentional and the result will be validated carefully.

## Hooks disabled or rejected

Symptom: generated project keeps raw template directories, dependency files are missing or malformed, tests/docs folders are not pruned, `setup.cfg` remains with Ruff, `LICENSE` remains despite “No license file,” or Python version metadata is wrong.

Likely cause: `--accept-hooks no` or hook execution failed.

Recovery:

- Re-run with hooks accepted for normal project generation.
- Use `--keep-project-on-failure` only for debugging a failed hook.
- Read `../template-options-and-hooks/references/hook-reference.md` to predict hook outputs.

## `--no-input` or extra context failed

Symptoms:

- A value remains at its default unexpectedly.
- Nested `dataset_storage` is not shaped correctly.
- An environment-manager/dependency-file pair later fails.

Recovery:

1. Confirm every extra-context item is `KEY=VALUE` and quote shell values with spaces.
2. For nested options, prefer JSON context through the bundled bake helper.
3. Validate option names and choices in `../template-options-and-hooks/references/options-reference.md`.
4. Check valid environment-manager/dependency-file pairings before generation.

## Checkout, network, or template download failure

Symptoms:

- Git clone/download errors.
- Branch/tag not found.
- Cookiecutter cannot locate the template.

Recovery:

- Verify the branch, tag, or commit passed to `-c/--checkout`.
- Retry transient network failures later or use a reachable mirror/template path if the user provides one.
- If generating from a local template path, confirm it contains CCDS v2 template files and hooks.
- Use `--keep-project-on-failure` only to inspect partial output; do not treat a partial project as valid.

## Custom config overlay surprises

Symptoms:

- Generated files are overwritten by unexpected content.
- Secrets or large local data appear in the generated project.
- Option-dependent files disappear after generation.

Likely cause: the `custom_config` overlay copies a directory, zip, URL zip, or VCS checkout into the generated project after core dependency/version generation.

Recovery:

1. Inspect overlay contents before generation.
2. Generate into a disposable parent and compare the tree.
3. Avoid overlays that contain `.env`, credentials, local data, environments, or files that collide with critical generated files unless that override is intentional.
4. Validate the result with the generated-project validator.

## v1/v2 confusion

Symptoms:

- User expects the old `src/` layout or Sphinx/tox files but sees v2 package-module layout.
- User expects v2 options but used `cookiecutter ... -c v1`.

Recovery:

- For v2, use `ccds` and the option references in this generated skill.
- For v1, explicitly pin `-c v1` and rely on v1-specific guidance; do not apply v2 hook or option assumptions.
