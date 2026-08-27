# Cross-Cutting Troubleshooting

## Package install or import failures

Symptoms:

- `import ccds` fails.
- `ccds --help` fails.
- `python -m pip show cookiecutter-data-science` cannot find the package.

Recovery:

1. Confirm the intended Python or CLI environment.
2. Install the package publicly with `pipx install cookiecutter-data-science` for CLI use, or `python -m pip install cookiecutter-data-science` inside the selected environment.
3. Run:

   ```bash
   python -c "import ccds; print(ccds.__version__)"
   ccds --help
   ```

4. If the CLI is missing but import works, check that the environment's scripts directory is on `PATH` or run through the environment manager.
5. Use `scripts/check_ccds_environment.py` for a safe import/CLI diagnostic.

## Wrong workflow route

- Use `sub-skills/project-generation-cli/` when the user is running `ccds` or choosing CLI flags.
- Use `sub-skills/template-options-and-hooks/` when the user asks what an option means, why a file is generated/removed, or how hooks/dependency writers behave.
- Use `sub-skills/generated-project-workflows/` when the project already exists and the user asks about its layout, Makefile, dependencies, scaffold code, docs, tests, or data workflow.

## Version and staleness issues

Symptoms:

- The user is on a CCDS release newer or older than v2.3.0.
- Options such as Pixi or Poetry are missing or behave differently.
- The template branch or tag differs from the installed package default.

Recovery:

1. Check the installed package version and generated project context.
2. Read `references/repo-provenance.md` to compare the source snapshot.
3. Use `ccds -c <branch-or-tag>` only when the task requires a specific template version.
4. If package APIs, options, hooks, or template files changed, refresh this skill before making exact claims.

## CLI, prompt, or replay confusion

Symptoms:

- Defaults differ from what the user expected.
- Old answers are reused.
- `cookiecutter` rather than `ccds` produces a different template.

Recovery:

- Prefer `ccds` for v2.
- Avoid `--replay` when fresh answers are needed.
- Use `--default-config` if user-level Cookiecutter config may interfere.
- Use `--no-input` only with complete context.
- For nested values, prefer a JSON context and the bundled bake helper.

## Generated-project validation failures

Symptoms:

- Missing expected files or directories.
- Leftover Jinja delimiters.
- Makefile rules do not match options.

Recovery:

1. Read the generated-project troubleshooting reference.
2. Run the bundled validator from `sub-skills/generated-project-workflows/scripts/validate_generated_project.py`.
3. Check whether hooks were disabled, generation failed, invalid option pairs were used, or a custom config overlay replaced files.
4. Regenerate in a disposable parent when the tree still contains raw templates or partial output.

## External tool and credential failures

The CCDS package can generate projects that reference external tools. It does not install or authenticate those tools for the generated project.

Common missing tools:

- environment managers: `conda`, `mkvirtualenv`, `pipenv`, `uv`, `pixi`, `poetry`;
- cloud CLIs: `aws`, `az`, `gsutil`;
- docs/lint/test packages before dependency installation.

Recovery:

- Install/configure tools only when the user chooses that workflow.
- Use manager-specific `run` commands when not in the environment shell.
- Do not run cloud sync until credentials, destination, direction, and transfer size are confirmed.

## Raw data, secrets, and project hygiene

Generated CCDS projects are opinionated:

- Do not edit `data/raw` in place.
- Do not commit `.env`, credentials, local environments, or large data by default.
- Move reusable notebook code into the package module.
- Treat starter tests and scaffold scripts as placeholders until replaced.

If a task violates these assumptions, explicitly call out the project-specific reason and document the deviation.
