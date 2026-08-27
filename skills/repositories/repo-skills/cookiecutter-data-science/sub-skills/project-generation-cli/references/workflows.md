# Project Generation Workflows

## Purpose

Use these recipes to generate CCDS projects safely and route the result to the right post-generation checks.

## Workflow: interactive released-template project

1. Install CCDS if needed:

   ```bash
   pipx install cookiecutter-data-science
   ```

2. Move to the parent directory where the project folder should be created.
3. Run:

   ```bash
   ccds
   ```

4. Answer prompts. If unsure, keep defaults for an ordinary starter project.
5. After generation, inspect the project folder and route to `../generated-project-workflows/` before running `make create_environment`, `make requirements`, cloud sync, lint, or tests.

## Workflow: generate in a chosen parent directory

```bash
ccds -o ./projects
```

`./projects` is the parent. The generated project folder name comes from `repo_name`. If `projects/<repo_name>` already exists, Cookiecutter fails unless `--overwrite-if-exists` or `--skip-if-file-exists` is used.

Use `--overwrite-if-exists` only when overwriting that exact generated project is intended. Prefer a temporary or empty parent for experiments.

## Workflow: pin a branch, tag, or commit

Use the installed default checkout for stable released behavior. Pin only when required:

```bash
ccds -c master
ccds -c v2.3.0
ccds -c <commit-sha>
```

Choose `master` for unreleased template changes, a tag for a known release, or a commit for exact reproducibility. If a user says “use v1,” route to the v1 command in the CLI reference and expect a different layout.

## Workflow: noninteractive generation with simple context

Use `--no-input` when a script or agent has a complete set of decisions. Omitted list-choice values default to their first option.

```bash
ccds --no-input \
  project_name="Demo Analysis" \
  repo_name="demo_analysis" \
  module_name="demo_analysis" \
  author_name="Data Team" \
  description="Demo project" \
  python_version_number="3.11"
```

For nested choices such as cloud storage, use a JSON context and the bundled helper below to avoid shell quoting mistakes.

## Workflow: noninteractive bake through bundled helper

The bundled helper calls the installed CCDS package through Cookiecutter's Python API and writes to a temporary parent by default:

```bash
python scripts/bake_ccds_project.py \
  --extra-context project_name="Demo Analysis" \
  --extra-context repo_name="demo_analysis" \
  --extra-context module_name="demo_analysis" \
  --extra-context author_name="Data Team" \
  --extra-context description="Demo project"
```

For JSON context:

```json
{
  "project_name": "Demo Analysis",
  "repo_name": "demo_analysis",
  "module_name": "demo_analysis",
  "author_name": "Data Team",
  "description": "Demo project",
  "python_version_number": "3.11",
  "environment_manager": "uv",
  "dependency_file": "pyproject.toml",
  "testing_framework": "pytest",
  "linting_and_formatting": "ruff",
  "docs": "mkdocs",
  "include_code_scaffold": "Yes"
}
```

Run:

```bash
python scripts/bake_ccds_project.py --config-json context.json --output-dir ./scratch --overwrite
```

The helper prints the generated project path. It does not validate every option combination; for that, read `../template-options-and-hooks/` before baking or run the post-generation validator from `../generated-project-workflows/` afterward.

## Workflow: custom config overlay

CCDS supports a custom configuration overlay consumed by post-generation hooks. Treat overlays as powerful and potentially destructive because they copy files into the generated project and can replace generated content.

Safe procedure:

1. Generate into a disposable parent directory first.
2. Review the overlay source: local directory, zip, URL zip, or VCS repository.
3. Confirm the overlay does not contain secrets, large data, or files that unintentionally replace generated `pyproject.toml`, `Makefile`, `.gitignore`, or package modules.
4. Bake with hooks enabled.
5. Validate the generated result before using it as a project baseline.

## Workflow: validate the generated project

After generation, use the generated-project workflow sub-skill. A common route is:

```bash
python sub-skills/generated-project-workflows/scripts/validate_generated_project.py /path/to/generated-project --module-name <module_name>
```

Then decide whether to run:

```bash
make
make create_environment
make requirements
make lint
make test
```

Only run manager-specific installs or cloud sync commands when the necessary external tools, credentials, network, and time are available.

## Integrated difficult case guidance

When a task requires both generation and option reasoning, use this route:

1. Use `../template-options-and-hooks/` to validate the option set and predict generated outputs.
2. Use this sub-skill to choose `ccds` flags, output parent, checkout, and noninteractive context.
3. Use `../generated-project-workflows/` to validate layout and select safe Makefile commands.

Example: generating a project with S3 storage, uv, pyproject dependencies, pytest, Ruff, MkDocs, and code scaffold requires option-validity checks, noninteractive generation, and post-generation validation before any cloud or dependency commands run.
