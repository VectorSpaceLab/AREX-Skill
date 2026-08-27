---
name: cookiecutter-data-science
description: "Use Cookiecutter Data Science to generate, configure, validate,
  and troubleshoot reproducible data-science project templates and generated
  project workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Cookiecutter Data Science

Use this repo skill for Cookiecutter Data Science (CCDS), the `cookiecutter-data-science` Python package and `ccds` CLI for creating standardized but flexible data-science project skeletons.

## What this skill covers

- Installing and checking the `ccds` CLI.
- Generating a new CCDS v2 project interactively or noninteractively.
- Choosing and validating CCDS options such as environment manager, dependency file, cloud storage, docs, tests, linting, license, and code scaffold.
- Understanding CCDS prompt patches, post-generation hooks, dependency-file writers, and custom config overlays.
- Working inside a generated CCDS project: layout, Makefile commands, data workflow, environment managers, scaffold modules, docs, tests, linting, and validation.
- Troubleshooting install/import, CLI, option, hook, generated layout, Makefile, external manager, and cloud-sync failures.

## Quick package facts

- Distribution: `cookiecutter-data-science`.
- Import module: `ccds`.
- Console script: `ccds`.
- Runtime requirement: Python 3.9+.
- Runtime dependencies: `click`, `cookiecutter`, and `tomlkit`.

Install for CLI use:

```bash
pipx install cookiecutter-data-science
```

Alternative inside a Python environment:

```bash
python -m pip install cookiecutter-data-science
```

Minimal checks:

```bash
python -c "import ccds; print(ccds.__version__)"
ccds --help
```

Run [scripts/check_ccds_environment.py](scripts/check_ccds_environment.py) for a bundled import/CLI/helper smoke check.

## Route by task

| Task intent | Read next |
| --- | --- |
| Install CCDS, run `ccds`, generate a project, set `--output-dir`, pin `--checkout`, use `--no-input`, handle replay/config, or debug project-generation failures. | [sub-skills/project-generation-cli/SKILL.md](sub-skills/project-generation-cli/SKILL.md) |
| Understand option names, defaults, nested choices, valid environment-manager/dependency-file pairs, hook effects, dependency-file generation, prompt monkey patches, or custom config overlays. | [sub-skills/template-options-and-hooks/SKILL.md](sub-skills/template-options-and-hooks/SKILL.md) |
| Work inside a generated project: data layout, Makefile rules, environment setup, dependency installation, scaffold modules, docs, tests, linting, cloud sync, or validation. | [sub-skills/generated-project-workflows/SKILL.md](sub-skills/generated-project-workflows/SKILL.md) |
| Check whether this skill matches the current CCDS repository or package version. | [references/repo-provenance.md](references/repo-provenance.md) |
| Diagnose cross-cutting package, route, version, external tool, validation, data, or secret-handling issues. | [references/troubleshooting.md](references/troubleshooting.md) |
| Check Python, manager, backend, and native verification expectations. | [references/compatibility.md](references/compatibility.md) |

## High-level operating flow

1. **If creating a project**, route to `project-generation-cli`. Decide interactive vs noninteractive generation, output parent, checkout/version, hook policy, and whether a disposable bake is safer.
2. **If choosing options**, route to `template-options-and-hooks`. Validate manager/dependency-file pairings and predict hook outputs before generation.
3. **After a project exists**, route to `generated-project-workflows`. Inspect actual option-dependent files, validate the tree, then decide whether to run environment, dependency, lint, test, data, or cloud commands.
4. **Before exact maintenance claims**, read provenance. CCDS option schemas and hooks are version-sensitive.

## Safety boundaries

- Do not run generated cloud sync rules unless credentials, destination, direction, and transfer size are explicitly intended.
- Do not run generated environment-manager commands in a shared or constrained environment without confirming the required external CLI and local side effects.
- Do not treat starter tests as project failures; generated pytest/unittest starters intentionally fail until replaced.
- Do not apply v2 option and hook behavior to the deprecated v1 template.
- Do not rely on the original source checkout at runtime. This skill bundles distilled references and safe helper scripts for CCDS v2.3.0 behavior.
