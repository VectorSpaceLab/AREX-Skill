---
name: project-generation-cli
description: "Use the Cookiecutter Data Science ccds CLI to create projects, pin
  template versions, run noninteractive generation, and diagnose generation
  failures."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Project Generation CLI

Use this sub-skill when the task is to install or run Cookiecutter Data Science (CCDS), generate a new data-science project, choose `ccds` CLI flags, pin a template version, or debug a generation failure.

## Route elsewhere

- For exact CCDS option semantics, valid option combinations, nested prompt behavior, dependency-file generation, and hook effects, read `../template-options-and-hooks/`.
- For using the generated project after it exists—Makefile rules, data layout, environment managers, scaffold modules, docs, tests, linting, or validation—read `../generated-project-workflows/`.

## Read or run these bundled files

- Read [references/cli-reference.md](references/cli-reference.md) for install commands, `ccds` flags, version pinning, replay/config behavior, and v1 guidance.
- Read [references/workflows.md](references/workflows.md) for interactive, noninteractive, custom-output, and version-pinned generation recipes.
- Read [references/troubleshooting.md](references/troubleshooting.md) when `ccds` is missing, the wrong template/version is used, output directories collide, hooks are disabled, checkout/network fails, or extra context is malformed.
- Run [scripts/bake_ccds_project.py](scripts/bake_ccds_project.py) when you need a safe noninteractive bake through the installed CCDS package. It writes to a temporary parent by default and prints the generated project path.

## Minimal package check

A user can normally install CCDS with one of:

```bash
pipx install cookiecutter-data-science
# or, when pipx is unavailable:
python -m pip install cookiecutter-data-science
```

Then verify the command is available:

```bash
ccds --help
```

CCDS v2 requires Python 3.9+. The package exposes the `ccds` console script and wraps Cookiecutter so that the default template is the public CCDS template and the default checkout is tied to the installed CCDS package version.

## Generation decision flow

1. **Pick an output parent, not a precreated project directory.** Run `ccds` from the parent directory where the new project folder should be created, or pass `-o/--output-dir <parent>`.
2. **Choose the template version.** Use the installed package default for stable released behavior. Use `-c master`, another branch, a tag, or a commit only when the task explicitly needs unreleased or historical template content.
3. **Choose interactive or noninteractive mode.** Interactive `ccds` is safest for humans. Use `--no-input` only when you have a complete context and understand default-first-choice behavior.
4. **Allow hooks unless intentionally inspecting raw templates.** CCDS uses hooks to write dependency files, prune docs/tests/scaffold paths, update Python version metadata, and apply custom configuration. Disabling hooks changes the generated project contract.
5. **Inspect and validate the result.** Route to `../generated-project-workflows/` and use its validation script before running dependency installation, cloud sync, or environment-manager commands.

## Common trigger phrases

Stay in this sub-skill for requests like:

- “Create a new CCDS project.”
- “Use `ccds` with `--no-input`.”
- “Generate from the master branch instead of the released template.”
- “Why did `cookiecutter-data-science` use v2.3.0?”
- “The `ccds` command is missing / my output directory already exists / replay used old answers.”

Route to sibling sub-skills when the user asks what an option means, why a file was generated or removed, or how to run `make requirements` inside an already-generated project.
