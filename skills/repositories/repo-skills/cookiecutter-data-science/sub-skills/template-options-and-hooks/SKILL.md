---
name: template-options-and-hooks
description: "Reason about CCDS v2 options, hooks, dependency-file generation,
  prompt patches, and custom configuration overlays."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Template Options And Hooks

Use this sub-skill when a task depends on Cookiecutter Data Science (CCDS) v2
configuration choices, nested prompts, post-generation hook effects, dependency
file contents, or custom configuration overlays.

Route basic `ccds` invocation, output directories, replay, and checkout usage to
`../project-generation-cli/`. Route how to use a generated project's Makefile,
source package, docs, or tests after generation to `../generated-project-workflows/`.

## Reference Map

- Read [references/options-reference.md](references/options-reference.md) when you need the exact CCDS v2 option names, defaults, choices, nested subfields, valid environment/dependency combinations, or `custom_config` semantics.
- Read [references/hook-reference.md](references/hook-reference.md) when you need to predict generated files, package additions, tests/docs pruning, license handling, scaffold removal, prompt monkey patches, or hook ordering.
- Read [references/api-reference.md](references/api-reference.md) when you need helper API signatures, dependency writer behavior, Python version specifier rules, package metadata, or CLI option surface facts.
- Read [references/troubleshooting.md](references/troubleshooting.md) when a configuration fails, generated files do not match expectations, dependency files look wrong, optional CLIs are missing, or a custom overlay changes the project unexpectedly.
- Run [scripts/summarize_ccds_options.py](scripts/summarize_ccds_options.py) when you have CCDS-compatible option/help JSON files and need a deterministic Markdown or JSON summary without importing CCDS, MkDocs, or Cookiecutter.

## Operating Procedure

1. Identify whether the user is asking about configuration semantics or about
   project generation. Stay here only for option/hook reasoning; route command
   mechanics and generated-project usage as described above.
2. Normalize the option set against the exact names and choices in the options
   reference. Preserve nested `dataset_storage` shape and remember that
   `custom_config` is hook-consumed but not a normal prompt field.
3. Check the environment-manager/dependency-file pair before predicting output.
   Invalid pairs often bake until a later hook or Makefile phase fails; reject
   them early using the compatibility table.
4. Predict hook effects in order: dependency package list construction, lint
   setup selection, tests/docs pruning, dependency-file writing, Python version
   update, custom overlay, license cleanup, pyproject quote cleanup, and optional
   scaffold removal.
5. For dependency-file questions, use the helper API reference rather than
   assuming all formats contain the same information. Pixi and Poetry are
   special cases.
6. For failures or surprising output, use the troubleshooting reference to map
   the symptom to the most likely option, hook phase, optional CLI, or overlay
   cause.

## Safety Notes

- Do not instruct future agents to read the CCDS source checkout to answer these
  questions. The bundled references are the runtime source of truth for CCDS
  v2.3.0 behavior covered by this sub-skill.
- Treat `custom_config` as powerful and potentially destructive: validate any
  overlay payload before generation because it can collide with generated paths
  and may be followed by later hook cleanup.
- Do not run mutating Cookiecutter hooks outside a disposable generated project.
  This sub-skill describes hook behavior; it does not bundle the original hook
  as a runtime script.
